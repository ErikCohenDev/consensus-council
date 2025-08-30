"""Consensus engine for LLM council decision making."""
import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ConsensusResult:
    """Result of consensus calculation."""
    weighted_average: float
    consensus_pass: bool
    approval_pass: bool
    final_decision: str  # "PASS" or "FAIL"
    agreement_level: float
    participating_auditors: List[str]
    failure_reasons: List[str]
    requires_human_review: bool


def calculate_trimmed_mean(scores: List[float], trim_percentage: float) -> float:
    """Calculate trimmed mean by removing outliers."""
    if not scores:
        raise ValueError("Cannot calculate trimmed mean of empty list")

    if len(scores) < 5:
        # Not enough data points to trim effectively
        return statistics.mean(scores)

    # Calculate how many scores to trim from each end
    trim_count = max(1, int(len(scores) * trim_percentage))

    # Sort scores and remove outliers from both ends
    sorted_scores = sorted(scores)
    trimmed_scores = sorted_scores[trim_count:-trim_count]

    if not trimmed_scores:
        # Safety check - if we trimmed everything, use original mean
        return statistics.mean(scores)

    return statistics.mean(trimmed_scores)


def calculate_agreement_level(scores: List[float]) -> float:
    """Calculate agreement level based on variance (0=low agreement, 1=perfect agreement)."""
    if len(scores) <= 1:
        return 1.0

    # Use coefficient of variation normalized to 0-1 scale
    mean_score = statistics.mean(scores)
    if mean_score == 0:
        return 1.0 if all(s == 0 for s in scores) else 0.0

    stdev = statistics.stdev(scores)
    coefficient_of_variation = stdev / mean_score

    # Normalize to 0-1 scale (lower CV = higher agreement)
    # CV of 0.5 or higher is considered low agreement
    agreement = max(0.0, 1.0 - (coefficient_of_variation / 0.5))
    return min(1.0, agreement)


class ConsensusEngine:
    """Engine for calculating consensus from multiple auditor responses."""

    def __init__(
        self,
        score_threshold: float = 3.8,
        approval_threshold: float = 0.67,
        trim_percentage: float = 0.1,
        disagreement_threshold: float = 1.0,
        blocking_gates: Optional[Dict[str, int]] = None
    ):
        self.score_threshold = score_threshold
        self.approval_threshold = approval_threshold
        self.trim_percentage = trim_percentage
        self.disagreement_threshold = disagreement_threshold
        self.blocking_gates = blocking_gates or {"critical": 0, "high": 2, "medium": 5}

    def calculate_consensus(self, responses: List[Dict[str, Any]]) -> ConsensusResult:
        """Calculate consensus from auditor responses."""
        if not responses:
            return ConsensusResult(
                weighted_average=0.0,
                consensus_pass=False,
                approval_pass=False,
                final_decision="FAIL",
                agreement_level=0.0,
                participating_auditors=[],
                failure_reasons=["No auditor responses provided"],
                requires_human_review=True
            )

        # Extract scores and calculate consensus
        all_scores = []
        approvals = 0
        blocking_issues_by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        participating_auditors = []

        for response in responses:
            participating_auditors.append(response["auditor_role"])

            # Get average score from this auditor
            avg_score = response["overall_assessment"]["average_score"]
            all_scores.append(avg_score)

            # Count approvals
            if response["overall_assessment"]["overall_pass"]:
                approvals += 1

            # Count blocking issues
            for issue in response.get("blocking_issues", []):
                severity = issue.get("severity", "low")
                if severity in blocking_issues_by_severity:
                    blocking_issues_by_severity[severity] += 1

        # Calculate consensus metrics
        weighted_average = calculate_trimmed_mean(all_scores, self.trim_percentage)
        agreement_level = calculate_agreement_level(all_scores)
        approval_percentage = approvals / len(responses)

        # Check pass conditions
        consensus_pass = weighted_average >= self.score_threshold
        approval_pass = approval_percentage >= self.approval_threshold

        # Check blocking issues
        blocking_issues_fail = False
        failure_reasons = []

        for severity, count in blocking_issues_by_severity.items():
            if count > self.blocking_gates.get(severity, 999):
                blocking_issues_fail = True
                failure_reasons.append(f"Too many {severity} issues: {count} > {self.blocking_gates[severity]}")

        # Check for disagreement requiring human review
        requires_human_review = False
        if agreement_level < (
            1.0 - self.disagreement_threshold / 5.0
        ):  # Convert threshold to agreement scale
            requires_human_review = True
            failure_reasons.append(f"High disagreement detected (agreement: {agreement_level:.2f})")

        # Final decision logic
        if blocking_issues_fail:
            final_decision = "FAIL"
        elif not consensus_pass:
            final_decision = "FAIL"
            failure_reasons.append(f"Consensus score {weighted_average:.2f} below threshold {self.score_threshold}")
        elif not approval_pass:
            final_decision = "FAIL"
            failure_reasons.append(f"Approval rate {approval_percentage:.2f} below threshold {self.approval_threshold}")
        else:
            final_decision = "PASS"

        return ConsensusResult(
            weighted_average=weighted_average,
            consensus_pass=consensus_pass,
            approval_pass=approval_pass,
            final_decision=final_decision,
            agreement_level=agreement_level,
            participating_auditors=participating_auditors,
            failure_reasons=failure_reasons,
            requires_human_review=requires_human_review
        )
