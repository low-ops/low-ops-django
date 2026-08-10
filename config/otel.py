import logging

from config.env import get_otel_config

logger = logging.getLogger('lowops.otel')


def setup_otel():
    otel = get_otel_config()
    if not otel:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({'service.name': otel['service_name']})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=f"{otel['endpoint']}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        DjangoInstrumentor().instrument()
        logger.info('OpenTelemetry tracing enabled (service=%s)', otel['service_name'])
    except Exception as exc:
        logger.warning('OpenTelemetry setup failed: %s', exc)
