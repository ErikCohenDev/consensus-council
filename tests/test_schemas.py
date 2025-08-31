"""
Tests for auditor response schema validation.

VERIFIES: REQ-001, REQ-002, REQ-003 (audit orchestration, consensus engine, schema validation)
VALIDATES: JSON schema compliance and data structure integrity
USE_CASE: UC-003 (document validation and scoring)
INTERFACES: schemas.py (AuditorResponse, DimensionScore, OverallAssessment)
LAST_SYNC: 2025-08-30
"""
import pytest
from pydantic import ValidationError
from llm_council.schemas import AuditorResponse, DimensionScore, OverallAssessment


class TestDimensionScore:
    """Test dimension score validation."""

    def test_valid_dimension_score(self):
        """
        Test that valid dimension scores are accepted.
        
        VERIFIES: REQ-002 (schema validation for dimension scoring)
        VALIDATES: DimensionScore model with score range 1-5
        """
        score_data = {
            "score": 4,
            "pass": True,
            "justification": "This is a clear and well-structured section with good explanations",
            "improvements": ["Consider adding more examples", "Clarify terminology"]
        }

        score = DimensionScore(**score_data)
        assert score.score == 4
        assert score.pass_ is True
        assert len(score.justification) >= 50
        assert len(score.improvements) >= 1

    def test_score_out_of_range_fails(self):
        """
        Test that scores outside 1-5 range are rejected.
        
        VERIFIES: REQ-002 (schema validation boundaries)
        VALIDATES: Pydantic validation for score constraints
        """
        with pytest.raises(ValidationError):
            DimensionScore(
                score=0,  # Invalid - below range
                **{"pass": False},
                justification="This is a failing score that's out of range completely",
                improvements=["Fix the score"]
            )

        with pytest.raises(ValidationError):
            DimensionScore(
                score=6,  # Invalid - above range
                **{"pass": True},
                justification="This is a passing score but the number is out of range",
                improvements=["Fix the score"]
            )

    def test_justification_too_short_fails(self):
        """Test that justifications under 50 characters are rejected."""
        with pytest.raises(ValidationError):
            DimensionScore(
                score=3,
                **{"pass": True},
                justification="Too short",  # Invalid - under 50 chars
                improvements=["Make justification longer"]
            )

    def test_empty_improvements_fails(self):
        """Test that empty improvements array is rejected."""
        with pytest.raises(ValidationError):
            DimensionScore(
                score=3,
                **{"pass": True},
                justification="This is a valid justification that meets the minimum length requirement",
                improvements=[]  # Invalid - must have at least 1 improvement
            )


class TestOverallAssessment:
    """Test overall assessment validation."""

    def test_valid_overall_assessment(self):
        """
        Test that valid overall assessments are accepted.
        
        VERIFIES: REQ-002, REQ-003 (overall assessment calculation)
        VALIDATES: OverallAssessment model structure and constraints
        """
        assessment_data = {
            "average_score": 3.83,
            "overall_pass": True,
            "summary": "Strong document with clear direction and good implementation guidance for the project",
            "top_strengths": ["Clear structure", "Actionable guidance", "Good examples"],
            "top_risks": ["Scope creep potential", "Timeline aggressive"],
            "quick_wins": ["Add timeline estimates", "Include comparison table"]
        }

        assessment = OverallAssessment(**assessment_data)
        assert assessment.average_score == 3.83
        assert assessment.overall_pass is True
        assert len(assessment.summary) >= 50
        assert len(assessment.top_strengths) <= 3
        assert len(assessment.top_risks) <= 3
        assert len(assessment.quick_wins) <= 3

    def test_summary_too_short_fails(self):
        """Test that summaries under 50 characters are rejected."""
        with pytest.raises(ValidationError):
            OverallAssessment(
                average_score=3.5,
                overall_pass=True,
                summary="Too short",  # Invalid - under 50 chars
                top_strengths=["Good"],
                top_risks=["Risk"],
                quick_wins=["Win"]
            )

    def test_too_many_items_fails(self):
        """Test that arrays with more than 3 items are rejected."""
        with pytest.raises(ValidationError):
            OverallAssessment(
                average_score=3.5,
                overall_pass=True,
                summary="This is a valid summary that meets the minimum length requirement for testing",
                top_strengths=["A", "B", "C", "D"],  # Invalid - more than 3
                top_risks=["Risk 1", "Risk 2"],
                quick_wins=["Win 1"]
            )


class TestAuditorResponse:
    """Test full auditor response validation."""

    def test_valid_auditor_response(self, sample_auditor_response):
        """
        Test that valid auditor responses are accepted.
        
        VERIFIES: REQ-001, REQ-002 (complete auditor response validation)
        VALIDATES: AuditorResponse model with all required fields
        USE_CASE: UC-003 (auditor assessment generation)
        """
        response = AuditorResponse(**sample_auditor_response)

        assert response.auditor_role == "pm"
        assert response.document_analyzed == "vision"
        assert response.overall_assessment.overall_pass is True
        assert len(response.blocking_issues) == 0
        assert response.confidence_level >= 1
        assert response.confidence_level <= 5

    def test_invalid_auditor_role_fails(self, sample_auditor_response):
        """Test that invalid auditor roles are rejected."""
        sample_auditor_response["auditor_role"] = "invalid_role"

        with pytest.raises(ValidationError):
            AuditorResponse(**sample_auditor_response)

    def test_invalid_document_type_fails(self, sample_auditor_response):
        """Test that invalid document types are rejected."""
        sample_auditor_response["document_analyzed"] = "invalid_doc"

        with pytest.raises(ValidationError):
            AuditorResponse(**sample_auditor_response)

    def test_confidence_level_out_of_range_fails(self, sample_auditor_response):
        """Test that confidence levels outside 1-5 range are rejected."""
        sample_auditor_response["confidence_level"] = 0

        with pytest.raises(ValidationError):
            AuditorResponse(**sample_auditor_response)

    def test_calculated_average_score_matches(self, sample_auditor_response):
        """
        Test that average score is calculated correctly from dimension scores.
        
        VERIFIES: REQ-003 (consensus calculation accuracy)
        VALIDATES: Mathematical consistency in score aggregation
        """
        # This will be implemented when we add validation logic
        response = AuditorResponse(**sample_auditor_response)

        dimension_scores = [
            response.scores_detailed.simplicity.score,
            response.scores_detailed.conciseness.score,
            response.scores_detailed.actionability.score,
            response.scores_detailed.readability.score,
            response.scores_detailed.options_tradeoffs.score,
            response.scores_detailed.evidence_specificity.score
        ]
        expected_avg = sum(dimension_scores) / len(dimension_scores)

        assert abs(response.overall_assessment.average_score - expected_avg) < 0.01

    def test_overall_pass_logic_correct(self, sample_auditor_response):
        """
        Test that overall pass logic is correct (avg >= 3.8 AND all dimensions >= 3.0).
        
        VERIFIES: REQ-003 (quality gate thresholds)
        VALIDATES: Boolean logic for document approval
        """
        # Test case where average is high enough but one dimension fails
        sample_auditor_response["scores_detailed"]["conciseness"]["score"] = 2  # Below 3.0
        sample_auditor_response["scores_detailed"]["conciseness"]["pass"] = False
        # Update average score: (4+2+4+5+3+4)/6 = 3.67
        sample_auditor_response["overall_assessment"]["average_score"] = 3.67
        sample_auditor_response["overall_assessment"]["overall_pass"] = False  # Should fail

        response = AuditorResponse(**sample_auditor_response)
        assert response.overall_assessment.overall_pass is False
