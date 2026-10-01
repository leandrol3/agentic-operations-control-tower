"""Small paired classroom measurement; configure Compose before each invocation.

Two warmups + five sequential mock requests. Not a scientific benchmark.
"""
import argparse
import json
from pathlib import Path
import statistics
import time
from urllib.request import Request,urlopen
from uuid import uuid4


def request(path,body=None):
    r=Request('http://127.0.0.1:8000'+path,data=json.dumps(body).encode() if body else None,
              headers={'Content-Type':'application/json'})
    with urlopen(r,timeout=15) as response:
        return json.load(response),response.headers


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['enabled','disabled'])
    args=parser.parse_args();samples=[]
    for index in range(7):
        started=time.perf_counter()
        data,headers=request('/incidents',{'incident_id':'OVERHEAD','version':uuid4().hex})
        assert bool(headers.get('X-Request-Trace-ID')) == (args.mode=='enabled'), 'Configure OTEL_ENABLED and recreate runtime first'
        for _ in range(600):
            state,_=request('/executions/'+data['execution_id'])
            if state['status'] in ('completed','failed'):break
            time.sleep(.05)
        assert state['status']=='completed'
        if index>=2:
            samples.append({'execution_id':data['execution_id'],'duration_ms':state['duration_ms'],
                            'observed_ms':(time.perf_counter()-started)*1000})
    result={'otel':args.mode,'warmups':2,'samples':samples,
            'median_execution_ms':statistics.median(s['duration_ms'] for s in samples)}
    path=Path('artifacts/lesson03-complete');path.mkdir(parents=True,exist_ok=True)
    (path/('overhead-'+args.mode+'.json')).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
