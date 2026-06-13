"""Structured logging + OpenTelemetry tracing for cool calls."""

from __future__ import annotations

import os
import time

import structlog
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def configure_observability() -> None:
    "Set up JSON logs and OTel tracer. Call once at startup."
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )
    provider = TracerProvider(resource=Resource.create({"service.name": "carbon-aware-mcp"}))

    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):  # send to a real backend if configured
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

log = structlog.get_logger()
tracer = trace.get_tracer("carbon-aware-mcp")

class ObservabilityMiddleware(Middleware):
    """Times, logs, and traces every tool call. Records errors on the span."""

    async def on_call_tool(self, context: MiddlewareContext, call_next: CallNext):
        tool = context.message.name
        arg_keys = sorted((context.message.arguments or {}).keys())  # keys, not values
        with tracer.start_as_current_span(f"call.{tool}") as span:
            span.set_attribute("mcp.tool", tool)
            span.set_attribute("mcp.arg_keys", arg_keys)
            start = time.perf_counter()
            try:
                result = await call_next(context)
            except Exception as exc:
                span.record_exception(exc)
                log.error("tool_error", tool=tool, error=type(exc).__name__, duration_ms=round((time.perf_counter() - start) *1000, 1))
                raise
            log.info("tool_call", tool=tool, arg_keys=arg_keys, duration_ms=round((time.perf_counter() - start) *1000, 1))
            return result





