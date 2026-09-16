"""Uma task reutiliza o workflow inteiro; nenhum checkpoint de nós."""
import os
import time
from threading import Lock
from .celery_app import app
from .config import MAX_ATTEMPTS, project_root
from .durable import FinalResult, TaskOptions
from .incidents import IncidentEnvelope
from .store import Store
from ..graph.workflow import run_workflow
from ..tools import Tools
from ..graph.state import Approval


class WorkflowFailure(Exception):
    pass


@app.task(bind=True, name='control_tower.execute', max_retries=2)
def execute(self, envelope, execution_id, idempotency_key):
    envelope = IncidentEnvelope.model_validate(envelope).model_dump(mode='json')
    store = Store()
    with store.acquire(execution_id, idempotency_key, envelope) as session:
        if session is None:  # outra entrega já está processando, não cria execução
            return {'execution_id': execution_id, 'duplicate': True}
        if not session.begin(f'{self.request.hostname}:{os.getpid()}'):
            return {'execution_id': execution_id, 'status': session.execution.status}
        options = TaskOptions.model_validate(session.options)
        starts, lock = {}, Lock()

        def observe(agent, phase):
            with lock:
                now = time.perf_counter()
                duration = None
                if phase == 'início':
                    starts[agent] = now
                else:
                    duration = (now - starts.pop(agent, now)) * 1000
                session.step(agent, phase, duration)

        workflow_started = time.perf_counter()
        try:
            from .llm_runtime import settings_for
            settings = settings_for(options)
            if options.demo_delay_ms:
                time.sleep(options.demo_delay_ms / 1000)
            root = project_root()
            tools = Tools(root)
            incident = tools.load_incident(root / 'incidents/incident_001.json')
            failure = options.fail_specialist if options.fail_always or session.attempts == 1 else None
            if options.llm_mode == 'openai':
                result = llm_workflow(tools, incident, observe, settings, session, options, envelope)
            else:
                state = run_workflow(tools, incident, observer=observe, fail_specialist=failure, llm=None)
                if state.status != 'awaiting_approval':
                    raise WorkflowFailure('; '.join(state.blockers) or 'Workflow bloqueado')
                result = FinalResult(recommendation=state.recommendation, approval=state.approval)
            session.finish(result, duration_ms=(time.perf_counter()-workflow_started)*1000)
        except WorkflowFailure as error:
            retry = session.attempts < MAX_ATTEMPTS
            session.fail(str(error), retry)
            if retry:
                raise self.retry(exc=error, countdown=2 ** session.attempts)
            raise
        except Exception as error:
            session.fail(f'{type(error).__name__}: {error}', retry=False)
            raise
    return {'execution_id': execution_id, 'status': 'completed'}


def llm_workflow(tools, incident, observe, settings, session, options, envelope):
    from .llm_runtime import ProviderUnavailable, ResilientInterpreter
    interpreter = ResilientInterpreter(settings, session, options)
    try:
        state = run_workflow(tools, incident, observer=observe, llm=interpreter)
        if state.status != 'awaiting_approval':
            raise ProviderUnavailable('workflow_validation_blocked', False)
        return FinalResult(mode='openai', model=settings.model,
                           recommendation=state.recommendation, approval=state.approval)
    except ProviderUnavailable as error:
        reason = str(error)
        if error.transient:
            session.event('llm.fallback_activated', detail=f'{reason}; decision={options.fallback}')
            safe_reference = (envelope['payload'].get('reference_case_id') == 'INCIDENT-001'
                              and envelope['payload'].get('workload') == 'reference_replay')
            if options.fallback == 'deterministic_reference' and safe_reference:
                # Descarta sínteses parciais. Mesmo grafo, novo estado, capacidades determinísticas.
                # Isto é continuidade limitada do case, não mock como fallback de produção.
                try:
                    state = run_workflow(tools, incident, observer=observe, llm=None)
                except (ValueError, OSError):
                    state = None
                if state is not None and state.status == 'awaiting_approval':
                    session.event('llm.degraded', detail='Case validado; síntese determinística; aprovação humana obrigatória')
                    return FinalResult(mode='degraded', outcome='degraded_recommendation', reason=reason,
                                       recommendation=state.recommendation, approval=state.approval)
                reason = 'deterministic_validation_blocked'
        session.event('llm.escalated', detail=reason)
        return FinalResult(mode='openai', model=settings.model, outcome='human_review_required',
                           reason=reason, approval=Approval(authority='operations_manager'))
