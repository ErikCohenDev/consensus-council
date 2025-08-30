"""Observability helpers for tracing/metrics/logging.

Best-effort setup that prefers Phoenix/OTel if present, otherwise
falls back to a basic OTLP or console exporter. Safe to import when
dependencies are missing; it will no-op gracefully.
"""
from __future__ import annotations

import os
from typing import Optional


def setup_tracing(service_name: str = "llm-council-backend"):
    """Initialize tracing with Phoenix/OTel if available; no-op on failure.

    Respects env vars:
    - PHOENIX_OTLP: OTLP endpoint (e.g., http://localhost:4318)
    - OTEL_EXPORTER_OTLP_ENDPOINT: standard OTel endpoint
    - OTEL_SERVICE_NAME: overrides service name
    """
    try:
        # Prefer Phoenix helper if installed
        from phoenix.otel import register  # type: ignore

        svc = os.getenv("OTEL_SERVICE_NAME", service_name)
        provider = register(service_name=svc, endpoint=os.getenv("PHOENIX_OTLP"))
        return provider
    except Exception:
        pass

    # Fallback: basic OTel with OTLP HTTP if configured, else console exporter
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry import trace

        svc = os.getenv("OTEL_SERVICE_NAME", service_name)
        resource = Resource.create({"service.name": svc})
        provider = TracerProvider(resource=resource)

        # OTLP HTTP exporter if endpoint set
        otlp = os.getenv("PHOENIX_OTLP") or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

                exporter = OTLPSpanExporter(endpoint=f"{otlp.rstrip('/')}/v1/traces")
                provider.add_span_processor(BatchSpanProcessor(exporter))
            except Exception:
                provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        else:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(provider)
        return provider
    except Exception:
        # As a last resort, swallow errors
        return None


def get_tracer(name: str):
    """Get a tracer; safe even if OTel not installed."""
    try:
        from opentelemetry import trace  # type: ignore

        return trace.get_tracer(name)
    except Exception:
        class _NoopSpan:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def set_attribute(self, *args, **kwargs):
                return None
            def add_event(self, *args, **kwargs):
                return None
        class _NoopTracer:
            def start_as_current_span(self, *args, **kwargs):
                return _NoopSpan()
        return _NoopTracer()


__all__ = ["setup_tracing", "get_tracer"]
