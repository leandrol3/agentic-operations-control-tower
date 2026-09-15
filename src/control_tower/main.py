"""CLI offline para explorar o checkpoint start."""
import argparse
import json
import os
from pathlib import Path
from .tools import Tools

def main():
    parser = argparse.ArgumentParser(description="NovaCore — lesson-01-start")
    parser.add_argument("command", choices=["doctor", "incident", "tools", "smoke"])
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Raiz do checkout (padrão: diretório atual)")
    args = parser.parse_args()
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
        parser.error("Este checkpoint suporta LLM_MODE=mock. OpenAI será implementado em lesson-01-complete.")
    try:
        tools = Tools(root)
        incident = tools.load_incident(root / "incidents/incident_001.json")
        if args.command in {"doctor", "smoke"}:
            print(json.dumps({"status": "ok", "mode": mode, "incident_id": incident.incident_id,
                              "affected_orders": len(tools.get_orders(incident.material, incident.plant)),
                              "checkpoint": "lesson-01-start", "orchestration": "TODO"}, indent=2))
        elif args.command == "incident":
            print(incident.model_dump_json(indent=2))
        else:
            print(json.dumps({"stock": tools.get_stock(incident.material, incident.plant).model_dump(),
                              "orders": [r.model_dump(mode="json") for r in tools.get_orders(incident.material, incident.plant)],
                              "alternatives": [r.model_dump(mode="json") for r in tools.get_alternative_suppliers(incident.material, incident.supplier_id)],
                              "routes": [r.model_dump(mode="json") for r in tools.get_routes("Campinas", incident.plant)]}, indent=2, ensure_ascii=False))
    except (ValueError, OSError) as error:
        parser.error(str(error))

if __name__ == "__main__":
    main()
