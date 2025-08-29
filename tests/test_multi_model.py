"""Tests for multi-model ensemble functionality."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import yaml

from llm_council.multi_model import UniversalModelProvider, MultiModelOrchestrator, ModelConfig


class TestModelProvider:
    """Test different model provider integrations."""
    
    def test_openai_provider_config(self):
        """Test OpenAI provider configuration."""
        config = ModelConfig(
            provider="openai",
            model="gpt-4o", 
            api_key="test-key",
            role="pm"
        )
        
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.role == "pm"
    
    def test_claude_provider_config(self):
        """Test Claude provider configuration."""
        config = ModelConfig(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            api_key="test-key", 
            role="security"
        )
        
        assert config.provider == "anthropic"
        assert config.model == "claude-3-5-sonnet-20241022"
        assert config.role == "security"
    
    def test_gemini_provider_config(self):
        """Test Gemini provider configuration.""" 
        config = ModelConfig(
            provider="google",
            model="gemini-1.5-pro",
            api_key="test-key",
            role="data_eval"
        )
        
        assert config.provider == "google"
        assert config.model == "gemini-1.5-pro"


class TestMultiModelOrchestrator:
    """Test multi-model ensemble orchestration."""
    
    @pytest.mark.asyncio
    @patch('llm_council.multi_model.acompletion')
    async def test_ensemble_auditor_execution(self, mock_completion, temp_dir):
        """Test that different models can audit the same document with diverse perspectives."""
        
        # Configure ensemble with different models for different roles
        model_configs = [
            ModelConfig("openai", "gpt-4o", "openai-key", "pm"),
            ModelConfig("anthropic", "claude-3-5-sonnet-20241022", "claude-key", "security"),
        ]
        
        orchestrator = MultiModelOrchestrator(model_configs)
        
        document_content = """# Vision
        Build an AI-powered document review platform using multiple LLM auditors.
        """
        
        # Mock LiteLLM responses
        mock_responses = [
            Mock(choices=[Mock(message=Mock(content='{"auditor_role": "pm", "model_provider": "openai", "overall_assessment": {"summary": "Strong vision"}}'))]),
            Mock(choices=[Mock(message=Mock(content='{"auditor_role": "security", "model_provider": "anthropic", "overall_assessment": {"summary": "Needs security details"}}'))])
        ]
        
        mock_completion.side_effect = mock_responses
        
        # Execute ensemble audit
        result = await orchestrator.execute_ensemble_audit("vision", document_content)
        
        # Verify models were called
        assert len(result.model_responses) >= 1
        assert result.execution_time > 0


class TestModelDiversityAnalysis:
    """Test analysis of model diversity and perspective differences."""
    
    def test_perspective_diversity_scoring(self):
        """Test that we can measure how much models disagree/agree."""
        from llm_council.multi_model import analyze_perspective_diversity
        
        responses = [
            {
                "auditor_role": "pm",
                "model_provider": "openai",
                "overall_assessment": {"top_risks": ["Market risk", "User adoption"]}
            },
            {
                "auditor_role": "security", 
                "model_provider": "anthropic",
                "overall_assessment": {"top_risks": ["API security", "Data privacy"]}
            },
            {
                "auditor_role": "data_eval",
                "model_provider": "google", 
                "overall_assessment": {"top_risks": ["Model bias", "Evaluation metrics"]}
            }
        ]
        
        diversity_score = analyze_perspective_diversity(responses)
        
        # Should detect high diversity (different risks from each model)
        assert diversity_score.diversity_score >= 0.7  # High diversity = good ensemble
        
        # Should identify unique insights per model
        unique_insights = diversity_score.unique_insights_per_model
        assert len(unique_insights) == 3
        assert "Market risk" in unique_insights["openai"]
        assert "API security" in unique_insights["anthropic"] 
        assert "Model bias" in unique_insights["google"]