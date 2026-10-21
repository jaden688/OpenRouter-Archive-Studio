import pathlib,sqlite3
def import_database(destination,source,notify=lambda message:None):
    destination=pathlib.Path(destination).resolve()
    source=pathlib.Path(source).resolve()
    if source==destination:raise ValueError("That is already the working database.")
    if not source.is_file():raise ValueError("Source file does not exist.")
    if source.stat().st_size<100:raise ValueError("This file does not appear to be a SQLite database.")
    with source.open('rb') as fh:
        if fh.read(16)!=bytes.fromhex('53514c69746520666f726d6174203300'):raise ValueError("Not a SQLite database. Choose a .sqlite, .sqlite3 or .db file.")
    source_db=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
    target_db=sqlite3.connect(destination)
    try:
        source_db.execute('PRAGMA query_only=ON')
        source_cols=[c[1] for c in source_db.execute('PRAGMA table_info(generations)')]
        dest_cols=[c[1] for c in target_db.execute('PRAGMA table_info(generations)')]
        required=('id','prompt_messages_json','completion_text','raw_metadata_json','raw_content_json')
        if not set(required).intersection(source_cols) or 'id' not in source_cols:
            raise ValueError('No compatible generations table found. This importer expects an OpenRouter Archive Studio SQLite database.')
        cols=[name for name in dest_cols if name in source_cols]
        if not cols:raise ValueError('No matching generation fields to import.')
        quoted=','.join('"'+c+'"' for c in cols)
        placeholders=','.join('?' for _ in cols)
        inserted=0;skipped=0
        count=source_db.execute('SELECT COUNT(*) FROM generations').fetchone()[0]
        notify(f'Found {count:,} source generations; importing all {len(cols)} matching data fields.')
        query=f'SELECT {quoted} FROM generations'
        insert=f'INSERT OR IGNORE INTO generations ({quoted}) VALUES ({placeholders})'
        target_db.execute('BEGIN')
        for row in source_db.execute(query):
            cursor=target_db.execute(insert,row)
            inserted+=cursor.rowcount
            skipped+=1-cursor.rowcount
        trans=0
        existing=source_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='english_translations'").fetchone()
        if existing:
            tr_cols=[c[1] for c in source_db.execute('PRAGMA table_info(english_translations)')]
            if {'generation_id','field_name','translated_text'}.issubset(tr_cols):
                for row in source_db.execute('SELECT generation_id,field_name,translated_text FROM english_translations'):
                    trans+=target_db.execute('INSERT OR IGNORE INTO english_translations (generation_id,field_name,translated_text) VALUES (?,?,?)',row).rowcount
        # Preserve additional tables from expanded exports under namespaced names.
        # Never replace tables previously imported or overwrite a user's working tables.
        extra_tables=[]
        for (table_name,) in source_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
            if table_name in ('generations','english_translations'):continue
            import re
            if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',table_name):continue
            target_name='source_'+table_name
            if target_db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(target_name,)).fetchone():
                continue
            info=source_db.execute('PRAGMA table_info("'+table_name+'")').fetchall()
            if not info:continue
            cols_def=','.join('"'+col[1]+'" '+(col[2] or 'BLOB') for col in info)
            target_db.execute('CREATE TABLE "'+target_name+'" ('+cols_def+')')
            columns=','.join('"'+col[1]+'"' for col in info)
            placeholders=','.join('?' for _ in info)
            batch=[]
            for extra_row in source_db.execute('SELECT '+columns+' FROM "'+table_name+'"'):
                batch.append(tuple(extra_row))
                if len(batch)>=300:
                    target_db.executemany('INSERT INTO "'+target_name+'" VALUES ('+placeholders+')',batch)
                    batch.clear()
            if batch:target_db.executemany('INSERT INTO "'+target_name+'" VALUES ('+placeholders+')',batch)
            extra_tables.append(target_name)
        target_db.commit()
        return (f'Imported {inserted:,} generations, skipped {skipped:,} existing IDs, '
                f'added {trans:,} saved translations, and preserved {len(extra_tables)} additional tables. '
                f'Source left unchanged.')
    except:
        target_db.rollback()
        raise
    finally:
        source_db.close();target_db.close()
