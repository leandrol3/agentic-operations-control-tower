"""Comandos aditivos da Aula 2; o parser/fluxo da Aula 1 permanece separado."""
import argparse
from pathlib import Path

from .batch import BatchOptions, render_batch, run_batch
from .idempotency import idempotency_key
from .incidents import generate_incidents, summarize

COMMANDS = ('generate-incidents', 'batch', 'idempotency-demo')


def main(argv):
    parser = argparse.ArgumentParser(description='lesson-02-start: carga sintética e baseline local mock')
    sub = parser.add_subparsers(dest='command', required=True)
    generator = sub.add_parser('generate-incidents', help='Gerar eventos sintéticos reproduzíveis')
    generator.add_argument('--count', type=int, default=500)
    generator.add_argument('--seed', type=int, default=42)
    generator.add_argument('--output', type=Path, help='Salvar JSONL (arquivo novo)')
    batch = sub.add_parser('batch', help='Replay local mock, sem broker/state store')
    batch.add_argument('--incidents', type=int, default=10)
    batch.add_argument('--workers', type=int, default=1)
    batch.add_argument('--provider-limit', type=int)
    batch.add_argument('--demo-delay-ms', type=int, default=0)
    batch.add_argument('--seed', type=int, default=42)
    batch.add_argument('--root', type=Path, default=Path.cwd())
    batch.add_argument('--output', type=Path, help='Snapshot JSON de estado/eventos ao terminar (arquivo novo)')
    idem = sub.add_parser('idempotency-demo', help='Mesma identidade lógica em entregas repetidas')
    idem.add_argument('--incident-id', default='NC-S42-0001')
    idem.add_argument('--operation', default='analyze-reference')
    idem.add_argument('--version', default='v1')
    args = parser.parse_args(argv)
    try:
        if args.command == 'idempotency-demo':
            first = idempotency_key(args.incident_id, args.operation, args.version)
            duplicate = idempotency_key(args.incident_id, args.operation, args.version)
            print(f'Idempotency contract | {args.incident_id} | {args.operation} | {args.version}')
            print(f'idempotency_key: {first}')
            print(f'Duas entregas, mesma chave: {first == duplicate}')
            print('Helper não elimina duplicatas. Retry/reivindicação atômica ficam para o complete.')
            return
        if args.output and args.output.exists():
            raise ValueError('Arquivo de saída já existe; escolha outro caminho')
        if args.command == 'generate-incidents':
            incidents = generate_incidents(args.count, args.seed)
            output = '\n'.join(i.model_dump_json() for i in incidents) + '\n'
            summary = summarize(incidents, args.seed)
            failed = False
        else:
            options = BatchOptions(workers=args.workers, provider_limit=args.provider_limit,
                                   demo_delay_ms=args.demo_delay_ms)
            incidents = generate_incidents(args.incidents, args.seed)
            report = run_batch(args.root.resolve(), incidents, options)
            output, summary, failed = report.model_dump_json(indent=2) + '\n', render_batch(report), report.failed
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('x') as target:
                target.write(output)
        print(summary)
        if args.output:
            print('Exportação local gravada; não é um state store nem permite retomada.')
        if failed:
            raise SystemExit(1)
    except (ValueError, OSError) as error:
        parser.error(str(error))
