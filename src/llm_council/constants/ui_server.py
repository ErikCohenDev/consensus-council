"""UI server constants and configuration values."""

# Server configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_DOCS_PATH = "./docs"

# CORS settings
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# API response messages
API_MESSAGES = {
    "FRONTEND_NOT_BUILT": "Frontend not built",
    "UNKNOWN_PROJECT": "Unknown project; provide docsPath or register project first",
    "OPENAI_KEY_MISSING": "OPENAI_API_KEY not set",
    "GRAPH_GENERATION_STARTED": "Graph generation started.",
    "AUDIT_TIME_BUDGET_EXCEEDED": "Audit time budget exceeded",
    "MAX_RECONNECT_ATTEMPTS": "Max reconnect attempts reached",
    "REQUESTED_RUN_NOT_ACTIVE": "Requested run not active; returning current snapshot.",
    "REQUESTED_AUDIT_NOT_ACTIVE": "Requested audit not active; returning current snapshot.",
}

# Model provider configurations
MODEL_CATALOG_FALLBACK = {
    'gpt-4o': {
        'provider': 'OpenAI',
        'label': 'gpt-4o',
        'inPricePer1K': 0.005,
        'outPricePer1K': 0.015,
        'contextK': 128
    },
    'gpt-4o-mini': {
        'provider': 'OpenAI',
        'label': 'gpt-4o-mini',
        'inPricePer1K': 0.00015,
        'outPricePer1K': 0.0006,
        'contextK': 128
    },
    'gpt-4-turbo': {
        'provider': 'OpenAI',
        'label': 'gpt-4-turbo',
        'inPricePer1K': 0.01,
        'outPricePer1K': 0.03,
        'contextK': 128
    },
    'claude-3-5-sonnet': {
        'provider': 'Anthropic',
        'label': 'claude-3.5-sonnet',
        'inPricePer1K': 0.003,
        'outPricePer1K': 0.015,
        'contextK': 200
    },
    'claude-3-opus': {
        'provider': 'Anthropic',
        'label': 'claude-3-opus',
        'inPricePer1K': 0.015,
        'outPricePer1K': 0.075,
        'contextK': 200
    },
    'claude-3-haiku': {
        'provider': 'Anthropic',
        'label': 'claude-3-haiku',
        'inPricePer1K': 0.00025,
        'outPricePer1K': 0.00125,
        'contextK': 200
    },
    'gemini-1.5-pro': {
        'provider': 'Google',
        'label': 'gemini-1.5-pro',
        'inPricePer1K': 0.0035,
        'outPricePer1K': 0.0105,
        'contextK': 1000
    },
    'gemini-1.5-flash': {
        'provider': 'Google',
        'label': 'gemini-1.5-flash',
        'inPricePer1K': 0.00035,
        'outPricePer1K': 0.00053,
        'contextK': 1000
    },
    'llama-3.1-70b-instruct': {
        'provider': 'Meta',
        'label': 'llama-3.1-70b-instruct',
        'inPricePer1K': 0.00059,
        'outPricePer1K': 0.00279,
        'contextK': 128
    },
    'llama-3.1-8b-instruct': {
        'provider': 'Meta',
        'label': 'llama-3.1-8b-instruct',
        'inPricePer1K': 0.0001,
        'outPricePer1K': 0.0004,
        'contextK': 128
    },
    'mistral-large-2407': {
        'provider': 'Mistral',
        'label': 'mistral-large-2407',
        'inPricePer1K': 0.003,
        'outPricePer1K': 0.009,
        'contextK': 128
    },
    'command-r-plus': {
        'provider': 'Cohere',
        'label': 'command-r+',
        'inPricePer1K': 0.003,
        'outPricePer1K': 0.015,
        'contextK': 128
    },
}

# Model ID mappings for litellm compatibility
LITELLM_MODEL_MAPPINGS = {
    'gemini-1.5-pro': 'gemini/gemini-1.5-pro-latest',
    'gemini-1.5-flash': 'gemini/gemini-1.5-flash-latest',
    'llama-3.1-70b-instruct': 'meta-llama/Llama-3.1-70b-instruct',
    'llama-3.1-8b-instruct': 'meta-llama/Llama-3.1-8b-instruct',
    'mistral-large-2407': 'mistral/mistral-large-latest',
}

# Council member defaults
DEFAULT_COUNCIL_MEMBERS = [
    {
        "role": "pm",
        "provider": "openai",
        "model": "gpt-4o",
        "expertise": ["business_logic", "user_needs"]
    },
    {
        "role": "security",
        "provider": "anthropic", 
        "model": "claude-3-5-sonnet-20241022",
        "expertise": ["threat_modeling", "compliance"]
    },
    {
        "role": "data_eval",
        "provider": "google",
        "model": "gemini-1.5-pro",
        "expertise": ["analytics", "evaluation"]
    },
    {
        "role": "infrastructure",
        "provider": "openrouter",
        "model": "x-ai/grok-2-1212",
        "expertise": ["scalability", "architecture"]
    },
]

# Environment variable names
ENV_VARS = {
    "OPENAI_API_KEY": "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
    "AUDIT_MAX_SECONDS": "AUDIT_MAX_SECONDS",
}
