import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from openrouter_schema import initialize_database


class DatabaseInitializationTests(unittest.TestCase):
    def test_creates_empty_archive_tables(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'fresh.sqlite'
            initialize_database(database)
            with closing(sqlite3.connect(database)) as conn:
                tables = {row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )}
                self.assertTrue({'generations', 'english_translations'} <= tables)
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM generations').fetchone()[0], 0)
                columns = {row[1] for row in conn.execute('PRAGMA table_info(generations)')}
                self.assertTrue({'id', 'model', 'prompt_text', 'completion_text'} <= columns)

    def test_existing_records_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'existing.sqlite'
            initialize_database(database)
            with closing(sqlite3.connect(database)) as conn:
                conn.execute("INSERT INTO generations (id, model) VALUES ('keep-me', 'test-model')")
                conn.commit()
            initialize_database(database)
            with closing(sqlite3.connect(database)) as conn:
                self.assertEqual(
                    conn.execute('SELECT model FROM generations WHERE id=?', ('keep-me',)).fetchone()[0],
                    'test-model'
                )


if __name__ == '__main__':
    unittest.main()
