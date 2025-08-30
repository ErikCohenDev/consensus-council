"""Observability and tracing constants for non-deterministic LLM applications."""

# Tracing configuration
TRACING_CONFIG = {
    "SERVICE_NAME": "llm-council-backend",
    "WEBSOCKET_SPAN_NAME": "websocket.connection",
    "AUDIT_SPAN_NAME": "audit.run",
    "DEBATE_SPAN_NAME": "audit.debate",
    "MODEL_CALL_SPAN_NAME": "llm.call",
    "CONSENSUS_SPAN_NAME": "consensus.calculation",
}

# Metrics and evaluation
EVALUATION_METRICS = {
    "CONSENSUS_THRESHOLD": 0.67,
    "AGREEMENT_THRESHOLD": 1.0,
    "MIN_DEBATE_ROUNDS": 1,
    "MAX_DEBATE_ROUNDS": 5,
    "COST_WARNING_THRESHOLD": 5.0,  # USD
    "EXECUTION_TIME_WARNING": 300.0,  # seconds
}

# Logging levels for different components
LOG_LEVELS = {
    "WEBSOCKET": "INFO",
    "AUDIT": "INFO", 
    "DEBATE": "DEBUG",
    "CONSENSUS": "INFO",
    "MODEL_CALLS": "DEBUG",
    "ERRORS": "ERROR",
}

# Attributes for structured logging and tracing
SPAN_ATTRIBUTES = {
    "AUDIT_ID": "audit.id",
    "PROJECT_ID": "project.id", 
    "STAGE": "audit.stage",
    "MODEL": "audit.model",
    "DOCS_PATH": "docs.path",
    "DOCUMENT_STAGE": "document.stage",
    "DOCUMENT_NAME": "document.name",
    "COUNCIL_MEMBER_ROLE": "council.member.role",
    "DEBATE_ROUND": "debate.round",
    "CONSENSUS_SCORE": "consensus.score",
    "EXECUTION_TIME": "execution.time_seconds",
    "TOTAL_COST": "total.cost_usd",
    "ERROR_TYPE": "error.type",
    "ERROR_MESSAGE": "error.message",
}

# Non-deterministic application monitoring
NONDETERMINISTIC_METRICS = {
    "MODEL_RESPONSE_VARIANCE": "model.response.variance",
    "CONSENSUS_STABILITY": "consensus.stability",
    "RETRY_COUNT": "operation.retry_count",
    "CACHE_HIT_RATE": "cache.hit_rate",
    "AGREEMENT_DISTRIBUTION": "agreement.distribution",
}