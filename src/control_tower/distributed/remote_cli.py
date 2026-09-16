"""Views curtas do banco. --json permite inspecionar os contratos completos."""
import argparse
import json
from uuid import UUID
from .durable import TaskOptions
from .incidents import generate_incidents
from .store import Store


def main(argv):
    parser = argparse.ArgumentParser(description='Aula 2: Celery + Redis + PostgreSQL | mock/openai')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('db-init')
    enqueue_parser = sub.add_parser('enqueue')
    enqueue_parser.add_argument('--count', type=int, default=20)
    enqueue_parser.add_argument('--seed', type=int, default=42)
    enqueue_parser.add_argument('--operation', default='analyze-reference')
    enqueue_parser.add_argument('--version', default='v1')
    enqueue_parser.add_argument('--demo-delay-ms', type=int, default=0)
    enqueue_parser.add_argument('--fail-specialist', choices=['supply', 'production', 'logistics'])
    enqueue_parser.add_argument('--fail-always', action='store_true')
    enqueue_parser.add_argument('--llm-failure', choices=['none', 'timeout'], default='none')
    enqueue_parser.add_argument('--fallback', choices=['human', 'deterministic_reference'], default='human')
    for name in ('executions', 'execution', 'events', 'result'):
        p = sub.add_parser(name)
        if name != 'executions':
            p.add_argument('execution_id', type=UUID)
        p.add_argument('--json', action='store_true')
        if name == 'events':
            p.add_argument('--llm', action='store_true', help='Somente eventos de provider/continuidade')
            p.add_argument('--lifecycle', action='store_true', help='Somente lifecycle/retry/erros')
        if name in ('events', 'executions'):
            p.add_argument('--limit', type=int, default=12 if name == 'events' else 8)
    args = parser.parse_args(argv)
    store = Store()
    try:
        if args.command == 'db-init':
            store.initialize()
            print('PostgreSQL: tabelas de execução/eventos prontas. Nenhum dado removido.')
        elif args.command == 'enqueue':
            from .producer import enqueue
            from ..settings import Settings
            from .config import project_root
            settings = Settings.load(project_root())
            options = TaskOptions(demo_delay_ms=args.demo_delay_ms, fail_specialist=args.fail_specialist, fail_always=args.fail_always,
                                  llm_mode=settings.mode, llm_model=settings.model, llm_failure=args.llm_failure, fallback=args.fallback)
            envelopes = generate_incidents(args.count, args.seed)
            created, ids = 0, []
            for envelope in envelopes:
                execution, new = enqueue(envelope, options, args.operation, args.version, store)
                created += new
                ids.append(str(execution.execution_id))
            print(f'Publicadas: {len(ids)} | novas executions: {created} | existentes: {len(ids)-created}')
            print(f'{options.llm_mode} | referência INCIDENT-001 | aprovação humana obrigatória')
            for identity in ids[:8]:
                print(identity)
            if len(ids) > 8:
                print(f'... mais {len(ids)-8}; consulte executions')
        elif args.command == 'executions':
            if not 1 <= args.limit <= 100:
                raise ValueError('limit deve estar entre 1 e 100')
            counts, recent = store.list(args.limit)
            if args.json:
                print(json.dumps({'counts': counts, 'recent': [e.model_dump(mode='json') for e in recent]}, indent=2))
            else:
                print(' | '.join(f'{s}: {counts.get(s,0)}' for s in ('queued','running','completed','failed')))
                print('execution_id                         status     attempt worker            duration')
                for e in recent:
                    worker = e.worker_id.split('@')[0] + ':' + e.worker_id.rsplit(':', 1)[-1] if e.worker_id else '—'
                    print(f'{e.execution_id} {e.status:10} {e.attempt:7} {worker:17} {e.duration_ms/1000:.2f}s' if e.duration_ms is not None else f'{e.execution_id} {e.status:10} {e.attempt:7} {worker:17} —')
        elif args.command == 'events':
            if not 1 <= args.limit <= 100:
                raise ValueError('limit deve estar entre 1 e 100')
            events = store.events(args.execution_id)
            if args.llm:
                events = [e for e in events if e.event_type.startswith('llm.')]
            if args.lifecycle:
                events = [e for e in events if e.event_type.startswith('execution.') or e.event_type.endswith('.failed')]
            if args.json:
                print(json.dumps([e.model_dump(mode='json') for e in events], indent=2))
            else:
                print(f'{args.execution_id} | eventos: {len(events)} | últimos {args.limit}')
                for e in events[-args.limit:]:
                    print(f'{e.sequence:3} {e.timestamp:%H:%M:%S} attempt={e.attempt} {e.event_type}')
        else:
            execution = store.get(args.execution_id)
            if args.command == 'result':
                result = execution.result
                if args.json:
                    print(result.model_dump_json(indent=2) if result else 'null')
                elif result:
                    print('Execution completed | human_review_required | actions_executed=false'
                          if result.outcome == 'human_review_required' else
                          'Workflow completed | approval pending | actions_executed=false')
                    print(f'Caso de referência: {result.reference_case_id} | modo: {result.mode}')
                    print(f'outcome: {result.outcome}' + (f' | reason: {result.reason}' if result.reason else ''))
                    r = result.recommendation
                    if r is None:
                        print('Revisão humana necessária; nenhuma recomendação automática.')
                        return
                    from textwrap import fill
                    print(fill(f'Ação: {r.recommended_action}', width=100))
                    print(f'Custo: R$ {r.estimated_cost_brl} | multa evitada: R$ {r.avoided_penalty_brl}')
                    print(f'Atraso: {r.customer_delay_days} dias | confiança: {r.confidence}')
                    print(f'Riscos: {len(r.risks)} | --json para contrato completo')
                else:
                    print(f'Sem resultado final; status={execution.status}')
            elif args.json:
                print(execution.model_dump_json(indent=2))
            else:
                for field in ('execution_id', 'incident_id', 'status', 'attempt', 'worker_id', 'current_step', 'started_at', 'completed_at', 'error'):
                    print(f'{field}: {getattr(execution, field)}')
                print(f'mode: {execution.llm_mode} | duration: {execution.duration_ms/1000:.2f}s' if execution.duration_ms is not None else f'mode: {execution.llm_mode} | duration: —')
                print(f'result: {execution.result.outcome if execution.result else "—"}; actions_executed=false')
    except Exception as error:
        # Nunca imprime DSN/chave; erros operacionais são identificados sem credenciais.
        if isinstance(error, ValueError):
            parser.error(str(error))
        parser.exit(1, f'{type(error).__name__}: operação não concluída. Verifique Compose/db-init/broker; '
                    'se publicação falhou, repita enqueue com os mesmos parâmetros.\n')
