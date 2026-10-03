"""Small read-only rehearsal for the cockpit; no automatic human approval."""

import argparse
import json
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--source", choices=["didactic", "durable"], default="didactic")
    args = parser.parse_args()
    with urlopen(
        args.url.rstrip("/") + "/cockpit/overview?source=" + args.source, timeout=15
    ) as response:
        data = json.load(response)
    supply = next(a for a in data["agents"] if a["registry"]["agent_id"] == "supply")
    goal = supply["goals"][0]
    print("L3 CONTROL PLANE — ENSAIO DO COCKPIT")
    print(
        "Fonte:",
        "DIDÁTICA / SINTÉTICA" if args.source == "didactic" else "HISTÓRICO PERSISTIDO",
    )
    print(
        "Agentes:",
        data["overview"]["total_agents"],
        "| com sinais de atenção:",
        data["overview"]["attention_agents"],
    )
    print(
        f"Supply: alvo={goal['target']}% | atual={goal['actual']}% | gap={goal['gap']} p.p."
    )
    print(
        "Proposta:",
        supply["recommendation"]["reason_pt"]
        if supply["recommendation"]
        else "Sem evidência suficiente",
    )
    print("Execuções disponíveis:", len(data["operations"]))
    print(
        "Conhecimentos aprovados:",
        data["knowledge"]["counts"]["approved"],
        "| pendentes:",
        data["knowledge"]["counts"]["pending_review"],
    )
    print("Planos propostos persistidos:", len(data["plans"]))
    print(
        "Valor realizado: desconhecido. Nenhuma ação operacional autorizada ou executada."
    )
    if args.source == "didactic":
        assert float(goal["target"]) == 90 and float(goal["actual"]) == 74
        assert supply["recommendation"]["action"] == "intervene"
        assert any(a["goals"][0]["status"] == "on_target" for a in data["agents"])
        assert data["overview"]["slo_violations"] > 0
        print(
            "Cenário didático conferido: 37/50 observações de cobertura; 6 execuções ilustrativas independentes."
        )


if __name__ == "__main__":
    main()
