"""Small real clients, never a second workflow. Requires the lesson04 Compose stack.

HTTP uses urllib. MCP uses the official SDK and stdio through docker compose exec -T.
Artifacts keep IDs only so normal vs degraded survives a runtime profile change.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen
from uuid import uuid4

BASE=os.environ.get('AULA4_URL','http://127.0.0.1:8000')
STATE=Path('artifacts/lesson04-demo.json')
COMPOSE=['-f','compose.yaml','-f','compose.override.yaml','-f','compose.lesson04.yaml']


def http(path, body=None):
    request=Request(BASE+path, data=json.dumps(body).encode() if body is not None else None,
                    headers={'Content-Type':'application/json'})
    with urlopen(request,timeout=15) as response:
        return json.load(response)


def remember(**values):
    old=json.loads(STATE.read_text()) if STATE.exists() else {}
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(old|values,indent=2)+'\n')


def saved(key):
    if not STATE.exists():
        raise SystemExit('Execute primeiro: uv run --extra lesson04 python scripts/demo_lesson04.py boundary')
    value=json.loads(STATE.read_text()).get(key)
    if not value: raise SystemExit(f'ID {key} ausente; execute a demo correspondente primeiro')
    return value


def status_line(label,data):
    print(f'{label}: {data["execution_id"]} | {data["status"]} | '
          f'worker={data.get("worker_id") or "-"} | duration_ms={data.get("duration_ms")}',flush=True)


def wait(uid):
    previous=None
    for _ in range(120):
        state=http('/executions/'+uid)
        if state['status']!=previous:
            status_line('HTTP status',state);previous=state['status']
        if state['status']=='completed': return state
        if state['status']=='failed': raise RuntimeError('Execution failed; consult durable events')
        time.sleep(.5)
    raise TimeoutError('Execution not completed in 60 seconds; inspect workers')


async def boundary():
    from mcp import StdioServerParameters
    # No provider required. Both paths use the current container configuration.
    supply=http('/agents/supply')
    if supply['execution_type']!='deterministic':
        raise SystemExit('Demo boundary exige runtime mock. Volte ao perfil mock do runbook.')
    version='boundary-'+uuid4().hex[:10]
    body={'incident_id':'L04-HTTP','version':version,'demo_delay_ms':1000}
    accepted=http('/incidents',body);status_line('HTTP accepted',accepted)
    parameters=StdioServerParameters(command='docker',args=['compose',*COMPOSE,'exec','-T',
        '-e','OTEL_SERVICE_NAME=control-tower-mcp','api','python','-m','control_tower.mcp.server'])
    STATE.parent.mkdir(parents=True,exist_ok=True)
    print('MCP protocol/runtime logs: artifacts/lesson04-mcp.log',flush=True)
    with Path('artifacts/lesson04-mcp.log').open('a') as logs:
        await boundary_session(parameters, accepted, body, logs)
    print('Same capability, different boundary.')


async def boundary_session(parameters, accepted, body, logs):
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client
    async with stdio_client(parameters, errlog=logs) as (read,write):
        async with ClientSession(read,write) as client:
            await client.initialize()
            print('MCP tools:', ', '.join(t.name for t in (await client.list_tools()).tools))
            async def call(name,args):
                result=await client.call_tool(name,args)
                if result.isError: raise RuntimeError('MCP tool failed: '+str(result.content))
                return result.structuredContent
            duplicate=await call('submit_incident',{'request':body})
            assert duplicate['execution_id']==accepted['execution_id'] and not duplicate['created']
            print('HTTP → MCP same identity: same execution_id, created=false (durable idempotency)')
            other=await call('submit_incident',{'request':body|{'incident_id':'L04-MCP'}})
            status_line('MCP accepted',other)
            state=await call('get_execution_status',{'execution_id':accepted['execution_id']})
            status_line('MCP reads HTTP execution',state)
            # Poll asynchronously so MCP transport can keep processing.
            await asyncio.to_thread(wait,accepted['execution_id'])
            await asyncio.to_thread(wait,other['execution_id'])
            result=await call('get_execution_result',{'execution_id':other['execution_id']})
            assert result==http(f'/executions/{other["execution_id"]}/result')
            assert result['approval_status']=='pending' and not result['actions_executed']
            print('HTTP = MCP public result | outcome='+result['outcome']+' | approval=pending | actions=false')
            remember(normal=accepted['execution_id'],mcp=other['execution_id'])


def registry(agent):
    if agent:
        print(json.dumps(http('/agents/'+agent),indent=2,ensure_ascii=False))
    else:
        print('AGENT WORKFORCE (current configured runtime; status is registration, not health)')
        for row in http('/agents'):
            print(f'{row["agent_id"]:15} {row["status"]:10} {row["execution_type"]:28} goals={len(row["business_goals"])}')
            print('  role: '+row['role'])
        print('Ownership/goals: registry supply. HTTP/MCP expose the system capability, not each agent.')


def degraded():
    if http('/agents/supply')['execution_type']=='deterministic':
        raise SystemExit('Ative o perfil de falha artificial do runbook antes desta demo.')
    body={'incident_id':'L04-DEGRADED','version':'degraded-'+uuid4().hex[:10],
          'llm_failure':'timeout','fallback':'deterministic_reference'}
    accepted=http('/incidents',body);status_line('Accepted',accepted)
    wait(accepted['execution_id']);remember(degraded=accepted['execution_id'])
    result=http('/executions/'+accepted['execution_id']+'/result')
    assert result['outcome']=='degraded_recommendation'
    print('Artificial timeout before network; deterministic continuity; no real OpenAI request.')


def quality():
    print('QUALITY: completed is runtime status, not a quality score')
    for key in ('normal','degraded'):
        uid=saved(key);row=http(f'/executions/{uid}/quality')
        print(f'{key}: {uid}')
        for field in ('outcome_type','fallback_used','human_review_required','approval_status',
                      'confidence','evidence_complete','policy_compliant'):
            print(f'  {field}: {row[field]}')
    print('confidence is copied from workflow, not calibrated. Unknown evidence/policy stay null.')


def economics(uid):
    uid=uid or saved('normal');row=http(f'/executions/{uid}/economics')
    print('Execution:',uid)
    for key in ('llm_calls','input_tokens','output_tokens','retry_count','task_retry_count','fallback_used',
                'estimated_llm_cost','estimated_execution_cost','cost_currency','cost_source',
                'usage_source','usage_coverage','pricing_version','cost_scope'):
        print(f'{key}: {row[key] if row[key] is not None else "unavailable"}')
    print('outcome:',http(f'/executions/{uid}/result')['outcome'])
    print('Provider usage = measured | Pricing = configured | Cost = estimated')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('demo',choices=['boundary','registry','degraded','quality','economics'])
    parser.add_argument('id',nargs='?')
    args=parser.parse_args()
    if args.demo=='boundary': asyncio.run(boundary())
    elif args.demo=='registry': registry(args.id)
    elif args.demo=='degraded': degraded()
    elif args.demo=='quality': quality()
    else: economics(args.id)


if __name__=='__main__': main()
