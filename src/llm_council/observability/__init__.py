"""Enhanced observability package for LLM Council platform."""

from .phoenix_tracer import PhoenixTracer, get_phoenix_tracer, setup_phoenix_tracing

# Aliases for backward compatibility
get_tracer = get_phoenix_tracer
setup_tracing = setup_phoenix_tracing

__all__ = ["PhoenixTracer", "get_phoenix_tracer", "setup_phoenix_tracing", "get_tracer", "setup_tracing"]