"""
Tests for consensus engine logic.

VERIFIES: REQ-003, REQ-004 (consensus algorithm, quality gates)
VALIDATES: Trimmed mean calculation and agreement detection
USE_CASE: UC-003, UC-004 (consensus building, human review triggers)
INTERFACES: consensus.py (ConsensusEngine, trimmed_mean, agreement_level)
LAST_SYNC: 2025-08-30
"""
import pytest
from llm_council.consensus import (
    ConsensusEngine,
    ConsensusResult,
    calculate_trimmed_mean,
    calculate_agreement_level
)
from llm_council.schemas import AuditorResponse


class TestTrimmedMean:
    """Test trimmed mean calculation."""

    def test_trimmed_mean_basic(self):
        """
        Test basic trimmed mean calculation.
        
        VERIFIES: REQ-003 (consensus algorithm implementation)
        VALIDATES: Trimmed mean removes outliers correctly
        """
        scores = [1, 2, 3, 4, 5]
        result = calculate_trimmed_mean(scores, trim_percentage=0.2)
        # Should remove 1 and 5, leaving [2, 3, 4], average = 3.0
        assert result == 3.0

    def test_trimmed_mean_no_trim_needed(self):
        """Test trimmed mean when no trimming is needed (small dataset)."""
        scores = [3, 4, 3]
        result = calculate_trimmed_mean(scores, trim_percentage=0.2)
        # Not enough data to trim, should return regular mean
        assert abs(result - 3.33) < 0.01

    def test_trimmed_mean_identical_scores(self):
        """Test trimmed mean with identical scores."""
        scores = [4, 4, 4, 4, 4]
        result = calculate_trimmed_mean(scores, trim_percentage=0.2)
        assert result == 4.0

    def test_trimmed_mean_empty_list(self):
        """Test trimmed mean with empty list raises error."""
        with pytest.raises(ValueError):
            calculate_trimmed_mean([], trim_percentage=0.1)


class TestAgreementLevel:
    """Test agreement level calculation."""

    def test_agreement_level_high(self):
        """
        Test high agreement (low variance).
        
        VERIFIES: REQ-004 (agreement threshold detection)
        VALIDATES: High consensus detection with low score variance
        """
        scores = [4.0, 4.1, 3.9, 4.0]
        agreement = calculate_agreement_level(scores)
        assert agreement > 0.9  # Should be high agreement

    def test_agreement_level_low(self):
        """Test low agreement (high variance)."""
        scores = [1.0, 5.0, 2.0, 4.0]
        agreement = calculate_agreement_level(scores)
        assert agreement < 0.5  # Should be low agreement

    def test_agreement_level_perfect(self):
        """Test perfect agreement (identical scores)."""
        scores = [4.0, 4.0, 4.0, 4.0]
        agreement = calculate_agreement_level(scores)
        assert agreement == 1.0  # Perfect agreement


