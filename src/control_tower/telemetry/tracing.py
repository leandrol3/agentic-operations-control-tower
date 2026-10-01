"""Process-local OTel SDK. No global provider replacement and no implicit network."""
from contextlib import contextmanager
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from .context import current_context

_provider = None
_meter_provider = None
_instruments = {}


def enabled():
    return _provider is not None


def tracer():
    return (_provider or trace.NoOpTracerProvider()).get_tracer('control_tower.runtime', 'lesson03')


def identifiers():
    context = trace.get_current_span().get_span_context()
    return ({'trace_id': format(context.trace_id, '032x'), 'span_id': format(context.span_id, '016x')}
            if context.is_valid else {})


def attributes():
    context = current_context.get()
    parent = getattr(trace.get_current_span(), 'attributes', None) or {}
    attempt = {'control_tower.attempt': parent['control_tower.attempt']} if 'control_tower.attempt' in parent else {}
    return attempt | {f'control_tower.{key}': str(value) for key, value in
            (context.model_dump().items() if context else []) if value is not None and key != 'trace_id'}


def mark_error(span, error_type):
    # Never record_exception(error): messages/stacks may contain keys, DSNs or customer content.
    span.set_status(Status(StatusCode.ERROR))
    span.set_attribute('error.type', error_type)
    span.add_event('exception', {'exception.type': error_type})


@contextmanager
def operation(name, **kwargs):
    with tracer().start_as_current_span(name, attributes=attributes() | kwargs.pop('attributes', {}),
            record_exception=False, set_status_on_exception=False, **kwargs) as span:
        try:
            yield span
        except BaseException as error:
            mark_error(span, type(error).__name__)
            raise


def metric(name, value=1, **labels):
    instrument = _instruments.get(name)
    if instrument:
        (instrument.record if name == 'execution.duration' else instrument.add)(value, labels)


def initialize_tracing(settings, *, span_exporter=None, metric_reader=None):
    global _provider, _meter_provider, _instruments
    if not settings.otel_enabled:
        _provider, _meter_provider, _instruments = None, None, {}
        return None
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    resource = Resource.create({'service.name': settings.otel_service_name,
                                'deployment.environment.name': settings.app_env})
    provider = TracerProvider(resource=resource)
    readers = [metric_reader] if metric_reader else []
    endpoint = settings.otel_exporter_otlp_endpoint
    if span_exporter:
        provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    elif endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(
            endpoint=endpoint.rstrip('/') + '/v1/traces', timeout=2), schedule_delay_millis=500))
    if endpoint and not metric_reader:
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        readers.append(PeriodicExportingMetricReader(OTLPMetricExporter(
            endpoint=endpoint.rstrip('/') + '/v1/metrics', timeout=2), export_interval_millis=5000))
    _provider = provider
    _meter_provider = MeterProvider(resource=resource, metric_readers=readers)
    meter = _meter_provider.get_meter('control_tower.runtime')
    names = ('executions.started', 'executions.completed', 'executions.failed',
             'llm.calls', 'llm.failures', 'llm.tokens.input', 'llm.tokens.output')
    _instruments = {name: meter.create_counter(name, unit='1') for name in names}
    _instruments['execution.duration'] = meter.create_histogram('execution.duration', unit='s')
    return provider


def shutdown():
    global _provider, _meter_provider, _instruments
    if _meter_provider:
        _meter_provider.shutdown()
    if _provider:
        _provider.shutdown()
    _provider, _meter_provider, _instruments = None, None, {}
