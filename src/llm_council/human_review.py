"""Human review interface for LLM Council audit system."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any
import click


@dataclass
class ReviewDecision:
    """Human review decision with rationale and planned actions."""
    action: str  # APPROVE, REVISE, ADD_CONTEXT, OVERRIDE, ABORT
    rationale: str
    context_additions: List[str]
    planned_changes: List[str]


@dataclass
class ReviewTrigger:
    """Represents a trigger for human review."""
    stage: str
    trigger_type: str
    description: str
    requires_review: bool
    
    @classmethod
    def from_consensus_result(cls, stage: str, consensus_result) -> ReviewTrigger:
        """Create review trigger from consensus result."""
        if consensus_result.requires_human_review:
            if consensus_result.agreement_level < 0.5:
                return cls(
                    stage=stage,
                    trigger_type="low_consensus", 
                    description=f"Low consensus (agreement: {consensus_result.agreement_level:.2f})",
                    requires_review=True
                )
            elif not consensus_result.consensus_pass:
                return cls(
                    stage=stage,
                    trigger_type="consensus_fail",
                    description=f"Consensus failed (score: {consensus_result.weighted_average:.1f})",
                    requires_review=True
                )

        return cls(
            stage=stage,
            trigger_type="none",
            description="No review required",
            requires_review=False
        )
    
    @classmethod
    def for_strategic_stage(cls, stage: str) -> ReviewTrigger:
        """Create trigger for strategic document stages."""
        strategic_stages = {"research_brief", "market_scan", "vision", "prd"}

        if stage in strategic_stages:
            return cls(
                stage=stage,
                trigger_type="strategic_document",
                description=f"Strategic document ({stage}) requires human review",
                requires_review=True
            )

        return cls(
            stage=stage,
            trigger_type="none",
            description="Implementation document - no automatic review",
            requires_review=False
        )


class HumanReviewInterface:
    """Interactive interface for human review of audit results."""
    
    def __init__(self):
        """Initialize human review interface."""
        pass
    
    def should_trigger_review(self, stage: str, auditor_responses: List[Dict[str, Any]], 
                            consensus_result) -> bool:
        """Determine if human review should be triggered."""
        # Strategic documents always trigger review
        strategic_trigger = ReviewTrigger.for_strategic_stage(stage)
        if strategic_trigger.requires_review:
            return True

        # Low consensus or failed consensus triggers review
        if hasattr(consensus_result, 'requires_human_review'):
            return consensus_result.requires_human_review

        # High severity blocking issues trigger review
        for response in auditor_responses:
            blocking_issues = response.get("blocking_issues", [])
            for issue in blocking_issues:
                if issue.get("severity") in ["critical", "high"]:
                    return True

        return False
    
    def display_disagreement_summary(self, stage: str, auditor_responses: List[Dict[str, Any]], 
                                   consensus_result) -> None:
        """Display summary of auditor disagreements."""
        click.echo("🚨 Human Review Required")
        click.echo("")
        click.echo(f"Stage: {stage.upper()} Document")

        try:
            if hasattr(consensus_result, 'agreement_level'):
                click.echo(f"Trigger: Low consensus (agreement: {consensus_result.agreement_level:.1f})")
            else:
                click.echo("Trigger: Strategic document review")
        except (TypeError, AttributeError):
            click.echo("Trigger: Review required")
        click.echo("")

        click.echo("Auditor Disagreement Summary:")
        click.echo("━" * 45)

        # Show individual auditor assessments
        for response in auditor_responses:
            role = response.get("auditor_role", "unknown")
            assessment = response.get("overall_assessment", {})
            pass_status = "✅ PASS" if assessment.get("overall_pass", False) else "❌ FAIL"
    
            click.echo(f"• {role.upper()}: {pass_status}")
    
                # Show key concerns
            risks = assessment.get("top_risks", [])
            if risks:
                click.echo(f"  Concerns: {', '.join(risks[:2])}")

        click.echo("━" * 45)
        click.echo("")
    
    def format_auditor_summary(self, auditor_response: Dict[str, Any]) -> str:
        """Format detailed summary for individual auditor."""
        role = auditor_response.get("auditor_role", "unknown")
        assessment = auditor_response.get("overall_assessment", {})

        # Use human-friendly role casing for display (e.g., "Security Auditor")
        lines = [f"{role.title()} Auditor:"]

        # Overall status
        overall_pass = assessment.get("overall_pass", False)
        summary = assessment.get("summary", "No summary provided")
        lines.append(f"Status: {'✅ PASS' if overall_pass else '❌ FAIL'}")
        lines.append(f"Summary: {summary}")
        lines.append("")

        # Top strengths
        strengths = assessment.get("top_strengths", [])
        if strengths:
            lines.append("✅ Strengths:")
            for strength in strengths:
                lines.append(f"  • {strength}")
            lines.append("")

        # Top risks
        risks = assessment.get("top_risks", [])
        if risks:
            lines.append("⚠️ Concerns:")
            for risk in risks:
                lines.append(f"  • {risk}")
            lines.append("")

        # Blocking issues
        blocking_issues = auditor_response.get("blocking_issues", [])
        if blocking_issues:
            lines.append("🚨 Blocking Issues:")
            for issue in blocking_issues:
                severity = issue.get("severity", "medium")
                description = issue.get("description", "")
                lines.append(f"  • [{severity.upper()}] {description}")
            lines.append("")

        return "\n".join(lines)
    
    def conduct_review(self, stage: str, auditor_responses: List[Dict[str, Any]], 
                      consensus_result) -> ReviewDecision:
        """Conduct interactive human review session."""
        # Display the disagreement summary
        self.display_disagreement_summary(stage, auditor_responses, consensus_result)

        # Show detailed auditor feedback
        click.echo("📋 Detailed Auditor Feedback")
        click.echo("")
        for response in auditor_responses:
            summary = self.format_auditor_summary(response)
            click.echo(summary)

        # Present decision options
        click.echo("🎯 Your Decision")
        click.echo("")
        click.echo("Based on auditor feedback, how should we proceed?")
        click.echo("")
        click.echo("Options:")
        click.echo("[1] APPROVE - Pass to next stage with current document")
        click.echo("[2] REVISE - Make changes and re-audit")
        click.echo("[3] ADD CONTEXT - Provide more information for auditors")
        click.echo("[4] OVERRIDE - Pass despite auditor concerns (requires justification)")
        click.echo("[5] ABORT - Stop the audit process")
        click.echo("")

        # Get user choice
        while True:
            try:
                choice_input = input("Enter choice [1-5]: ").strip()
                if choice_input in ["1", "2", "3", "4", "5"]:
                    choice = choice_input
                    break
                else:
                    click.echo("Invalid choice. Please enter 1-5.")
            except (KeyboardInterrupt, EOFError):
                return ReviewDecision("ABORT", "User interrupted", [], [])

        # Handle different decision types
        if choice == "1":
            return ReviewDecision(
                action="APPROVE",
                rationale="Human reviewer approved despite auditor concerns",
                context_additions=[],
                planned_changes=[]
            )

        elif choice == "2":
            changes = input("What changes will you make? ")
            return ReviewDecision(
                action="REVISE", 
                rationale=changes,
                context_additions=[],
                planned_changes=[changes]
            )

        elif choice == "3":
            context = input("Additional context for auditors: ")
            return ReviewDecision(
                action="ADD_CONTEXT",
                rationale="Adding context for auditor re-evaluation",
                context_additions=[context],
                planned_changes=[]
            )

        elif choice == "4":
            justification = input("Override justification: ")
            return ReviewDecision(
                action="OVERRIDE",
                rationale=justification,
                context_additions=[],
                planned_changes=[]
            )

        else:  # choice == "5"
            return ReviewDecision(
                action="ABORT",
                rationale="Human reviewer chose to abort audit",
                context_additions=[],
                planned_changes=[]
            )
    
    def generate_review_record(self, stage: str, decision: ReviewDecision, 
                             auditor_responses: List[Dict[str, Any]]) -> str:
        """Generate markdown record of human review decision."""
        lines = [f"# Human Review Record - {stage.upper()}"]
        lines.append("")
        lines.append(f"**Decision:** {decision.action}")
        lines.append(f"**Rationale:** {decision.rationale}")
        lines.append("")

        if decision.context_additions:
            lines.append("## Context Added")
            for context in decision.context_additions:
                lines.append(f"- {context}")
            lines.append("")

        if decision.planned_changes:
            lines.append("## Planned Changes")
            for change in decision.planned_changes:
                lines.append(f"- {change}")
            lines.append("")

        lines.append("## Auditor Summary")
        total_auditors = len(auditor_responses)
        passing_auditors = sum(1 for r in auditor_responses 
                             if r.get("overall_assessment", {}).get("overall_pass", False))

        lines.append(f"- Total Auditors: {total_auditors}")
        lines.append(f"- Passing Votes: {passing_auditors}/{total_auditors}")
        lines.append("")

        lines.append("---")
        lines.append("*Generated by LLM Council Human Review Interface*")

        return "\n".join(lines)


__all__ = ["HumanReviewInterface", "ReviewDecision", "ReviewTrigger"]
