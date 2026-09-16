"""Baseline em um processo: threads + capacidade simulada + grafo mock da Aula 1."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
from threading import BoundedSemaphore, Lock, current_thread
import time
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import Field

from ..graph.workflow import run_workflow
from ..models import Contract
from ..tools import Tools
from .events import ExecutionEvent, InMemoryEvents
from .incidents import IncidentEnvelope
from .models import Execution, Milliseconds


class BatchOptions(Contract):
    workers: Annotated[int, Field(ge=1, le=64)] = 1
    provider_limit: Annotated[int, Field(ge=1, le=64)] | None = None
    demo_delay_ms: Annotated[int, Field(ge=0, le=2000)] = 0


class BatchReport(Contract):
    mode: Literal['mock'] = 'mock'
    workload: Literal['reference_replay:INCIDENT-001'] = 'reference_replay:INCIDENT-001'
    incidents: int
    workers: int
    provider_limit: int | None
    demo_delay_ms: int
    completed: int
    failed: int
    duration_s: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    throughput: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    max_active: int
    waited: int
    max_waiting: int
    provider_wait_ms: Milliseconds
    executions: tuple[Execution, ...]
    events: tuple[ExecutionEvent, ...]


class SimulatedCapacity:
    """Limita workflows, não requests/s. Não é rate limit real de OpenAI."""
    def __init__(self, limit: int):
        self._semaphore = BoundedSemaphore(limit)
        self._lock = Lock()
        self.active = self.max_active = self.waiting = self.max_waiting = self.waited = 0
        self.wait_ms = 0.0

    @contextmanager
    def slot(self):
        if not self._semaphore.acquire(blocking=False):
            start = time.perf_counter()
            with self._lock:
                self.waited += 1
                self.waiting += 1
                self.max_waiting = max(self.max_waiting, self.waiting)
            self._semaphore.acquire()
            with self._lock:
                self.waiting -= 1
                self.wait_ms += (time.perf_counter() - start) * 1000
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            yield
        finally:
            with self._lock:
                self.active -= 1
            self._semaphore.release()


def run_batch(root: Path, incidents: tuple[IncidentEnvelope, ...], options: BatchOptions) -> BatchReport:
    if not incidents or len(incidents) > 5000:
        raise ValueError('Batch exige entre 1 e 5000 incidentes')
    # Dados compartilhados apenas para leitura; cada invocação cria seu próprio grafo/estado.
    tools = Tools(root)
    reference = tools.load_incident(root / 'incidents/incident_001.json')
    capacity = SimulatedCapacity(options.provider_limit or options.workers)
    initial = [Execution(execution_id=uuid4(), incident_id=i.incident_id) for i in incidents]
    logs = [InMemoryEvents() for _ in incidents]
    for execution, log in zip(initial, logs):
        log.emit(execution, 'intake', 'execution_queued')

    def process(pair):
        queued, log = pair
        started = time.perf_counter()
        running = Execution.model_validate(queued.model_dump() | {
            'status': 'running', 'started_at': datetime.now(timezone.utc),
            'worker_id': f'local:{os.getpid()}:{current_thread().name}', 'current_step': 'capacity_wait',
        })
        log.emit(running, 'worker', 'execution_started')
        step_starts = {}
        step_lock = Lock()

        def observe(agent, phase):
            now = time.perf_counter()
            with step_lock:
                if phase == 'início':
                    step_starts[agent] = now
                    event_type, duration = 'step_started', None
                else:
                    duration = (now - step_starts.pop(agent, now)) * 1000
                    event_type = 'step_failed' if phase == 'erro' else 'step_completed'
                log.emit(running, agent, event_type, duration)

        workflow_status = None
        try:
            with capacity.slot():
                # Uma espera por execução sob capacidade. Não altera o delay da CLI da Aula 1.
                if options.demo_delay_ms:
                    time.sleep(options.demo_delay_ms / 1000)
                state = run_workflow(tools, reference, observer=observe, llm=None)
                workflow_status = state.status
                if workflow_status != 'awaiting_approval':
                    raise ValueError('Workflow de referência bloqueado; execução não concluída')
            final = Execution.model_validate(running.model_dump() | {
                'status': 'completed', 'completed_at': datetime.now(timezone.utc),
                'current_step': 'awaiting_approval', 'workflow_status': workflow_status,
            })
        except Exception as error:
            # Isola falha por execução; não inventa sucesso nem faz retry. Não captura Ctrl-C.
            final = Execution.model_validate(running.model_dump() | {
                'status': 'failed', 'completed_at': datetime.now(timezone.utc), 'current_step': 'failed',
                'workflow_status': workflow_status, 'error': f'{type(error).__name__}: {error}',
            })
        log.emit(final, 'worker', 'execution_completed' if final.status == 'completed' else 'execution_failed',
                 (time.perf_counter() - started) * 1000)
        return final

    started = time.perf_counter()
    if options.workers == 1:
        results = tuple(process(pair) for pair in zip(initial, logs))
    else:
        with ThreadPoolExecutor(max_workers=options.workers, thread_name_prefix='lesson02') as executor:
            results = tuple(executor.map(process, zip(initial, logs)))
    duration = time.perf_counter() - started
    completed = sum(e.status == 'completed' for e in results)
    return BatchReport(
        incidents=len(incidents), workers=options.workers, provider_limit=options.provider_limit,
        demo_delay_ms=options.demo_delay_ms, completed=completed, failed=len(results)-completed,
        duration_s=duration, throughput=completed/duration if duration else 0,
        max_active=capacity.max_active, waited=capacity.waited, max_waiting=capacity.max_waiting,
        provider_wait_ms=capacity.wait_ms, executions=results,
        events=tuple(event for log in logs for event in log.snapshot()),
    )


def render_batch(report: BatchReport) -> str:
    return '\n'.join([
        'Batch execution | mock | threads locais, sem Celery',
        'Carga de referência: INCIDENT-001 por envelope; não analisa as 5 categorias.',
        '----------------', f'incidents: {report.incidents}', f'workers: {report.workers}',
        f'provider_limit: {report.provider_limit or "sem limite adicional"} | pico ativo: {report.max_active}',
        f'completed: {report.completed}', f'failed: {report.failed}',
        f'duration: {report.duration_s:.3f} s', f'throughput: {report.throughput:.2f} incidents/s (completed)',
        f'waited: {report.waited} | pico esperando capacidade: {report.max_waiting}',
        f'provider_wait_total: {report.provider_wait_ms/1000:.3f} worker-s (somatório, não duração)',
        f'delay didático: {report.demo_delay_ms} ms por execução; não é benchmark de produção.',
        'completed = workflow terminou; aprovação humana pendente. Nenhuma ação executada.',
        'Estado/eventos em memória; fila durável, deduplicação e retry ainda não existem.',
    ])
