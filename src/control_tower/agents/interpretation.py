"""LLM interpreta; evidência, elegibilidade, cálculos e aprovação continuam em código."""
from pydantic import ValidationError

from ..llm import ChallengerJudgment, InvestigationPlan, RecommendationDecision, SpecialistSynthesis
from ..graph.state import Finding, Review
from ..models import Recommendation
from . import supervisor

NAMES = ('supply', 'production', 'logistics')


def structured(llm, role, schema, context):
    try:
        response = llm.parse(role, schema, context)
        return schema.model_validate(response.model_dump())
    except ValidationError:
        raise ValueError(f'LLM/{role}: saída fora do contrato Pydantic') from None


def supervise(llm, state):
    known = supervisor.supervise(state)
    if known.get('blockers'):
        return known
    plan = structured(llm, 'supervisor', InvestigationPlan,
                      {'incident': state.incident.model_dump(mode='json')})
    selected = {task.specialist for task in plan.tasks}
    if selected != set(NAMES):
        raise ValueError('Supervisor: comparação A–D exige supply, production e logistics; plano incompleto')
    # Ordem canônica para a barreira e comparação; seleção original preservada no contrato.
    return {'plan': NAMES, 'supervisor_reason': plan.interpretation, 'llm_plan': plan}


def synthesize(llm, name, incident, evidence, plan):
    context = {'incident': incident.model_dump(mode='json'),
               'evidence': evidence.model_dump(mode='json'),
               'allowed_evidence_refs': list(type(evidence).model_fields),
               'question': next(t.question for t in plan.tasks if t.specialist == name)}
    context['output_rule'] = 'evidence_refs deve usar somente nomes de allowed_evidence_refs.'
    synthesis = structured(llm, name, SpecialistSynthesis, context)
    if not set(synthesis.evidence_refs) <= set(type(evidence).model_fields):
        raise ValueError(f'{name}: referência de evidência desconhecida na síntese')
    return synthesis


def challenge(llm, state, deterministic_review):
    judgment = structured(llm, 'challenger', ChallengerJudgment, {
        'evidence': state.investigation.model_dump(mode='json'),
        'specialist_syntheses': {n: getattr(state, n+'_synthesis').model_dump(mode='json') for n in NAMES},
        'finance': state.finance.model_dump(mode='json'),
        'deterministic_review': deterministic_review.model_dump(mode='json'),
    })
    additions = tuple(Finding(scenario_id=f.scenario_id, category=f.category,
                              blocking=False, message=f'[LLM] {f.message}') for f in judgment.findings)
    return {'review': Review(findings=deterministic_review.findings + additions,
                             selected_scenario=deterministic_review.selected_scenario),
            'llm_challenger': judgment}


def template(state, scenario_id):
    selected = next(s for s in state.finance.scenarios if s.scenario_id == scenario_id)
    baseline = next(s for s in state.finance.scenarios if s.scenario_id == 'A')
    risks = [f.message for f in state.review.findings if f.scenario_id in ('all', scenario_id)]
    return Recommendation(
        incident_id=state.incident.incident_id, severity='high',
        recommended_action=f'Cenário {selected.scenario_id}: {selected.description}',
        estimated_cost_brl=selected.total_cost_brl,
        avoided_penalty_brl=max(0, baseline.penalty_brl - selected.penalty_brl),
        customer_delay_days=max(d.delay_days for d in selected.deliveries),
        confidence=0.65, risks=risks, approval_required=True,
    )


def recommend(llm, state):
    eligible = [s.scenario_id for s in state.finance.scenarios if not any(
        f.blocking and f.scenario_id in ('all', s.scenario_id) for f in state.review.findings)]
    templates = {sid: template(state, sid) for sid in eligible}
    decision = structured(llm, 'recommendation', RecommendationDecision, {
        'evidence': state.investigation.model_dump(mode='json'),
        'finance': state.finance.model_dump(mode='json'),
        'review': state.review.model_dump(mode='json'),
        'eligible_scenarios': eligible,
        'templates': {sid: t.model_dump(mode='json') for sid, t in templates.items()},
    })
    if decision.scenario_id not in templates:
        raise ValueError('Recommendation: LLM escolheu cenário bloqueado pelas regras determinísticas')
    expected = templates[decision.scenario_id]
    proposed = decision.recommendation
    for field in ('incident_id', 'estimated_cost_brl', 'avoided_penalty_brl',
                  'customer_delay_days', 'confidence', 'approval_required'):
        if getattr(proposed, field) != getattr(expected, field):
            raise ValueError(f'Recommendation: LLM alterou campo determinístico {field}')
    # Mantém a ação operacional canônica e todos os riscos; narrativa LLM é consultiva.
    final = Recommendation.model_validate(proposed.model_dump() | {
        'recommended_action': expected.recommended_action,
        'risks': list(dict.fromkeys(expected.risks + proposed.risks)),
    })
    review = Review(findings=state.review.findings, selected_scenario=decision.scenario_id)
    return {'recommendation': final, 'review': review, 'llm_recommendation': decision}
