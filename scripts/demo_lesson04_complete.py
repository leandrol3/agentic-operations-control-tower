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
from control_tower.cockpit.localization import pt
from control_tower.cockpit.presentation import NAMES, REASONS


def number(value):
    if value is None:
        return "Desconhecido"
    return format(Decimal(str(value)), ".6f").rstrip("0").rstrip(".") or "0"


def show(views, section):
    print("COLETAR → INTERPRETAR → RECOMENDAR (somente leitura; sem ACT)")
    print(
        "Agente                  Lifecycle    Meta             Qualidade* Custo(USD)** SLO                 Ação"
    )
    details = section in ("lifecycle", "recommendation", "pipeline")
    for v in views:
        g = v["goals"][0]
        r = v["recommendation"]
        statuses = {s["status"] for s in v["slos"]}
        status = next(
            (s for s in ("violation", "warn", "unknown", "pass") if s in statuses),
            "unknown",
        )
        print(
            f"{NAMES[v['registry']['agent_id']]:23} {pt(v['registry']['lifecycle_state']):12} {pt(g['status']):16} "
            f"{number(v['quality']['observed']):10} {number(v['economics']['observed']):12} {pt(status):19} {pt(r['action']) if r else 'Sem proposta'}"
        )
        if section != "cockpit":
            print(
                f"  COLETAR fonte={pt(v['evidence_source'])} amostras={v['sample_count']} modo={v['mode']} modelo={pt(v['cohort_model'])}"
            )
            print(
                f"  Pricing={v['pricing_version']} referência={pt(v['pricing_reference_date'])}"
            )
            print(
                f"  META alvo={g['target']} atual={number(g['actual'])} gap={number(g['gap'])}; tendência de custo={pt(v['cost_trend'])}"
            )
            for slo in v["slos"] if section != "goals" else []:
                print(
                    f"  SLO {slo['slo_id']}: {number(slo['observed'])} {slo['operator']} {slo['target']} → {pt(slo['status'])}"
                )
            if details:
                print(
                    "  Sinais:",
                    ", ".join(pt(t["trigger_type"]) for t in v["triggers"]) or "Nenhum",
                )
            if r and details:
                print(
                    f"  RECOMENDAÇÃO {pt(r['action'])} | prioridade={pt(r['priority'])} | aprovação humana={pt(r['requires_human_approval'])}"
                )
                print("  Motivo:", REASONS[r["action"]])
                print(
                    "  Lifecycle:",
                    pt(r["current_lifecycle_state"]),
                    "→ sugestão",
                    pt(r["suggested_lifecycle_state"]),
                    "(não aplicada)",
                )
                for e in r["evidence"]:
                    print(
                        f"  Evidência {pt(e['metric'])}={number(e['observed'])} alvo={pt(e['target'])} {e['unit']} escopo={pt(e['scope'])} n={len(e['execution_ids'])}"
                    )
            elif details:
                print(
                    "  Decisão: nenhuma proposta sustentada. Revise suficiência dos dados e limites do agente."
                )
            if v["business_value"] and section in ("recommendation", "pipeline"):
                print(
                    "  Valor realizado DESCONHECIDO; custos de cenários e tempo até proposta não comprovam economia."
                )
    print(
        "* Resultado não normal do workflow (%), não correção do agente. ** Estimativa média do consumo atribuído ao papel."
    )
    print(
        "Desconhecido não é zero. Recomendação não é autorização. Lifecycle inalterado. Sem inferência de economia ou ROI."
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--fixture",
        choices=["stable", "cost", "optimize", "intervene", "review", "pause"],
    )
    source.add_argument("--live", action="store_true")
    p.add_argument(
        "--agent",
        choices=[
            "supervisor",
            "supply",
            "production",
            "logistics",
            "finance",
            "challenger",
            "recommendation",
        ],
    )
    p.add_argument("--mode", choices=["mock", "openai"], default="mock")
    p.add_argument(
        "--section",
        choices=["goals", "slo", "lifecycle", "recommendation", "pipeline", "cockpit"],
        default="cockpit",
    )
    p.add_argument("--url", default="http://localhost:8000")
    args = p.parse_args()
    if args.fixture:
        print(
            "FONTE: FIXTURE DIDÁTICA. Eventos/tokens sintéticos; sem chamadas LLM nem gravação no banco."
        )
        pricing = PricingConfig.model_validate_json(
            Path("config/lesson04-pricing.json").read_text()
        )
        views = [
            v.model_dump(mode="json")
            for v in ControlPlane(None, config=load_config(), pricing=pricing).evaluate(
                samples=fixture_samples(args.fixture),
                source="didactic_fixture",
                mode="openai",
                agent_id=args.agent,
            )
        ]
    else:
        print("FONTE: HISTÓRICO PERSISTIDO, modo=" + args.mode)
        path = (
            "/control-plane/agents"
            + ("/" + args.agent if args.agent else "")
            + "?mode="
            + args.mode
        )
        with urlopen(args.url.rstrip("/") + path, timeout=20) as response:
            result = json.load(response)
        views = [result] if args.agent else result
    show(views, args.section)


if __name__ == "__main__":
    main()
