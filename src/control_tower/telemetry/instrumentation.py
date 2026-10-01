"""Explicit runtime adapters around frozen course code; CLI lessons 1/2 stay untouched.

Installed once by lesson03 bootstrap. Existing observer brackets actual LangGraph nodes;
contextvars are copied by LangGraph into independent parallel tasks. No new graph.
"""
from contextvars import ContextVar
from functools import wraps
from threading import Lock, get_ident
import time
from opentelemetry import trace, context as otel_context
from opentelemetry.trace import SpanKind
from . import tracing
from .propagation import inject

_installed = False
_llm_scope = ContextVar('llm_span_scope', default=None)
_node = ContextVar('observed_agent', default=None)
_degraded = ContextVar('deterministic_continuity', default=False)


def observed_workflow(original, tools, incident, **options):
    if not tracing.enabled():
        return original(tools, incident, **options)
    observer = options.get('observer')
    active, lock = {}, Lock()
    llm = options.get('llm')
    from ..runtime.settings import RuntimeSettings
    settings = RuntimeSettings()

    def observe(name, phase):
        key = (get_ident(), name)
        if phase == 'início':
            title = ('deterministic finance' if name == 'finance' else
                     'agent ' + name if name in ('supervisor','supply','production','logistics',
                                                'challenger','recommendation') else 'workflow ' + name)
            span = tracing.tracer().start_span(title, attributes=tracing.attributes() | {'agent.name': name,
                'agent.role': 'deterministic' if name == 'finance' else name})
            cm = otel_context.attach(trace.set_span_in_context(span))
            token = _node.set(name)
            with lock:
                active[key] = (cm, span, token)
            # Delay exists only in the opt-in runtime demo, never hidden in data/provider latency.
            if name == 'logistics' and settings.demo_agent_delay_ms:
                span.set_attribute('demo_delay_ms', settings.demo_agent_delay_ms)
                time.sleep(settings.demo_agent_delay_ms / 1000)
        if observer:
            observer(name, phase)
        if phase != 'início':
            with lock:
                entry = active.pop(key, None)
            if entry:
                cm, span, token = entry
                if phase == 'erro':
                    tracing.mark_error(span, 'node_failed')
                elif llm is None and name in ('supervisor','supply','production','logistics','challenger','recommendation'):
                    # Boundary marker for the existing deterministic substitute; no inference/usage claimed.
                    with tracing.operation('llm completion', attributes={
                        'gen_ai.provider.name': 'deterministic' if _degraded.get() else 'mock',
                        'control_tower.llm.mode': 'degraded' if _degraded.get() else 'mock',
                        'control_tower.llm.operation': 'deterministic_substitute', 'agent.name': name}):
                        pass
                    tracing.metric('llm.calls', provider='deterministic' if _degraded.get() else 'mock')
                _node.reset(token)
                otel_context.detach(cm)
                span.end()

    with tracing.operation('workflow incident-investigation') as workflow_span:
        try:
            state = original(tools, incident, **(options | {'observer': observe}))
            workflow_span.set_attribute('execution.outcome', state.status)
            if state.status == 'blocked':
                tracing.mark_error(workflow_span, 'workflow_blocked')
            return state
        finally:
            # Exceptions can bypass the historical observer's end callback. Those nodes still end.
            # Their context lives in LangGraph's copied task context, not this parent's context.
            for _, span, _ in active.values():
                tracing.mark_error(span, 'node_aborted')
                span.end()


def _wrap_tool(original, name):
    @wraps(original)
    def wrapped(*args, **kwargs):
        if not tracing.enabled() or not _node.get():
            return original(*args, **kwargs)
        with tracing.operation('tool ' + name, attributes={'tool.name': name}):
            return original(*args, **kwargs)
    return wrapped


