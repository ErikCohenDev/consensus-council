"""Pydantic models for auditor response validation."""
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, model_validator


class DimensionScore(BaseModel):
    """Score for individual evaluation dimension."""
    score: int = Field(ge=1, le=5, description="Score from 1-5")
    pass_: bool = Field(alias="pass", description="Whether this dimension passes")
    justification: str = Field(min_length=50, description="Explanation of score")
    improvements: List[str] = Field(min_length=1, description="Specific improvement suggestions")


class OverallAssessment(BaseModel):
    """Overall assessment of document."""
    average_score: float = Field(description="Calculated average of all dimension scores")
    overall_pass: bool = Field(description="Whether document passes overall")
    summary: str = Field(min_length=50, description="Summary of assessment")
    top_strengths: List[str] = Field(max_length=3, description="Top 3 strengths")
    top_risks: List[str] = Field(max_length=3, description="Top 3 risks")
    quick_wins: List[str] = Field(max_length=3, description="Top 3 quick wins")


class BlockingIssue(BaseModel):
    """Blocking issue that prevents document approval."""
    severity: Literal["critical", "high", "medium", "low"]
    category: Literal["technical", "business", "legal", "security", "ux"]
    description: str
    impact: str
    suggested_resolution: str
    line_reference: Optional[str] = None


class AlignmentFeedback(BaseModel):
    """Feedback on document alignment."""
    upstream_consistency: Dict[str, Any] = Field(
        description="Consistency with upstream documents"
    )
    internal_consistency: Dict[str, Any] = Field(
        description="Internal consistency within document"
    )


class ScoresDetailed(BaseModel):
    """Detailed scores for all dimensions."""
    simplicity: DimensionScore
    conciseness: DimensionScore
    actionability: DimensionScore
    readability: DimensionScore
    options_tradeoffs: DimensionScore
    evidence_specificity: DimensionScore


class AuditorResponse(BaseModel):
    """Complete auditor response schema."""
    auditor_role: Literal["pm", "infrastructure", "data_eval", "security", "ux", "cost"]
    document_analyzed: Literal["research_brief", "market_scan", "vision", "prd", "architecture", "implementation_plan"]
    audit_timestamp: datetime
    scores_detailed: ScoresDetailed
    overall_assessment: OverallAssessment
    blocking_issues: List[BlockingIssue] = Field(default_factory=list)
    alignment_feedback: AlignmentFeedback
    role_specific_insights: Dict[str, str] = Field(default_factory=dict)
    confidence_level: int = Field(ge=1, le=5, description="Confidence in assessment")

    @model_validator(mode='after')
    def validate_assessment_logic(self):
        """Validate average score calculation and overall pass logic."""
        scores_detailed = self.scores_detailed
        overall_assessment = self.overall_assessment

        # Validate average score calculation
        dimension_scores = [
            scores_detailed.simplicity.score,
            scores_detailed.conciseness.score,
            scores_detailed.actionability.score,
            scores_detailed.readability.score,
            scores_detailed.options_tradeoffs.score,
            scores_detailed.evidence_specificity.score
        ]
        expected_avg = sum(dimension_scores) / len(dimension_scores)

        if abs(overall_assessment.average_score - expected_avg) > 0.01:
            raise ValueError(f"Average score {overall_assessment.average_score} doesn't match calculated average {expected_avg}")

        # Validate overall pass logic
        min_dimension_score = min(dimension_scores)
        expected_pass = overall_assessment.average_score >= 3.8 and min_dimension_score >= 3.0

        if overall_assessment.overall_pass != expected_pass:
            raise ValueError(f"Overall pass {overall_assessment.overall_pass} doesn't match logic (avg={overall_assessment.average_score}, min={min_dimension_score})")

        return self
