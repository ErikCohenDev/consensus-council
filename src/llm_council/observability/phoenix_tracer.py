"""Arize Phoenix observability integration for LLM Council platform.

Provides comprehensive tracing, evaluation, and monitoring for non-deterministic
LLM applications with focus on consensus, debate quality, and model reliability.
"""

from __future__ import annotations
import os
import time
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

try:
    from phoenix.otel import register
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from openinference.instrumentation.openai import OpenAIInstrumentor
    from openinference.instrumentation.anthropic import AnthropicInstrumentor
    PHOENIX_AVAILABLE = True
except ImportError:
    PHOENIX_AVAILABLE = False
    trace = None

from ..constants.observability import (
    TRACING_CONFIG, SPAN_ATTRIBUTES, EVALUATION_METRICS, 
    NONDETERMINISTIC_METRICS
)


class PhoenixTracer:
    """Enhanced tracer for LLM Council with Phoenix integration."""
    
    def __init__(self):
        self.tracer = None
        self.phoenix_enabled = False
        self._initialize_phoenix()
    
    def _initialize_phoenix(self):
        """Initialize Phoenix tracing if available."""
        if not PHOENIX_AVAILABLE:
            print("⚠️  Phoenix not available. Install with: pip install arize-phoenix-otel openinference-instrumentation-openai")
            return
            
        try:
            # Register Phoenix with OpenTelemetry
            phoenix_endpoint = os.getenv("PHOENIX_ENDPOINT", "http://localhost:6006")
            tracer_provider = register(
                project_name="llm-council",
                endpoint=phoenix_endpoint
            )
            
            # Auto-instrument LLM providers
            OpenAIInstrumentor().instrument()
            AnthropicInstrumentor().instrument()
            
            self.tracer = trace.get_tracer(TRACING_CONFIG["SERVICE_NAME"])
            self.phoenix_enabled = True
            print(f"✅ Phoenix tracing enabled: {phoenix_endpoint}")
            
        except Exception as e:
            print(f"⚠️  Phoenix initialization failed: {e}")
            self.phoenix_enabled = False
    
    @contextmanager
    def trace_audit_run(self, audit_id: str, project_id: Optional[str], 
                       stage: Optional[str], model: str, docs_path: str):
        """Trace an entire audit run with context."""
        if not self.phoenix_enabled or not self.tracer:
            yield None
            return
            
        attributes = {
            SPAN_ATTRIBUTES["AUDIT_ID"]: audit_id,
            SPAN_ATTRIBUTES["PROJECT_ID"]: project_id or "unknown",
            SPAN_ATTRIBUTES["STAGE"]: stage or "all",
            SPAN_ATTRIBUTES["MODEL"]: model,
            SPAN_ATTRIBUTES["DOCS_PATH"]: docs_path,
        }
        
        with self.tracer.start_as_current_span(
            TRACING_CONFIG["AUDIT_SPAN_NAME"], 
            attributes=attributes
        ) as span:
            start_time = time.perf_counter()
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute(SPAN_ATTRIBUTES["ERROR_TYPE"], type(e).__name__)
                span.set_attribute(SPAN_ATTRIBUTES["ERROR_MESSAGE"], str(e))
                raise
            finally:
                execution_time = time.perf_counter() - start_time
                span.set_attribute(SPAN_ATTRIBUTES["EXECUTION_TIME"], execution_time)
                
                # Warn on slow execution
                if execution_time > EVALUATION_METRICS["EXECUTION_TIME_WARNING"]:
                    span.add_event("slow_execution_warning", {
                        "threshold_seconds": EVALUATION_METRICS["EXECUTION_TIME_WARNING"],
                        "actual_seconds": execution_time
                    })
    
    @contextmanager 
    def trace_debate_round(self, round_number: int, participants: List[str],
                          document_stage: str, document_name: str):
        """Trace a council debate round."""
        if not self.phoenix_enabled or not self.tracer:
            yield None
            return
            
        attributes = {
            SPAN_ATTRIBUTES["DEBATE_ROUND"]: round_number,
            SPAN_ATTRIBUTES["DOCUMENT_STAGE"]: document_stage,
            SPAN_ATTRIBUTES["DOCUMENT_NAME"]: document_name,
            "debate.participants": ",".join(participants),
            "debate.participant_count": len(participants),
        }
        
        with self.tracer.start_as_current_span(
            TRACING_CONFIG["DEBATE_SPAN_NAME"],
            attributes=attributes
        ) as span:
            start_time = time.perf_counter()
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            finally:
                duration = time.perf_counter() - start_time
                span.set_attribute("debate.duration_seconds", duration)
    
    @contextmanager
    def trace_consensus_calculation(self, scores: List[float], method: str = "trimmed_mean"):
        """Trace consensus calculation with variance tracking."""
        if not self.phoenix_enabled or not self.tracer:
            yield None
            return
            
        attributes = {
            "consensus.method": method,
            "consensus.score_count": len(scores),
            "consensus.min_score": min(scores) if scores else 0,
            "consensus.max_score": max(scores) if scores else 0,
        }
        
        # Calculate variance for non-deterministic monitoring
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            variance = sum((x - mean_score) ** 2 for x in scores) / len(scores)
            attributes[NONDETERMINISTIC_METRICS["MODEL_RESPONSE_VARIANCE"]] = variance
        
        with self.tracer.start_as_current_span(
            TRACING_CONFIG["CONSENSUS_SPAN_NAME"],
            attributes=attributes  
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
    
    def trace_model_call(self, role: str, model: str, provider: str, 
                        input_tokens: Optional[int] = None, 
                        output_tokens: Optional[int] = None,
                        cost_usd: Optional[float] = None):
        """Create a span for individual model calls.""" 
        if not self.phoenix_enabled or not self.tracer:
            return
            
        attributes = {
            SPAN_ATTRIBUTES["COUNCIL_MEMBER_ROLE"]: role,
            "llm.model": model,
            "llm.provider": provider,
        }
        
        if input_tokens:
            attributes["llm.input_tokens"] = input_tokens
        if output_tokens:
            attributes["llm.output_tokens"] = output_tokens  
        if cost_usd:
            attributes["llm.cost_usd"] = cost_usd
            
            # Cost warning
            if cost_usd > EVALUATION_METRICS["COST_WARNING_THRESHOLD"]:
                attributes["cost_warning"] = True
        
        span = self.tracer.start_span(
            TRACING_CONFIG["MODEL_CALL_SPAN_NAME"],
            attributes=attributes
        )
        return span
    
    def add_evaluation_metrics(self, span, consensus_score: float, 
                             agreement_level: float, retry_count: int = 0):
        """Add evaluation metrics to a span for LLM reliability tracking."""
        if not span:
            return
            
        span.set_attribute(SPAN_ATTRIBUTES["CONSENSUS_SCORE"], consensus_score)
        span.set_attribute("agreement.level", agreement_level)
        span.set_attribute(NONDETERMINISTIC_METRICS["RETRY_COUNT"], retry_count)
        
        # Quality indicators
        if consensus_score < EVALUATION_METRICS["CONSENSUS_THRESHOLD"]:
            span.add_event("low_consensus_warning", {
                "threshold": EVALUATION_METRICS["CONSENSUS_THRESHOLD"],
                "actual": consensus_score
            })
        
        if agreement_level > EVALUATION_METRICS["AGREEMENT_THRESHOLD"]:
            span.add_event("high_disagreement_detected", {
                "agreement_level": agreement_level
            })


# Global instance
_phoenix_tracer: Optional[PhoenixTracer] = None

def get_phoenix_tracer() -> PhoenixTracer:
    """Get or create the global Phoenix tracer instance."""
    global _phoenix_tracer
    if _phoenix_tracer is None:
        _phoenix_tracer = PhoenixTracer()
    return _phoenix_tracer

def setup_phoenix_tracing(service_name: str = "llm-council-backend"):
    """Setup Phoenix tracing for the application."""
    tracer = get_phoenix_tracer()
    print(f"🔍 Phoenix observability setup for {service_name}")
    return tracer