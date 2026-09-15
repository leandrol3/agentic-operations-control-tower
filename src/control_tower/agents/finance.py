"""Finance propõe pelo custo incremental total; Challenger revisa admissibilidade."""
from ..graph.state import FinanceReport, Investigation
from ..models import Incident
from ..scenarios import simulate
from ..tools import Tools


def analyze(tools: Tools, incident: Incident, evidence: Investigation) -> FinanceReport:
    scenarios = tuple(simulate(tools, incident, evidence, name) for name in ('A', 'B', 'C', 'D'))
    cheapest = min(scenarios, key=lambda s: (s.total_cost_brl, s.scenario_id))
    return FinanceReport(scenarios=scenarios, proposed_scenario=cheapest.scenario_id)
