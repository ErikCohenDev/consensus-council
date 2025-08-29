"""Multi-model ensemble orchestration for diverse LLM perspectives.

Uses LiteLLM for unified access to OpenAI, Anthropic, Google, OpenRouter (Grok)
and other providers. Enables different models per auditor role to maximize
perspective diversity and cross-model consensus building.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

try:
    import litellm
    from litellm import acompletion
except ImportError:
    litellm = None
    acompletion = None


class ProviderType(Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    GOOGLE = "google"
    OPENROUTER = "openrouter"


@dataclass
class ModelConfig:
    """Configuration for a specific model in the ensemble."""
    provider: str
    model: str
    api_key: str
    role: str
    temperature: float = 0.2
    max_tokens: int = 4000


@dataclass
class ModelResponse:
    """Response from a single model in the ensemble."""
    auditor_role: str
    model_provider: str
    model_name: str
    response_data: Dict[str, Any]
    execution_time: float
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


@dataclass
class EnsembleResult:
    """Result from multi-model ensemble execution."""
    model_responses: List[ModelResponse]
    consensus_result: Optional[Any]
    perspective_diversity_score: float
    cross_model_insights: Dict[str, List[str]]
    execution_time: float


@dataclass
class PerspectiveDiversityAnalysis:
    """Analysis of how much perspective diversity exists across models."""
    diversity_score: float  # 0-1, higher = more diverse
    unique_insights_per_model: Dict[str, List[str]]
    consensus_areas: List[str]
    disagreement_areas: List[str]


class UniversalModelProvider:
    """Universal LLM provider using LiteLLM for all major providers."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        if litellm is None:
            raise ImportError("litellm package required for multi-model support")
        
        # Set up provider-specific API keys in environment for LiteLLM
        self._setup_api_keys()
    
    def _setup_api_keys(self):
        """Configure API keys for LiteLLM based on provider."""
        # LiteLLM expects specific environment variable names
        if self.config.provider == "openai":
            os.environ["OPENAI_API_KEY"] = self.config.api_key
        elif self.config.provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = self.config.api_key
        elif self.config.provider == "google":
            os.environ["GOOGLE_API_KEY"] = self.config.api_key
        elif self.config.provider == "openrouter":
            os.environ["OPENROUTER_API_KEY"] = self.config.api_key
    
    async def execute_audit(self, prompt: str) -> Dict[str, Any]:
        """Execute audit using LiteLLM unified interface."""
        # LiteLLM model format: provider/model-name
        model_name = f"{self.config.provider}/{self.config.model}"
        if self.config.provider == "openrouter":
            model_name = self.config.model  # OpenRouter models use full path
        
        try:
            response = await acompletion(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert {self.config.role} auditor. Return ONLY valid JSON conforming to the schema."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            content = response.choices[0].message.content if response.choices else "{}"
            data = json.loads(content)
            
            # Add model metadata
            data["model_provider"] = self.config.provider
            data["model_name"] = self.config.model
            data["auditor_role"] = self.config.role
            
            return data
            
        except Exception as e:
            # Return error response that matches expected schema
            return {
                "auditor_role": self.config.role,
                "model_provider": self.config.provider,
                "model_name": self.config.model,
                "error": str(e),
                "overall_assessment": {
                    "summary": f"Model {self.config.model} failed: {str(e)}",
                    "overall_pass": False,
                    "average_score": 0.0,
                    "top_risks": [f"Model execution failed: {str(e)}"],
                    "quick_wins": []
                }
            }


class MultiModelOrchestrator:
    """Orchestrates multiple LLM providers for diverse perspective analysis."""
    
    def __init__(self, model_configs: List[ModelConfig]):
        self.model_configs = model_configs
        self._providers = self._initialize_providers()
    
    def _initialize_providers(self) -> Dict[str, UniversalModelProvider]:
        """Initialize universal provider instances using LiteLLM."""
        providers = {}
        
        for config in self.model_configs:
            providers[config.role] = UniversalModelProvider(config)
        
        return providers
    
    async def execute_ensemble_audit(self, stage: str, document_content: str) -> EnsembleResult:
        """Execute audit across all configured models and analyze perspective diversity."""
        import time
        start_time = time.perf_counter()
        
        # Execute all models in parallel
        tasks = []
        for role, provider in self._providers.items():
            # Build role-specific prompt (simplified for MVP)
            prompt = f"""Audit this {stage} document from a {role} perspective:

{document_content}

Return structured JSON with your analysis focusing on {role}-specific concerns."""
            
            tasks.append(self._execute_single_model(provider, prompt))
        
        model_responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful responses
        successful_responses = [r for r in model_responses if isinstance(r, ModelResponse)]
        
        # Analyze perspective diversity
        diversity_analysis = analyze_perspective_diversity([r.response_data for r in successful_responses])
        
        execution_time = time.perf_counter() - start_time
        
        return EnsembleResult(
            model_responses=successful_responses,
            consensus_result=None,  # Will integrate with existing consensus engine
            perspective_diversity_score=diversity_analysis.diversity_score,
            cross_model_insights=diversity_analysis.unique_insights_per_model,
            execution_time=execution_time
        )
    
    async def _execute_single_model(self, provider: UniversalModelProvider, prompt: str) -> ModelResponse:
        """Execute audit with a single model provider."""
        import time
        start_time = time.perf_counter()
        
        try:
            response_data = await provider.execute_audit(prompt)
            execution_time = time.perf_counter() - start_time
            
            return ModelResponse(
                auditor_role=provider.config.role,
                model_provider=provider.config.provider,
                model_name=provider.config.model,
                response_data=response_data,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            # Return error response
            return ModelResponse(
                auditor_role=provider.config.role,
                model_provider=provider.config.provider,
                model_name=provider.config.model,
                response_data={"error": str(e), "auditor_role": provider.config.role},
                execution_time=execution_time
            )


def analyze_perspective_diversity(responses: List[Dict[str, Any]]) -> PerspectiveDiversityAnalysis:
    """Analyze how much perspective diversity exists across model responses."""
    
    # Extract insights from each model
    model_insights = {}
    all_insights = set()
    
    for response in responses:
        provider = response.get("model_provider", "unknown")
        
        # Extract key insights (risks, wins, feedback)
        insights = []
        overall = response.get("overall_assessment", {})
        
        risks = overall.get("top_risks", [])
        wins = overall.get("quick_wins", [])
        
        insights.extend(risks)
        insights.extend(wins)
        
        model_insights[provider] = insights
        all_insights.update(insights)
    
    # Calculate diversity score based on unique insights per model
    if not model_insights or not all_insights:
        return PerspectiveDiversityAnalysis(
            diversity_score=0.0,
            unique_insights_per_model={},
            consensus_areas=[],
            disagreement_areas=[]
        )
    
    # Find unique insights per model
    unique_per_model = {}
    consensus_insights = []
    
    for provider, insights in model_insights.items():
        unique_insights = []
        for insight in insights:
            # Check if this insight is unique to this model
            other_models_insights = []
            for other_provider, other_insights in model_insights.items():
                if other_provider != provider:
                    other_models_insights.extend(other_insights)
            
            if insight not in other_models_insights:
                unique_insights.append(insight)
            else:
                if insight not in consensus_insights:
                    consensus_insights.append(insight)
        
        unique_per_model[provider] = unique_insights
    
    # Calculate diversity score (higher = more diverse perspectives)
    total_unique = sum(len(insights) for insights in unique_per_model.values())
    total_insights = len(all_insights)
    
    diversity_score = total_unique / total_insights if total_insights > 0 else 0.0
    
    return PerspectiveDiversityAnalysis(
        diversity_score=diversity_score,
        unique_insights_per_model=unique_per_model,
        consensus_areas=consensus_insights,
        disagreement_areas=list(all_insights - set(consensus_insights))
    )


__all__ = [
    "ModelConfig", 
    "UniversalModelProvider",
    "MultiModelOrchestrator", 
    "EnsembleResult",
    "analyze_perspective_diversity",
    "PerspectiveDiversityAnalysis"
]