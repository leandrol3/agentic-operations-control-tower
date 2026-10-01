"""W3C only; custom execution IDs are domain attributes, never substitute parents."""
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context import Context

_propagator = TraceContextTextMapPropagator()


def extract(headers):
    return _propagator.extract({str(k).lower(): v for k, v in (headers or {}).items()}, context=Context())


def inject(headers):
    _propagator.inject(headers)
