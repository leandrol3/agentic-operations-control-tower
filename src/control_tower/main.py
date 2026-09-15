"""CLI offline: base e demonstração completa da Aula 1."""
import argparse
import json
import os
import time
from pathlib import Path
from .tools import Tools
from .smoke import check_demo

def main():
    parser = argparse.ArgumentParser(description="NovaCore — candidato lesson-01-complete")
    parser.add_argument("command", choices=["doctor", "incident", "tools", "smoke", "run", "graph"])
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Raiz do checkout (padrão: diretório atual)")
    parser.add_argument("incident_id", nargs="?", help="Obrigatório para run: INCIDENT-001")
    parser.add_argument("--json", action="store_true", help="Estado completo em JSON, sem eventos")
    parser.add_argument("--sequential", action="store_true", help="Controle sequencial para comparar com o paralelismo")
    parser.add_argument("--demo-delay-ms", type=int, default=0, help="Espera artificial por especialista, 0–2000 ms")
    parser.add_argument("--fail-specialist", choices=["supply", "production", "logistics"])
    args = parser.parse_args()
    if args.command == "run" and args.incident_id != "INCIDENT-001":
        parser.error("Use run INCIDENT-001; nenhum outro incidente está cadastrado nesta aula")
    if args.command != "run" and (args.incident_id or args.json or args.fail_specialist or args.demo_delay_ms):
        parser.error("incident_id, --json, --fail-specialist e --demo-delay-ms são opções de run")
    if args.sequential and args.command not in {"run", "graph"}:
        parser.error("--sequential é opção de run ou graph")
    root = args.root.resolve()
    mode = "mock"
    env_file = root / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key.strip() == "LLM_MODE":
                mode = value.strip().strip("\"'")
    mode = os.environ.get("LLM_MODE", mode)
    if mode != "mock":
        parser.error("Este candidato suporta LLM_MODE=mock. OpenAI foi adiado; o grafo não faz chamadas LLM.")
    try:
        tools = Tools(root)
        incident = tools.load_incident(root / "incidents/incident_001.json")
        if args.command == "graph":
            from .graph.workflow import build_graph
            print(build_graph(tools, sequential=args.sequential).get_graph().draw_mermaid())
        elif args.command == "run":
            from .graph.workflow import run_workflow
            from .presentation import render
            started = time.perf_counter()
            if not args.json:
                print(f"Execução {'sequencial' if args.sequential else 'paralela'} | mock | "
                      f"latência artificial por especialista: {args.demo_delay_ms} ms", flush=True)
            def observe(name, phase):
                print(f"  {name}: {phase}", flush=True)
            state = run_workflow(tools, incident, sequential=args.sequential,
                                 demo_delay_ms=args.demo_delay_ms, fail_specialist=args.fail_specialist,
                                 observer=None if args.json else observe)
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
                              "checkpoint": "lesson-01-complete-candidate", "orchestration": "available_via_run", **details}, indent=2))
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
