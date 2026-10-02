"""Read-only cockpit: explicit offline fixtures OR real durable HTTP projections."""
import argparse
import json
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen
from control_tower.control_plane.configuration import load_config
from control_tower.control_plane.economics import PricingConfig
from control_tower.control_plane.demo_fixture import fixture_samples
from control_tower.control_plane.service import ControlPlane


def number(value):
    if value is None:
        return 'unknown'
    return format(Decimal(str(value)), '.6f').rstrip('0').rstrip('.') or '0'


def show(views, section):
    print('COLLECT -> INTERPRET -> RECOMMEND (read-only; no ACT)')
    print('Agent          Lifecycle Goals       Quality* Cost(USD)** SLO        Action')
    details = section in ('lifecycle', 'recommendation', 'pipeline')
    for v in views:
        g=v['goals'][0];r=v['recommendation']
        statuses={s['status'] for s in v['slos']}
        status=next((s for s in ('violation','warn','unknown','pass') if s in statuses),'unknown')
        cost=v['economics']['observed'];quality=v['quality']['observed']
        print(f'{v["registry"]["agent_id"]:14} {v["registry"]["lifecycle_state"]:9} {g["status"]:11} '
              f'{number(quality):8} {number(cost):11} {status:10} {r["action"] if r and (details or section == "cockpit") else "-" if r else "no_action"}')
        if section != 'cockpit':
            if section == 'pipeline':
                print(f'  COLLECT source={v["evidence_source"]} samples={v["sample_count"]} mode={v["mode"]} model={v["cohort_model"]}')
                print(f'  Pricing={v["pricing_version"]} reference={v["pricing_reference_date"]}')
                print('  INTERPRET goal gap, SLO, trends and triggers:')
            print(f'  GOAL target={g["target"]} actual={number(g["actual"])} gap={number(g["gap"])}; cost_trend={v["cost_trend"]}')
            for s in (v['slos'] if section != 'goals' else []):
                print(f'  SLO {s["slo_id"]}: {number(s["observed"])} {s["operator"]} {s["target"]} -> {s["status"]}')
            if details:
                print('  Triggers:', ', '.join(t['trigger_type'] for t in v['triggers']) or 'none')
            if r and details:
                print(f'  RECOMMEND {r["action"].upper()} | priority={r["priority"]} | approval={r["requires_human_approval"]}')
                print('  Reason:',r['reason'])
                print('  Lifecycle:',r['current_lifecycle_state'],'-> suggested',r['suggested_lifecycle_state'], '(not applied)')
                for e in r['evidence']:
                    print(f'  Evidence {e["metric"]}={number(e["observed"])} target={e["target"]} {e["unit"]} scope={e["scope"]} n={len(e["execution_ids"])}')
            elif details:
                print('  Decision:',v['decision_note'])
            if v['business_value'] and section in ('recommendation', 'pipeline'):
                value=v['business_value'][0]
                print(f'  Business context: {value["value_metric"]}={value["value_amount"]} {value["currency_or_unit"]}; realized value UNKNOWN')
                proxy=v['business_value'][1]
                print(f'  Value proxy: {proxy["value_metric"]}={number(proxy["value_amount"])} {proxy["currency_or_unit"]}; no savings claim')
    print('* Workflow non-normal outcome %, not agent correctness. ** Mean recorded role usage estimate; unknown is not zero.')
    print('Recommendation is not authorization. Lifecycle unchanged. No savings/ROI inferred.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    source=p.add_mutually_exclusive_group(required=True)
    source.add_argument('--fixture',choices=['stable','cost','optimize','intervene','review','pause'])
    source.add_argument('--live',action='store_true')
    p.add_argument('--agent',choices=['supervisor','supply','production','logistics','finance','challenger','recommendation'])
    p.add_argument('--mode',choices=['mock','openai'],default='mock')
    p.add_argument('--section',choices=['goals','slo','lifecycle','recommendation','pipeline','cockpit'],default='cockpit')
    p.add_argument('--url',default='http://localhost:8000')
    args=p.parse_args()
    if args.fixture:
        print('SOURCE: DIDACTIC FIXTURE. Synthetic events/tokens; no provider calls, no database writes.')
        pricing=PricingConfig.model_validate_json(Path('config/lesson04-pricing.json').read_text())
        views=[v.model_dump(mode='json') for v in ControlPlane(None,config=load_config(),pricing=pricing).evaluate(
            samples=fixture_samples(args.fixture),source='didactic_fixture',mode='openai',agent_id=args.agent)]
    else:
        print('SOURCE: DURABLE HISTORY, cohort='+args.mode)
        path='/control-plane/agents'+('/'+args.agent if args.agent else '')+'?mode='+args.mode
        with urlopen(args.url.rstrip('/')+path,timeout=20) as response:
            result=json.load(response)
        views=[result] if args.agent else result
    show(views,args.section)


if __name__=='__main__':
    main()