def observe_event(session, kind, agent='worker', **fields):
    if not tracing.enabled():
        return
    span = trace.get_current_span()
    span.set_attribute('control_tower.attempt', session.execution.attempt)
    if kind in ('execution.started', 'execution.completed', 'execution.failed'):
        tracing.metric('executions.' + kind.split('.')[1])
    if kind == 'execution.started':
        _degraded.set(False)
        session._otel_started = time.perf_counter()
    if kind in ('execution.completed', 'execution.failed') and hasattr(session, '_otel_started'):
        tracing.metric('execution.duration', time.perf_counter() - session._otel_started,
                       outcome=kind.split('.')[1])
        del session._otel_started
    if kind == 'llm.requested':
        cm = tracing.operation('llm completion', kind=SpanKind.CLIENT, attributes={
            'agent.name': agent, 'gen_ai.provider.name': 'openai',
            'gen_ai.request.model': session.options.get('llm_model', 'unknown'),
            'control_tower.llm.mode': 'openai',
            'control_tower.llm.simulated_failure': session.options.get('llm_failure') == 'timeout'})
        call = cm.__enter__()
        _llm_scope.set((cm, call))
        tracing.metric('llm.calls', provider='openai')
    elif kind in ('llm.failed', 'llm.completed'):
        entry = _llm_scope.get()
        if entry:
            cm, call = entry
            if kind == 'llm.failed':
                tracing.mark_error(call, 'provider_failure')
                tracing.metric('llm.failures', provider='openai')
            for side in ('input', 'output'):
                tokens = fields.get(side + '_tokens')
                if tokens is not None:
                    call.set_attribute(f'gen_ai.usage.{side}_tokens', tokens)
                    tracing.metric(f'llm.tokens.{side}', tokens, provider='openai')
            cm.__exit__(None, None, None)
            _llm_scope.set(None)
    if kind in ('llm.retry', 'llm.fallback_activated', 'llm.degraded', 'llm.escalated',
                'execution.retry', 'execution.interrupted'):
        attrs = {'control_tower.attempt': session.execution.attempt}
        if kind == 'llm.fallback_activated':
            _degraded.set(session.options.get('fallback') == 'deterministic_reference')
            attrs['fallback.mode'] = session.options.get('fallback', 'human')
        trace.get_current_span().add_event(kind, attrs)
    if kind == 'execution.completed' and session.execution.result:
        span.set_attribute('execution.outcome', session.execution.result.outcome)
    if kind == 'execution.failed':
        tracing.mark_error(span, 'execution_failed')


def install():
    global _installed
    if _installed:
        return
    from ..distributed import tasks
    from ..distributed.store import Session
    from ..graph import workflow
    from ..tools import Tools
    original_workflow = workflow.run_workflow
    @wraps(original_workflow)
    def run(tools, incident, **options):
        return observed_workflow(original_workflow, tools, incident, **options)
    workflow.run_workflow = tasks.run_workflow = run
    for method, name in {'get_stock': 'inventory.lookup', 'get_supplier': 'supplier.lookup',
                          'get_orders': 'production.lookup', 'get_routes': 'logistics.lookup'}.items():
        setattr(Tools, method, _wrap_tool(getattr(Tools, method), name))
    original_event = Session.event
    @wraps(original_event)
    def event(session, kind, agent='worker', *args, **kwargs):
        result = original_event(session, kind, agent, *args, **kwargs)
        observe_event(session, kind, agent, **kwargs)
        return result
    Session.event = event
    original_publish = tasks.execute.apply_async
    @wraps(original_publish)
    def publish(*args, **kwargs):
        if not tracing.enabled():
            return original_publish(*args, **kwargs)
        parent_attrs = getattr(trace.get_current_span(), 'attributes', None) or {}
        submission = {k: parent_attrs[k] for k in ('control_tower.operation', 'control_tower.version')
                      if k in parent_attrs}
        with tracing.operation('messaging publish incident', kind=SpanKind.PRODUCER, attributes=submission | {
            'messaging.system': 'redis', 'messaging.destination.name': 'lesson02',
            'messaging.operation.type': 'send', 'messaging.operation.name': 'publish'}):
            headers = dict(kwargs.pop('headers', {}) or {})
            inject(headers)
            return original_publish(*args, headers=headers, **kwargs)
    tasks.execute.apply_async = publish
    _installed = True
