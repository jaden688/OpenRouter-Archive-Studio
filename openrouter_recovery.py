import json,sqlite3,urllib.request,urllib.parse,urllib.error,datetime,time,os
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT='https://openrouter.ai/api/v1'
def get_json(url,key,payload=None):
    hdr={'Authorization':'Bearer '+key,'Accept':'application/json'}
    if payload is not None:
        hdr['Content-Type']='application/json'
    req=urllib.request.Request(ROOT+url,data=(json.dumps(payload).encode() if payload is not None else None),headers=hdr)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req,timeout=45) as resp:return json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code==404:return {'_missing':404}
            if exc.code not in (429,500,502,503,504) or attempt==4:raise
        except (TimeoutError,urllib.error.URLError):
            if attempt==4:raise
        time.sleep(min(16,2**attempt))
def recover(database,start_date,end_date,key,notify=lambda s:None):
    if not key:raise ValueError('A management key is required.')
    start=datetime.date.fromisoformat(start_date);end=datetime.date.fromisoformat(end_date)
    if end<start:raise ValueError('End date precedes start date.')
    meta=get_json('/analytics/meta',key).get('data',{})
    dims=[x.get('name') if isinstance(x,dict) else x for x in meta.get('dimensions',[])]
    if 'generation_id' not in dims:raise RuntimeError('Your analytics API does not expose generation_id.')
    ids=set();day=start
    while day<=end:
        nxt=day+datetime.timedelta(days=1)
        payload={'dimensions':['generation_id','model'],'metrics':['request_count','total_usage'],'time_range':{'start':day.isoformat()+'T00:00:00Z','end':nxt.isoformat()+'T00:00:00Z'},'limit':5000}
        response=get_json('/analytics/query',key,payload)
        content=response.get('data',{})
        data=content.get('data',[]) if isinstance(content,dict) else []
        for x in data:
            if x.get('generation_id'):ids.add(x['generation_id'])
        metadata=content.get('metadata',{}) if isinstance(content,dict) else {}
        notify(f'{day.isoformat()}: discovered {len(data)} generations.')
        if metadata.get('truncated') or len(data)>=5000:
            notify(f'WARNING: {day} hit the 5,000-record query limit; that day may be incomplete.')
        day=nxt
    conn=sqlite3.connect(database)
    conn.execute('CREATE TABLE IF NOT EXISTS recovered_raw (generation_id TEXT PRIMARY KEY, metadata_json TEXT, content_json TEXT, status TEXT, imported_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    existing={x[0] for x in conn.execute("SELECT generation_id FROM recovered_raw WHERE status='ok'")}
    pending=sorted(ids-existing)
    notify(f'Found {len(ids)} unique IDs, {len(pending)} require retrieval.')
    def pull(gid):
        q=urllib.parse.urlencode({'id':gid})
        metadata=get_json('/generation?'+q,key)
        content=get_json('/generation/content?'+q,key)
        return gid,metadata,content
    successes=0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(pull,gid) for gid in pending]
        for n,task in enumerate(as_completed(futures),1):
            try:
                gid,m,c=task.result()
                status='missing_content' if c.get('_missing') else 'ok'
                conn.execute('INSERT OR REPLACE INTO recovered_raw(generation_id,metadata_json,content_json,status) VALUES (?,?,?,?)',(gid,json.dumps(m,ensure_ascii=False),json.dumps(c,ensure_ascii=False),status))
                if status=='ok':successes+=1
                rawm=m.get('data',{});rawc=c.get('data',{})
                if not isinstance(rawm,dict):rawm={}
                if not isinstance(rawc,dict):rawc={}
                input_data=rawc.get('input') or {}
                messages=input_data.get('messages') or [] if isinstance(input_data,dict) else []
                output=rawc.get('output') or {}
                prompt_text=(chr(10)*2).join('['+str(msg.get('role','?'))+']'+chr(10)+str(msg.get('content','')) for msg in messages if isinstance(msg,dict))
                if not prompt_text and isinstance(input_data,dict) and isinstance(input_data.get('prompt'),str):
                    prompt_text=input_data.get('prompt')
                cols={row[1] for row in conn.execute('PRAGMA table_info(generations)')}
                if 'id' in cols:
                    stamp=None
                    try:
                        stamp=datetime.datetime.fromisoformat(str(rawm.get('created_at','')).replace('Z','+00:00'))
                        if stamp.tzinfo is None: stamp=stamp.replace(tzinfo=datetime.timezone.utc)
                    except Exception: pass
                    local_stamp=stamp.astimezone(ZoneInfo('America/Edmonton')) if stamp else None
                    values={
                        'id':gid,'created_at_utc':rawm.get('created_at'),
                        'created_at_local':local_stamp.isoformat() if local_stamp else None,
                        'date_utc':stamp.date().isoformat() if stamp else None,
                        'date_local':local_stamp.date().isoformat() if local_stamp else None,
                        'model':rawm.get('model'),
                        'provider_name':rawm.get('provider_name'),'api_type':rawm.get('api_type'),
                        'tokens_prompt':rawm.get('tokens_prompt'),'tokens_completion':rawm.get('tokens_completion'),
                        'native_tokens_prompt':rawm.get('native_tokens_prompt'),
                        'native_tokens_completion':rawm.get('native_tokens_completion'),
                        'native_tokens_reasoning':rawm.get('native_tokens_reasoning'),
                        'native_tokens_cached':rawm.get('native_tokens_cached'),
                        'total_cost':rawm.get('total_cost'),'usage':rawm.get('usage'),
                        'finish_reason':rawm.get('finish_reason'),'native_finish_reason':rawm.get('native_finish_reason'),
                        'generation_time_ms':rawm.get('generation_time'),'latency_ms':rawm.get('latency'),
                        'streamed':rawm.get('streamed'),'cancelled':rawm.get('cancelled'),'is_byok':rawm.get('is_byok'),
                        'session_id':rawm.get('session_id'),'request_id':rawm.get('request_id'),
                        'upstream_id':rawm.get('upstream_id'),
                        'metadata_status':200 if rawm else 404,'content_status':200 if status=='ok' else 404,
                        'prompt_messages_json':json.dumps(messages,ensure_ascii=False),'prompt_text':prompt_text,
                        'completion_text':output.get('completion'),'reasoning_text':output.get('reasoning'),
                        'raw_metadata_json':json.dumps(rawm,ensure_ascii=False),'raw_content_json':json.dumps(rawc,ensure_ascii=False)
                    }
                    chosen={k:v for k,v in values.items() if k in cols}
                    names=list(chosen); marks=','.join('?' for _ in names)
                    conn.execute('INSERT INTO generations ('+','.join(names)+') VALUES ('+marks+') ON CONFLICT(id) DO UPDATE SET '+','.join(f'{k}=excluded.{k}' for k in names if k!='id'),list(chosen.values()))
                conn.commit()
            except Exception as e:
                notify('Retrieval issue: '+str(e)[:180])
            if n%20==0 or n==len(pending):notify(f'Retrieved {n}/{len(pending)}; {successes} content records.')
    conn.close()
    return f'Done. {len(ids)} IDs enumerated; {successes} new content records recovered.'
