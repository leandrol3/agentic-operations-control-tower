"""SDK preparado; nenhum span de aplicação/autoinstrumentação no start."""


def initialize_tracing(settings):
    if not settings.otel_enabled:
        return None  # não importa SDK, não inicia thread nem faz rede
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    provider = TracerProvider(resource=Resource.create({
        'service.name': settings.otel_service_name,
        'deployment.environment.name': settings.app_env,
    }))
    if settings.otel_exporter_otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        endpoint = settings.otel_exporter_otlp_endpoint.rstrip('/') + '/v1/traces'
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, timeout=3)))
    # Provider pertence ao runtime, não substitui o singleton global em testes.
    return provider