class TestConsensusEngine:
    """Test consensus engine integration."""

    def test_consensus_pass_high_agreement(self):
        """
        Test consensus passes with high scores and agreement.
        
        VERIFIES: REQ-003, REQ-004 (quality gate pass conditions)
        VALIDATES: Consensus engine approval logic
        USE_CASE: UC-003 (successful document promotion)
        """
        engine = ConsensusEngine(
            score_threshold=3.8,
            approval_threshold=0.67,
            trim_percentage=0.1
        )

        # Mock auditor responses with high scores
        responses = self._create_mock_responses([
            {"role": "pm", "scores": [4, 4, 4, 4, 4, 4]},
            {"role": "ux", "scores": [4, 4, 5, 4, 4, 4]},
            {"role": "security", "scores": [4, 3, 4, 4, 4, 5]}
        ])

        result = engine.calculate_consensus(responses)

        assert result.consensus_pass is True
        assert result.approval_pass is True
        assert result.final_decision == "PASS"
        assert result.weighted_average >= 3.8

    def test_consensus_fail_low_scores(self):
        """
        Test consensus fails with low average scores.
        
        VERIFIES: REQ-004 (quality gate fail conditions)
        VALIDATES: Document rejection with insufficient scores
        USE_CASE: UC-004 (document revision required)
        """
        engine = ConsensusEngine(
            score_threshold=3.8,
            approval_threshold=0.67,
            trim_percentage=0.1
        )

        # Mock auditor responses with low scores
        responses = self._create_mock_responses([
            {"role": "pm", "scores": [3, 3, 3, 3, 3, 3]},
            {"role": "ux", "scores": [2, 3, 3, 3, 3, 3]},
            {"role": "security", "scores": [3, 2, 3, 3, 3, 3]}
        ])

        result = engine.calculate_consensus(responses)

        assert result.consensus_pass is False
        assert result.final_decision == "FAIL"
        assert result.weighted_average < 3.8

    def test_consensus_fail_low_approvals(self):
        """Test consensus fails with good scores but low approval percentage."""
        engine = ConsensusEngine(
            score_threshold=3.8,
            approval_threshold=0.67,  # Need 67% approvals
            trim_percentage=0.1
        )

        # Mock responses where scores are high but most auditors don't approve
        responses = self._create_mock_responses([
            {"role": "pm", "scores": [4, 4, 4, 4, 4, 4], "overall_pass": True},
            {"role": "ux", "scores": [4, 4, 4, 4, 4, 4], "overall_pass": False},  # Fails due to blocking issues
            {"role": "security", "scores": [4, 4, 4, 4, 4, 4], "overall_pass": False}  # Fails due to blocking issues
        ])

        result = engine.calculate_consensus(responses)

        assert result.consensus_pass is True  # Scores are good
        assert result.approval_pass is False  # Only 1/3 approved (33% < 67%)
        assert result.final_decision == "FAIL"

    def test_blocking_issues_prevent_pass(self):
        """
        Test that critical blocking issues prevent consensus pass.
        
        VERIFIES: REQ-006 (blocking issue severity gates)
        VALIDATES: Critical issue override of score-based approval
        USE_CASE: UC-004 (security/compliance blockers)
        """
        engine = ConsensusEngine(
            score_threshold=3.8,
            approval_threshold=0.67,
            trim_percentage=0.1,
            blocking_gates={"critical": 0, "high": 2}
        )

        # High scores but critical blocking issue
        responses = self._create_mock_responses([
            {"role": "pm", "scores": [4, 4, 4, 4, 4, 4], "overall_pass": True},
            {"role": "security", "scores": [4, 4, 4, 4, 4, 4], "overall_pass": True,
             "blocking_issues": [{"severity": "critical", "description": "Security vulnerability"}]}
        ])

        result = engine.calculate_consensus(responses)

        assert result.final_decision == "FAIL"
        assert "critical" in str(result.failure_reasons)

    def test_disagreement_detection(self):
        """
        Test detection of high disagreement between auditors.
        
        VERIFIES: REQ-005 (human review trigger conditions)
        VALIDATES: Disagreement threshold detection for human intervention
        USE_CASE: UC-004 (human review required for deadlock)
        """
        engine = ConsensusEngine(
            score_threshold=3.8,
            approval_threshold=0.67,
            trim_percentage=0.1,
            disagreement_threshold=1.0
        )

        # High disagreement in scores
        responses = self._create_mock_responses([
            {"role": "pm", "scores": [5, 5, 5, 5, 5, 5]},   # Very high
            {"role": "ux", "scores": [2, 2, 2, 2, 2, 2]},   # Very low
            {"role": "security", "scores": [4, 4, 4, 4, 4, 4]}  # Medium
        ])

        result = engine.calculate_consensus(responses)

        assert result.requires_human_review is True
        assert any("disagreement" in reason.lower() for reason in result.failure_reasons)

    def _create_mock_responses(self, response_configs):
        """Helper to create mock auditor responses."""
        responses = []
        for config in response_configs:
            # Create dimension scores from the scores array
            dimension_names = ["simplicity", "conciseness", "actionability",
                             "readability", "options_tradeoffs", "evidence_specificity"]
            scores_detailed = {}

            for i, dim in enumerate(dimension_names):
                scores_detailed[dim] = {
                    "score": config["scores"][i],
                    "pass": config["scores"][i] >= 3.0,
                    "justification": f"This dimension scored {config['scores'][i]} based on evaluation criteria",
                    "improvements": ["Consider improvements"]
                }

            avg_score = sum(config["scores"]) / len(config["scores"])
            overall_pass = config.get("overall_pass", avg_score >= 3.8 and min(config["scores"]) >= 3.0)

            response_data = {
                "auditor_role": config["role"],
                "document_analyzed": "vision",
                "audit_timestamp": "2025-08-29T12:00:00Z",
                "scores_detailed": scores_detailed,
                "overall_assessment": {
                    "average_score": avg_score,
                    "overall_pass": overall_pass,
                    "summary": f"Assessment from {config['role']} auditor with average score {avg_score}",
                    "top_strengths": ["Good structure"],
                    "top_risks": ["Some risks"],
                    "quick_wins": ["Quick improvements"]
                },
                "blocking_issues": config.get("blocking_issues", []),
                "alignment_feedback": {
                    "upstream_consistency": {"score": 4, "issues": [], "suggestions": []},
                    "internal_consistency": {"score": 4, "issues": [], "suggestions": []}
                },
                "confidence_level": 4
            }

            responses.append(response_data)

        return responses


class TestConsensusResult:
    """Test consensus result data structure."""

    def test_consensus_result_creation(self):
        """Test that consensus results are created correctly."""
        result = ConsensusResult(
            weighted_average=3.85,
            consensus_pass=True,
            approval_pass=True,
            final_decision="PASS",
            agreement_level=0.85,
            participating_auditors=["pm", "ux", "security"],
            failure_reasons=[],
            requires_human_review=False
        )

        assert result.weighted_average == 3.85
        assert result.final_decision == "PASS"
        assert len(result.participating_auditors) == 3
        assert result.requires_human_review is False
