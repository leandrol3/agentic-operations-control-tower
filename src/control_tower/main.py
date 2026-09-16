"""CLI da Aula 1: mock offline e interpretação OpenAI opcional."""
import argparse
import json
import time
import sys
from pathlib import Path
from .tools import Tools
from .smoke import check_demo
from .settings import Settings

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('db-init', 'enqueue', 'executions', 'execution', 'events', 'result'):
        from .distributed.remote_cli import main as distributed_main
        return distributed_main(sys.argv[1:])
    if len(sys.argv) > 1 and sys.argv[1] in ('generate-incidents', 'batch', 'idempotency-demo'):
        from .distributed.cli import main as lesson02_main
        return lesson02_main(sys.argv[1:])
    parser = argparse.ArgumentParser(description="NovaCore — lesson-01-complete")
    parser.add_argument("command", choices=["doctor", "incident", "tools", "smoke", "run", "graph", "show"])
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Raiz do checkout (padrão: diretório atual)")
    parser.add_argument("incident_id", nargs="?", help="Obrigatório para run: INCIDENT-001")
    parser.add_argument("view", nargs="?", choices=["summary", "state", "specialists", "coordination", "scenarios", "challenger", "recommendation", "llm-decisions"])
    parser.add_argument("--json", action="store_true", help="Estado completo em JSON, sem eventos")
    parser.add_argument("--sequential", action="store_true", help="Controle sequencial para comparar com o paralelismo")
    parser.add_argument("--demo-delay-ms", type=int, default=0, help="Espera artificial por especialista, 0–2000 ms")
    parser.add_argument("--fail-specialist", choices=["supply", "production", "logistics"])
    args = parser.parse_args()
    if args.command in {"run", "show"} and args.incident_id != "INCIDENT-001":
        parser.error("Use run/show INCIDENT-001; nenhum outro incidente está cadastrado nesta aula")
    if args.command == "show" and not args.view:
        parser.error("Use show INCIDENT-001 seguido de uma view")
    if args.command != "show" and args.view:
        parser.error("View é argumento exclusivo de show")
    if args.command not in {"run", "show"} and args.incident_id:
        parser.error("incident_id é argumento de run/show")
    if args.json and args.command != "run":
        parser.error("--json é opção de run; show é uma apresentação compacta")
    if args.command != "run" and (args.fail_specialist or args.demo_delay_ms or args.sequential):
        if not (args.command == "show" and args.view == "coordination") and not (
            args.command == "graph" and not args.fail_specialist and not args.demo_delay_ms):
            parser.error("Opções de execução são de run, show coordination ou graph --sequential")
    root = args.root.resolve()
    try:
        settings = Settings.load(root)
        mode = settings.mode
        llm = settings.interpreter() if args.command in {'run', 'show'} else None
        tools = Tools(root)
        incident = tools.load_incident(root / "incidents/incident_001.json")
        if args.command == "show":
            from .views import show
            text, blocked = show(tools, incident, args.view, sequential=args.sequential,
                                 demo_delay_ms=args.demo_delay_ms, fail_specialist=args.fail_specialist, llm=llm)
            print(text)
            if blocked:
                raise SystemExit(1)
        elif args.command == "graph":
            from .graph.workflow import build_graph
            print(build_graph(tools, sequential=args.sequential).get_graph().draw_mermaid())
        elif args.command == "run":
            from .graph.workflow import run_workflow
            from .presentation import render
            started = time.perf_counter()
            if not args.json:
                print(f"Execução {'sequencial' if args.sequential else 'paralela'} | {mode} | "
                      f"latência artificial por especialista: {args.demo_delay_ms} ms", flush=True)
            def observe(name, phase):
                print(f"  {name}: {phase}", flush=True)
            state = run_workflow(tools, incident, sequential=args.sequential,
                                 demo_delay_ms=args.demo_delay_ms, fail_specialist=args.fail_specialist,
                                 observer=None if args.json else observe, llm=llm)
            if args.json:
                print(state.model_dump_json(indent=2))
            else:
                print(render(state))
                print(f"Tempo observado do workflow: {time.perf_counter() - started:.3f}s (não é benchmark).")
            if state.status == "blocked":
                raise SystemExit(1)
        elif args.command in {"doctor", "smoke"}:
            details = check_demo(tools, incident) if args.command == "smoke" else {}
            print(json.dumps({"status": "ok", "mode": mode, "incident_id": incident.incident_id,
                              "related_orders": len(tools.get_orders(incident.material, incident.plant)),
                              "impact_status": "not_assessed",
                              "checkpoint": "lesson-01-complete", "orchestration": "available_via_run", **details}, indent=2))
        elif args.command == "incident":
            print(incident.model_dump_json(indent=2))
        else:
            print(json.dumps({"stock": tools.get_stock(incident.material, incident.plant).model_dump(),
                              "related_orders": [r.model_dump(mode="json") for r in tools.get_orders(incident.material, incident.plant)],
                              "impact_status": "not_assessed",
                              "alternatives": [r.model_dump(mode="json") for r in tools.get_alternative_suppliers(incident.material, incident.supplier_id)],
                              "routes": [r.model_dump(mode="json") for r in tools.get_routes("Campinas", incident.plant)]}, indent=2, ensure_ascii=False))
    except (ValueError, OSError) as error:
        parser.error(str(error))

if __name__ == "__main__":
    main()
