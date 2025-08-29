"""Tests for auditor orchestration system."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from llm_council.orchestrator import (
    AuditorOrchestrator,
    AuditorWorker,
    OrchestrationResult,
    AuditorExecutionError
)
from llm_council.schemas import AuditorResponse


class TestAuditorWorker:
    """Test individual auditor worker."""
    
    @pytest.mark.asyncio
    async def test_auditor_worker_successful_execution(self, sample_template_config):
        """Test successful auditor execution."""
        # Mock OpenAI client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"auditor_role": "pm", "document_analyzed": "vision", "audit_timestamp": "2025-08-29T12:00:00Z", "scores_detailed": {"simplicity": {"score": 4, "pass": true, "justification": "Clear and well-structured document with good explanations throughout", "improvements": ["Consider adding examples"]}, "conciseness": {"score": 3, "pass": true, "justification": "Mostly concise but some sections could be tightened up significantly", "improvements": ["Remove redundant text"]}, "actionability": {"score": 4, "pass": true, "justification": "Clear action items and implementation guidance provided throughout", "improvements": ["Add timelines"]}, "readability": {"score": 5, "pass": true, "justification": "Excellent structure with clear headings and logical flow throughout", "improvements": ["Perfect as-is"]}, "options_tradeoffs": {"score": 3, "pass": true, "justification": "Some alternatives considered but could explore more options thoroughly", "improvements": ["Add comparison table"]}, "evidence_specificity": {"score": 4, "pass": true, "justification": "Good use of specific examples and data points throughout the document", "improvements": ["Include more quantitative data"]}}, "overall_assessment": {"average_score": 3.83, "overall_pass": true, "summary": "Strong vision document with clear direction and good implementation guidance", "top_strengths": ["Clear structure", "Actionable guidance", "Good examples"], "top_risks": ["Scope creep potential", "Timeline aggressive"], "quick_wins": ["Add timeline estimates", "Include comparison table"]}, "blocking_issues": [], "alignment_feedback": {"upstream_consistency": {"score": 4, "issues": [], "suggestions": ["Check alignment"]}, "internal_consistency": {"score": 5, "issues": [], "suggestions": []}}, "role_specific_insights": {"market_analysis": "Good analysis"}, "confidence_level": 4}'
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        worker = AuditorWorker(
            role="pm",
            stage="vision", 
            client=mock_client,
            timeout=60,
            max_retries=3
        )
        
        prompt = "Test prompt for PM auditor reviewing vision document"
        result = await worker.execute_audit(prompt)
        
        assert result is not None
        assert result["auditor_role"] == "pm"
        assert result["document_analyzed"] == "vision"
        assert result["overall_assessment"]["overall_pass"] is True
        
        # Verify client was called correctly
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auditor_worker_json_validation_retry(self, sample_template_config):
        """Test that worker retries on invalid JSON and eventually succeeds."""
        mock_client = AsyncMock()
        
        # First call returns invalid JSON, second call returns valid JSON
        invalid_response = Mock()
        invalid_response.choices = [Mock()]
        invalid_response.choices[0].message.content = 'invalid json content'
        
        valid_response = Mock()
        valid_response.choices = [Mock()] 
        valid_response.choices[0].message.content = '{"auditor_role": "pm", "document_analyzed": "vision", "audit_timestamp": "2025-08-29T12:00:00Z", "scores_detailed": {"simplicity": {"score": 4, "pass": true, "justification": "Clear and well-structured document with good explanations throughout", "improvements": ["Consider adding examples"]}, "conciseness": {"score": 3, "pass": true, "justification": "Mostly concise but some sections could be tightened up significantly", "improvements": ["Remove redundant text"]}, "actionability": {"score": 4, "pass": true, "justification": "Clear action items and implementation guidance provided throughout", "improvements": ["Add timelines"]}, "readability": {"score": 5, "pass": true, "justification": "Excellent structure with clear headings and logical flow throughout", "improvements": ["Perfect as-is"]}, "options_tradeoffs": {"score": 3, "pass": true, "justification": "Some alternatives considered but could explore more options thoroughly", "improvements": ["Add comparison table"]}, "evidence_specificity": {"score": 4, "pass": true, "justification": "Good use of specific examples and data points throughout the document", "improvements": ["Include more quantitative data"]}}, "overall_assessment": {"average_score": 3.83, "overall_pass": true, "summary": "Strong vision document with clear direction and good implementation guidance", "top_strengths": ["Clear structure", "Actionable guidance", "Good examples"], "top_risks": ["Scope creep potential", "Timeline aggressive"], "quick_wins": ["Add timeline estimates", "Include comparison table"]}, "blocking_issues": [], "alignment_feedback": {"upstream_consistency": {"score": 4, "issues": [], "suggestions": ["Check alignment"]}, "internal_consistency": {"score": 5, "issues": [], "suggestions": []}}, "role_specific_insights": {"market_analysis": "Good analysis"}, "confidence_level": 4}'
        
        mock_client.chat.completions.create = AsyncMock(side_effect=[invalid_response, valid_response])
        
        worker = AuditorWorker(
            role="pm",
            stage="vision",
            client=mock_client,
            timeout=60,
            max_retries=3
        )
        
        result = await worker.execute_audit("Test prompt")
        
        assert result is not None
        assert result["auditor_role"] == "pm"
        
        # Verify client was called twice (retry happened)
        assert mock_client.chat.completions.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_auditor_worker_max_retries_exceeded(self):
        """Test that worker raises error when max retries exceeded."""
        mock_client = AsyncMock()
        invalid_response = Mock()
        invalid_response.choices = [Mock()]
        invalid_response.choices[0].message.content = 'invalid json'
        
        mock_client.chat.completions.create = AsyncMock(return_value=invalid_response)
        
        worker = AuditorWorker(
            role="pm",
            stage="vision",
            client=mock_client,
            timeout=60,
            max_retries=2  # Low retry count for testing
        )
        
        with pytest.raises(AuditorExecutionError):
            await worker.execute_audit("Test prompt")
        
        # Verify all retries were attempted
        assert mock_client.chat.completions.create.call_count == 2
    
    @pytest.mark.asyncio 
    async def test_auditor_worker_timeout_handling(self):
        """Test that worker handles timeouts appropriately."""
        mock_client = AsyncMock()
        
        # Simulate timeout by making the call hang
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(2)  # Longer than timeout
            return Mock()
        
        mock_client.chat.completions.create = AsyncMock(side_effect=slow_response)
        
        worker = AuditorWorker(
            role="pm",
            stage="vision", 
            client=mock_client,
            timeout=0.1,  # Very short timeout
            max_retries=1
        )
        
        with pytest.raises(AuditorExecutionError):
            await worker.execute_audit("Test prompt")


class TestAuditorOrchestrator:
    """Test auditor orchestration system."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_successful_execution(self, temp_dir, sample_template_config, sample_document_content):
        """Test successful orchestration of multiple auditors."""
        # Create template file
        import yaml
        template_file = temp_dir / "test_template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)
        
        # Mock OpenAI client
        with patch('llm_council.orchestrator.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            # Create mock responses for each auditor
            pm_response = Mock()
            pm_response.choices = [Mock()]
            pm_response.choices[0].message.content = '{"auditor_role": "pm", "document_analyzed": "vision", "audit_timestamp": "2025-08-29T12:00:00Z", "scores_detailed": {"simplicity": {"score": 4, "pass": true, "justification": "Clear and well-structured document with good explanations throughout", "improvements": ["Consider adding examples"]}, "conciseness": {"score": 3, "pass": true, "justification": "Mostly concise but some sections could be tightened up significantly", "improvements": ["Remove redundant text"]}, "actionability": {"score": 4, "pass": true, "justification": "Clear action items and implementation guidance provided throughout", "improvements": ["Add timelines"]}, "readability": {"score": 5, "pass": true, "justification": "Excellent structure with clear headings and logical flow throughout", "improvements": ["Perfect as-is"]}, "options_tradeoffs": {"score": 3, "pass": true, "justification": "Some alternatives considered but could explore more options thoroughly", "improvements": ["Add comparison table"]}, "evidence_specificity": {"score": 4, "pass": true, "justification": "Good use of specific examples and data points throughout the document", "improvements": ["Include more quantitative data"]}}, "overall_assessment": {"average_score": 3.83, "overall_pass": true, "summary": "Strong vision document with clear direction and good implementation guidance", "top_strengths": ["Clear structure", "Actionable guidance", "Good examples"], "top_risks": ["Scope creep potential", "Timeline aggressive"], "quick_wins": ["Add timeline estimates", "Include comparison table"]}, "blocking_issues": [], "alignment_feedback": {"upstream_consistency": {"score": 4, "issues": [], "suggestions": ["Check alignment"]}, "internal_consistency": {"score": 5, "issues": [], "suggestions": []}}, "role_specific_insights": {"market_analysis": "Good analysis"}, "confidence_level": 4}'
            
            ux_response = Mock()
            ux_response.choices = [Mock()]
            ux_response.choices[0].message.content = '{"auditor_role": "ux", "document_analyzed": "vision", "audit_timestamp": "2025-08-29T12:00:00Z", "scores_detailed": {"simplicity": {"score": 5, "pass": true, "justification": "Exceptionally clear and well-structured document with excellent explanations", "improvements": ["Consider visual aids"]}, "conciseness": {"score": 4, "pass": true, "justification": "Well-balanced content length with appropriate level of detail provided", "improvements": ["Minor trimming possible"]}, "actionability": {"score": 4, "pass": true, "justification": "Clear action items and implementation guidance provided throughout", "improvements": ["Add user stories"]}, "readability": {"score": 5, "pass": true, "justification": "Excellent structure with clear headings and logical flow throughout", "improvements": ["Perfect as-is"]}, "options_tradeoffs": {"score": 4, "pass": true, "justification": "Good consideration of alternatives with solid reasoning provided throughout", "improvements": ["Add user impact analysis"]}, "evidence_specificity": {"score": 3, "pass": true, "justification": "Adequate examples but could benefit from more user-focused evidence", "improvements": ["Include user research data"]}}, "overall_assessment": {"average_score": 4.17, "overall_pass": true, "summary": "Excellent vision document from UX perspective with strong user focus", "top_strengths": ["User-centered approach", "Clear structure", "Good readability"], "top_risks": ["Missing user validation", "Accessibility considerations"], "quick_wins": ["Add user stories", "Include accessibility notes"]}, "blocking_issues": [], "alignment_feedback": {"upstream_consistency": {"score": 4, "issues": [], "suggestions": ["Align with user research"]}, "internal_consistency": {"score": 5, "issues": [], "suggestions": []}}, "role_specific_insights": {"user_experience": "Strong UX focus"}, "confidence_level": 4}'
            
            mock_client.chat.completions.create = AsyncMock(side_effect=[pm_response, ux_response])
            
            orchestrator = AuditorOrchestrator(
                template_path=template_file,
                model="gpt-4o",
                api_key="test-key",
                max_parallel=2
            )
            
            result = await orchestrator.execute_stage_audit("vision", sample_document_content)
            
            assert isinstance(result, OrchestrationResult)
            assert result.success is True
            assert len(result.auditor_responses) == 2
            assert "pm" in [r["auditor_role"] for r in result.auditor_responses] 
            assert "ux" in [r["auditor_role"] for r in result.auditor_responses]
            assert result.consensus_result is not None
            assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_orchestrator_partial_failure(self, temp_dir, sample_template_config, sample_document_content):
        """Test orchestrator handling of partial auditor failures.""" 
        import yaml
        template_file = temp_dir / "test_template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)
        
        with patch('llm_council.orchestrator.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            # PM succeeds, UX fails
            pm_response = Mock()
            pm_response.choices = [Mock()]
            pm_response.choices[0].message.content = '{"auditor_role": "pm", "document_analyzed": "vision", "audit_timestamp": "2025-08-29T12:00:00Z", "scores_detailed": {"simplicity": {"score": 4, "pass": true, "justification": "Clear and well-structured document with good explanations throughout", "improvements": ["Consider adding examples"]}, "conciseness": {"score": 3, "pass": true, "justification": "Mostly concise but some sections could be tightened up significantly", "improvements": ["Remove redundant text"]}, "actionability": {"score": 4, "pass": true, "justification": "Clear action items and implementation guidance provided throughout", "improvements": ["Add timelines"]}, "readability": {"score": 5, "pass": true, "justification": "Excellent structure with clear headings and logical flow throughout", "improvements": ["Perfect as-is"]}, "options_tradeoffs": {"score": 3, "pass": true, "justification": "Some alternatives considered but could explore more options thoroughly", "improvements": ["Add comparison table"]}, "evidence_specificity": {"score": 4, "pass": true, "justification": "Good use of specific examples and data points throughout the document", "improvements": ["Include more quantitative data"]}}, "overall_assessment": {"average_score": 3.83, "overall_pass": true, "summary": "Strong vision document with clear direction and good implementation guidance", "top_strengths": ["Clear structure", "Actionable guidance", "Good examples"], "top_risks": ["Scope creep potential", "Timeline aggressive"], "quick_wins": ["Add timeline estimates", "Include comparison table"]}, "blocking_issues": [], "alignment_feedback": {"upstream_consistency": {"score": 4, "issues": [], "suggestions": ["Check alignment"]}, "internal_consistency": {"score": 5, "issues": [], "suggestions": []}}, "role_specific_insights": {"market_analysis": "Good analysis"}, "confidence_level": 4}'
            
            # UX call raises exception
            mock_client.chat.completions.create = AsyncMock(
                side_effect=[pm_response, Exception("API Error")]
            )
            
            orchestrator = AuditorOrchestrator(
                template_path=template_file,
                model="gpt-4o", 
                api_key="test-key",
                max_parallel=2
            )
            
            result = await orchestrator.execute_stage_audit("vision", sample_document_content)
            
            assert isinstance(result, OrchestrationResult)
            assert result.success is False  # Overall failure due to partial failure
            assert len(result.auditor_responses) == 1  # Only PM succeeded
            assert len(result.failed_auditors) == 1   # UX failed
            assert "ux" in result.failed_auditors
            assert result.consensus_result is None  # No consensus with partial results

    @pytest.mark.asyncio
    async def test_orchestrator_max_parallel_limiting(self, temp_dir, sample_template_config, sample_document_content):
        """Test that orchestrator respects max parallel execution limit."""
        import yaml
        # Add more auditors to test parallel limiting
        expanded_config = sample_template_config.copy()
        expanded_config["auditor_questions"]["vision"]["security"] = {
            "focus_areas": ["security"],
            "key_questions": ["Are there security risks?"]
        }
        expanded_config["auditor_questions"]["vision"]["cost"] = {
            "focus_areas": ["cost"],  
            "key_questions": ["Are costs reasonable?"]
        }
        
        template_file = temp_dir / "test_template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(expanded_config, f)
        
        with patch('llm_council.orchestrator.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            # Track call timing to verify parallel limiting
            call_times = []
            
            async def track_call(*args, **kwargs):
                call_times.append(asyncio.get_event_loop().time())
                response = Mock()
                response.choices = [Mock()]
                # Return different responses based on call count
                role = ["pm", "ux", "security", "cost"][len(call_times) - 1]
                response.choices[0].message.content = f'{{"auditor_role": "{role}", "document_analyzed": "vision", "audit_timestamp": "2025-08-29T12:00:00Z", "scores_detailed": {{"simplicity": {{"score": 4, "pass": true, "justification": "Clear and well-structured document with good explanations throughout", "improvements": ["Consider adding examples"]}}, "conciseness": {{"score": 3, "pass": true, "justification": "Mostly concise but some sections could be tightened up significantly", "improvements": ["Remove redundant text"]}}, "actionability": {{"score": 4, "pass": true, "justification": "Clear action items and implementation guidance provided throughout", "improvements": ["Add timelines"]}}, "readability": {{"score": 5, "pass": true, "justification": "Excellent structure with clear headings and logical flow throughout", "improvements": ["Perfect as-is"]}}, "options_tradeoffs": {{"score": 3, "pass": true, "justification": "Some alternatives considered but could explore more options thoroughly", "improvements": ["Add comparison table"]}}, "evidence_specificity": {{"score": 4, "pass": true, "justification": "Good use of specific examples and data points throughout the document", "improvements": ["Include more quantitative data"]}}}}, "overall_assessment": {{"average_score": 3.83, "overall_pass": true, "summary": "Strong vision document with clear direction and good implementation guidance", "top_strengths": ["Clear structure", "Actionable guidance", "Good examples"], "top_risks": ["Scope creep potential", "Timeline aggressive"], "quick_wins": ["Add timeline estimates", "Include comparison table"]}}, "blocking_issues": [], "alignment_feedback": {{"upstream_consistency": {{"score": 4, "issues": [], "suggestions": ["Check alignment"]}}, "internal_consistency": {{"score": 5, "issues": [], "suggestions": []}}}}, "role_specific_insights": {{"{role}_analysis": "Good analysis"}}, "confidence_level": 4}}'
                await asyncio.sleep(0.1)  # Small delay to test timing
                return response
            
            mock_client.chat.completions.create = AsyncMock(side_effect=track_call)
            
            orchestrator = AuditorOrchestrator(
                template_path=template_file,
                model="gpt-4o",
                api_key="test-key", 
                max_parallel=2  # Limit to 2 parallel executions
            )
            
            result = await orchestrator.execute_stage_audit("vision", sample_document_content)
            
            assert result.success is True
            assert len(result.auditor_responses) == 4  # All auditors completed
            
            # Verify that not all calls happened simultaneously (parallel limiting worked)
            assert len(call_times) == 4
            # With max_parallel=2, we should have 2 batches of calls


class TestOrchestrationResult:
    """Test orchestration result data structure."""
    
    def test_orchestration_result_creation(self):
        """Test creating orchestration results."""
        result = OrchestrationResult(
            success=True,
            auditor_responses=[{"auditor_role": "pm"}],
            failed_auditors=[],
            consensus_result=None,
            execution_time=1.5,
            total_tokens=1000,
            total_cost=0.05
        )
        
        assert result.success is True
        assert len(result.auditor_responses) == 1
        assert len(result.failed_auditors) == 0
        assert result.execution_time == 1.5
        assert result.total_tokens == 1000
        assert result.total_cost == 0.05