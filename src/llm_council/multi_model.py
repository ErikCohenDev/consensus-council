"""Multi-model client for LLM operations."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class MultiModelClient:
    """Mock multi-model client for testing."""
    
    def __init__(self):
        pass
    
    async def call_model(
        self,
        model: str,
        messages: List[Dict[str, str]],
        response_format: str = "text"
    ) -> Dict[str, Any]:
        """Mock model call for testing."""
        
        # Return mock responses based on model
        if "gpt-4o" in model:
            if response_format == "json":
                return {
                    "answer": "Mock GPT-4o answer",
                    "confidence": 0.85,
                    "reasoning": "Mock reasoning from GPT-4o"
                }
            else:
                return {"content": "Mock GPT-4o response"}
        
        elif "claude" in model:
            if response_format == "json":
                return {
                    "answer": "Mock Claude answer",
                    "confidence": 0.80,
                    "reasoning": "Mock careful Claude analysis"
                }
            else:
                return {"content": "Mock Claude response"}
        
        elif "gemini" in model:
            if response_format == "json":
                return {
                    "answer": "Mock Gemini answer", 
                    "confidence": 0.75,
                    "reasoning": "Mock Gemini technical analysis"
                }
            else:
                return {"content": "Mock Gemini response"}
        
        else:
            return {"content": "Mock response from unknown model"}
