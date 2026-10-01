"""Small classroom client and optional integration assertions. No credential handling.

Requires runtime already up. Saves actual Jaeger JSON + a short tree as offline evidence.
"""
import argparse
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from uuid import uuid4


def http(url, body=None):
    request=Request(url, data=json.dumps(body).encode() if body is not None else None,
                    headers={'Content-Type':'application/json'})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def tags(span):
    return {t['key']:t['value'] for t in span['tags']}


def validate(record, failure=False):
    spans=record['spans'];names={s['operationName'] for s in spans}
    expected={'http POST /incidents','messaging publish incident','messaging process incident',
        'workflow incident-investigation','agent supervisor','agent supply','agent production',
        'agent logistics','deterministic finance','agent challenger','agent recommendation',
        'workflow consolidation','workflow human_approval','tool inventory.lookup','tool supplier.lookup','llm completion'}
    assert expected<=names, expected-names
    lookup={s['spanID']:s for s in spans}
    agent=next(s for s in spans if s['operationName']=='agent supply')
    child=[s for s in spans if any(r['spanID']==agent['spanID'] for r in s['references'])]
    assert {'tool inventory.lookup','llm completion'}<={s['operationName'] for s in child}
    if failure:
        calls=[s for s in spans if s['operationName']=='llm completion' and tags(s).get('error')]
        assert len(calls)==2
        events={f['value'] for s in spans for log in s['logs'] for f in log['fields'] if f['key']=='event'}
        assert {'llm.retry','llm.fallback_activated','llm.degraded'}<=events,events
    # Every exported branch has a real parent; join after all specialist spans in its workflow.
    for workflow in [s for s in spans if s['operationName']=='workflow incident-investigation']:
        nodes=[s for s in spans if any(r['spanID']==workflow['spanID'] for r in s['references'])]
        byname={s['operationName']:s for s in nodes}
        if 'workflow consolidation' not in byname:
            continue # failed primary workflow stops before fan-out
        branches=[byname['agent '+n] for n in ('supply','production','logistics')]
        assert byname['workflow consolidation']['startTime'] >= max(s['startTime']+s['duration'] for s in branches)
    assert all(not any(k in tags(s) for k in ('gen_ai.input.messages','gen_ai.output.messages','db.connection_string')) for s in spans)
    return len(spans)


def tree(record):
    spans=record['spans'];ids={s['spanID'] for s in spans}
    def parent(s):
        return next((r['spanID'] for r in s['references'] if r['refType']=='CHILD_OF'), None)
    lines=[]
    def visit(s, depth):
        attributes=tags(s)
        suffix=' ERROR' if attributes.get('error') else ''
        if 'demo_delay_ms' in attributes:suffix+=' demo_delay_ms='+str(attributes['demo_delay_ms'])
        lines.append('  '*depth+s['operationName']+f" [{s['duration']/1000:.2f} ms]"+suffix)
        for child in sorted([v for v in spans if parent(v)==s['spanID']], key=lambda v:v['startTime']):
            visit(child,depth+1)
    for root in [s for s in spans if parent(s) not in ids]:visit(root,0)
    return '\n'.join(lines)


def run(demo='normal',base='http://127.0.0.1:8000',viewer='http://127.0.0.1:16686', output='artifacts/lesson03-complete'):
    started=time.perf_counter()
    body={'incident_id':'HTTP-TRACE-001','version':'trace-'+uuid4().hex[:12]}
    if demo=='failure':body.update(llm_failure='timeout',fallback='deterministic_reference')
    accepted=http(base+'/incidents',body)
    uid,tid=accepted['execution_id'],accepted['trace_id']
    path=base+'/executions/'+uid
    for _ in range(240):
        status=http(path)
        if status['status'] in ('completed','failed'):break
        time.sleep(.25)
    assert status['status']=='completed',status
    result=http(path+'/result')
    assert result['approval_status']=='pending' and result['actions_executed'] is False
    if demo=='failure':assert result['outcome']=='degraded_recommendation'
    for _ in range(60):
        try:
            record=http(viewer+'/api/traces/'+tid)['data'][0]
            count=validate(record,demo=='failure')
            break
        except (AssertionError,IndexError,KeyError):
            time.sleep(.5)
        except Exception as error:
            # Jaeger returns 404 until the first batch arrives.
            if getattr(error,'code',None)!=404:raise
            time.sleep(.5)
    else:raise AssertionError('Trace completo não chegou ao backend em 30s')
    summary={'demo':demo,'execution_id':uid,'trace_id':tid,'worker':status['worker_id'],
             'execution_duration_ms':status['duration_ms'],'spans':count,
             'operational_seconds':round(time.perf_counter()-started,3),
             'outcome':result['outcome'],'jaeger':viewer+'/trace/'+tid}
    directory=Path(output);directory.mkdir(parents=True,exist_ok=True)
    (directory/(demo+'-trace.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2))
    (directory/(demo+'-summary.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    (directory/(demo+'-tree.txt')).write_text(tree(record)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print(tree(record))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('demo',choices=['normal','bottleneck','failure'],nargs='?',default='normal')
    parser.add_argument('--output',default='artifacts/lesson03-complete')
    args=parser.parse_args()
    run(args.demo,output=args.output)
