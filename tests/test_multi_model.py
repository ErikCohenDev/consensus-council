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
    
    @patch('llm_council.multi_model.OpenAI')
    @patch('llm_council.multi_model.Anthropic') 
    @patch('llm_council.multi_model.genai')
    async def test_ensemble_auditor_execution(self, mock_genai, mock_anthropic, mock_openai, temp_dir):
        """Test that different models can audit the same document with diverse perspectives."""
        
        # Configure ensemble with different models for different roles
        model_configs = [
            ModelConfig("openai", "gpt-4o", "openai-key", "pm"),
            ModelConfig("anthropic", "claude-3-5-sonnet-20241022", "claude-key", "security"),
            ModelConfig("google", "gemini-1.5-pro", "gemini-key", "data_eval")
        ]
        
        orchestrator = MultiModelOrchestrator(model_configs)
        
        document_content = """# Vision
        Build an AI-powered document review platform using multiple LLM auditors.
        Target cost: $2 per analysis with caching enabled.
        """
        
        # Mock responses from different models with different perspectives
        mock_openai_response = {
            "auditor_role": "pm",
            "overall_assessment": {
                "summary": "Strong business case but needs clearer success metrics",
                "top_risks": ["Market validation", "User adoption"],
                "quick_wins": ["Add beta user targets", "Define retention metrics"]
            }
        }
        
        mock_claude_response = {
            "auditor_role": "security", 
            "overall_assessment": {
                "summary": "Security considerations need more detail",
                "top_risks": ["API key exposure", "Data privacy"],
                "quick_wins": ["Add security section", "Define data handling"]
            }
        }
        
        mock_gemini_response = {
            "auditor_role": "data_eval",
            "overall_assessment": {
                "summary": "Need evaluation framework for multi-model consensus",
                "top_risks": ["Model bias", "Consensus validity"],
                "quick_wins": ["Add eval metrics", "Define ground truth"]
            }
        }
        
        # Set up mock clients
        mock_openai_client = AsyncMock()
        mock_openai.return_value = mock_openai_client
        mock_openai_client.chat.completions.create.return_value.choices = [
            Mock(message=Mock(content=str(mock_openai_response).replace("'", '"')))
        ]
        
        mock_claude_client = AsyncMock()
        mock_anthropic.return_value = mock_claude_client
        mock_claude_client.messages.create.return_value.content = [
            Mock(text=str(mock_claude_response).replace("'", '"'))
        ]
        
        mock_gemini_client = AsyncMock()
        mock_genai.GenerativeModel.return_value = mock_gemini_client
        mock_gemini_client.generate_content.return_value.text = str(mock_gemini_response).replace("'", '"')
        
        # Execute ensemble audit
        result = await orchestrator.execute_ensemble_audit("vision", document_content)
        
        # Verify all models were called
        assert len(result.model_responses) == 3
        
        # Verify diverse perspectives captured
        roles = [resp["auditor_role"] for resp in result.model_responses]
        assert "pm" in roles
        assert "security" in roles  
        assert "data_eval" in roles
        
        # Verify consensus includes all perspectives
        assert result.consensus_result is not None
        assert len(result.consensus_result.participating_auditors) == 3


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
        assert diversity_score >= 0.7  # High diversity = good ensemble
        
        # Should identify unique insights per model
        unique_insights = diversity_score.unique_insights_per_model
        assert len(unique_insights) == 3
        assert "Market risk" in unique_insights["openai"]
        assert "API security" in unique_insights["anthropic"] 
        assert "Model bias" in unique_insights["google"]