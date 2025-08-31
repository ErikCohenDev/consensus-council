"""
Tests for human review interface system.

VERIFIES: REQ-005, REQ-006 (human review triggers, decision framework)
VALIDATES: Interactive review workflow and decision capture
USE_CASE: UC-004, UC-008 (human intervention, strategic decisions)
INTERFACES: human_review.py (HumanReviewInterface, ReviewDecision, ReviewTrigger)
LAST_SYNC: 2025-08-30
"""
import pytest
from io import StringIO
from unittest.mock import Mock, patch
from typing import List

from llm_council.human_review import HumanReviewInterface, ReviewDecision, ReviewTrigger
from llm_council.consensus import ConsensusResult


class TestReviewDecision:
    """Test review decision data structure."""
    
    def test_review_decision_creation(self):
        """
        Test creating review decisions.
        
        VERIFIES: REQ-005 (human decision capture and structure)
        VALIDATES: ReviewDecision data model with action and rationale
        USE_CASE: UC-004 (human approval/rejection decisions)
        """
        decision = ReviewDecision(
            action="APPROVE",
            rationale="Document meets all requirements",
            context_additions=[],
            planned_changes=[]
        )
        
        assert decision.action == "APPROVE"
        assert decision.rationale == "Document meets all requirements"
        assert len(decision.context_additions) == 0
        assert len(decision.planned_changes) == 0
    
    def test_review_decision_with_revisions(self):
        """Test review decision with planned changes."""
        decision = ReviewDecision(
            action="REVISE",
            rationale="Scope too broad for MVP",
            context_additions=["Timeline is 6 months", "Budget is $50K"],
            planned_changes=["Remove mobile app", "Reduce feature set"]
        )
        
        assert decision.action == "REVISE"
        assert len(decision.context_additions) == 2
        assert len(decision.planned_changes) == 2
        assert "mobile app" in decision.planned_changes[0]


class TestReviewTrigger:
    """Test review trigger detection."""
    
    def test_trigger_detection_low_consensus(self):
        """
        Test trigger detection for low consensus.
        
        VERIFIES: REQ-005 (consensus threshold triggers for human review)
        VALIDATES: ReviewTrigger detection logic for disagreement
        USE_CASE: UC-004 (automated human review escalation)
        """
        consensus_result = ConsensusResult(
            weighted_average=3.2,
            consensus_pass=False,
            approval_pass=True,
            final_decision="FAIL",
            agreement_level=0.3,  # Low agreement
            participating_auditors=["pm", "ux", "cost"],
            failure_reasons=["Low consensus score"],
            requires_human_review=True
        )
        
        trigger = ReviewTrigger.from_consensus_result("vision", consensus_result)
        
        assert trigger.stage == "vision"
        assert trigger.trigger_type == "low_consensus"
        assert trigger.requires_review
        assert "Low consensus" in trigger.description
    
    def test_trigger_detection_strategic_document(self):
        """Test trigger for strategic document types."""
        trigger = ReviewTrigger.for_strategic_stage("vision")
        
        assert trigger.stage == "vision"
        assert trigger.trigger_type == "strategic_document"
        assert trigger.requires_review
        assert "strategic" in trigger.description.lower()
    
    def test_no_trigger_for_implementation_docs(self):
        """Test that implementation docs don't automatically trigger review."""
        trigger = ReviewTrigger.for_strategic_stage("implementation_plan")
        
        assert not trigger.requires_review


class TestHumanReviewInterface:
    """Test human review interface functionality."""
    
    def test_interface_initialization(self):
        """Test human review interface initialization."""
        interface = HumanReviewInterface()
        
        assert interface is not None
        assert hasattr(interface, 'conduct_review')
        assert hasattr(interface, 'display_disagreement_summary')
    
    def test_display_disagreement_summary(self, capsys):
        """Test displaying disagreement summary."""
        interface = HumanReviewInterface()
        
        auditor_responses = [
            {
                "auditor_role": "pm",
                "overall_assessment": {
                    "overall_pass": True,
                    "summary": "Strong strategic direction",
                    "top_risks": ["Timeline risk"],
                    "quick_wins": ["Add metrics"]
                },
                "scores_detailed": {
                    "simplicity": {"score": 4, "pass": True},
                    "actionability": {"score": 3, "pass": True}
                }
            },
            {
                "auditor_role": "ux", 
                "overall_assessment": {
                    "overall_pass": False,
                    "summary": "Scope too broad for MVP",
                    "top_risks": ["Feature complexity"],
                    "quick_wins": ["Reduce scope"]
                },
                "scores_detailed": {
                    "simplicity": {"score": 2, "pass": False},
                    "actionability": {"score": 4, "pass": True}
                }
            }
        ]
        
        consensus_result = ConsensusResult(
            weighted_average=3.2,
            consensus_pass=False,
            approval_pass=False,
            final_decision="FAIL",
            agreement_level=0.4,
            participating_auditors=["pm", "ux"],
            failure_reasons=["Low consensus"],
            requires_human_review=True
        )
        
        interface.display_disagreement_summary("vision", auditor_responses, consensus_result)
        
        captured = capsys.readouterr()
        assert "Human Review Required" in captured.out
        assert "vision" in captured.out.lower()
        assert "pm" in captured.out.lower()
        assert "ux" in captured.out.lower()
        assert "disagreement" in captured.out.lower()
    
    @patch('builtins.input')
    def test_conduct_review_approve(self, mock_input):
        """Test conducting review with approval decision."""
        mock_input.return_value = "1"  # APPROVE
        
        interface = HumanReviewInterface()
        
        auditor_responses = [{"auditor_role": "pm", "overall_assessment": {"overall_pass": True}}]
        consensus_result = ConsensusResult(
            weighted_average=3.9,
            consensus_pass=True,
            approval_pass=True,
            final_decision="PASS",
            agreement_level=0.8,
            participating_auditors=["pm"],
            failure_reasons=[],
            requires_human_review=False
        )
        
        decision = interface.conduct_review("vision", auditor_responses, consensus_result)
        
        assert decision.action == "APPROVE"
        assert len(decision.rationale) > 0
    
    @patch('builtins.input')
    def test_conduct_review_revise(self, mock_input):
        """Test conducting review with revision decision."""
        # Mock sequence: choice=2 (REVISE), then change description
        mock_input.side_effect = ["2", "Reduce MVP scope based on UX feedback"]
        
        interface = HumanReviewInterface()
        
        auditor_responses = [{"auditor_role": "ux", "overall_assessment": {"overall_pass": False}}]
        consensus_result = ConsensusResult(
            weighted_average=2.8,
            consensus_pass=False,
            approval_pass=False,
            final_decision="FAIL",
            agreement_level=0.3,
            participating_auditors=["ux"],
            failure_reasons=["Low scores"],
            requires_human_review=True
        )
        
        decision = interface.conduct_review("vision", auditor_responses, consensus_result)
        
        assert decision.action == "REVISE"
        assert "Reduce MVP scope" in decision.rationale
    
    @patch('builtins.input')
    def test_conduct_review_add_context(self, mock_input):
        """Test conducting review with context addition."""
        # Mock sequence: choice=3 (ADD_CONTEXT), then context input
        mock_input.side_effect = ["3", "Timeline is flexible, can extend to 8 months if needed"]
        
        interface = HumanReviewInterface()
        
        decision = interface.conduct_review("prd", [], Mock())
        
        assert decision.action == "ADD_CONTEXT"
        assert "Timeline is flexible" in decision.context_additions[0]
    
    @patch('builtins.input')  
    def test_conduct_review_override(self, mock_input):
        """Test conducting review with override decision."""
        mock_input.side_effect = ["4", "Business priority overrides UX concerns for MVP"]
        
        interface = HumanReviewInterface()
        
        decision = interface.conduct_review("prd", [], Mock())
        
        assert decision.action == "OVERRIDE"
        assert "Business priority" in decision.rationale
    
    @patch('builtins.input')
    def test_conduct_review_abort(self, mock_input):
        """Test conducting review with abort decision.""" 
        mock_input.return_value = "5"  # ABORT
        
        interface = HumanReviewInterface()
        
        decision = interface.conduct_review("architecture", [], Mock())
        
        assert decision.action == "ABORT"
    
    @patch('builtins.input')
    def test_review_invalid_input_retry(self, mock_input):
        """Test that invalid input prompts for retry."""
        # Invalid input, then valid choice
        mock_input.side_effect = ["invalid", "6", "1"]
        
        interface = HumanReviewInterface()
        
        decision = interface.conduct_review("vision", [], Mock())
        
        assert decision.action == "APPROVE"
    
    def test_format_auditor_summary(self):
        """Test formatting individual auditor summaries."""
        interface = HumanReviewInterface()
        
        auditor_response = {
            "auditor_role": "security",
            "overall_assessment": {
                "overall_pass": True,
                "summary": "Good security considerations",
                "top_risks": ["Data exposure", "Auth bypass"],
                "quick_wins": ["Add HTTPS", "Input validation"]
            },
            "scores_detailed": {
                "simplicity": {"score": 4, "pass": True},
                "evidence_specificity": {"score": 3, "pass": True}
            },
            "blocking_issues": [
                {"severity": "high", "description": "Missing threat model"}
            ]
        }
        
        summary = interface.format_auditor_summary(auditor_response)
        
        assert "Security Auditor" in summary
        assert "Good security considerations" in summary
        assert "Data exposure" in summary
        assert "Add HTTPS" in summary
        assert "threat model" in summary
    
    def test_should_trigger_review_strategic_docs(self):
        """Test review triggering for strategic documents."""
        interface = HumanReviewInterface()
        
        # Strategic documents should trigger review
        assert interface.should_trigger_review("research_brief", Mock(), Mock())
        assert interface.should_trigger_review("market_scan", Mock(), Mock())  
        assert interface.should_trigger_review("vision", Mock(), Mock())
        assert interface.should_trigger_review("prd", Mock(), Mock())
        
        # Implementation docs should not automatically trigger  
        assert not interface.should_trigger_review("architecture", Mock(), Mock())
        assert not interface.should_trigger_review("implementation_plan", Mock(), Mock())
    
    def test_should_trigger_review_low_consensus(self):
        """Test review triggering for low consensus."""
        interface = HumanReviewInterface()
        
        low_consensus = ConsensusResult(
            weighted_average=3.0,
            consensus_pass=False,
            approval_pass=False,
            final_decision="FAIL",
            agreement_level=0.2,  # Very low agreement
            participating_auditors=["pm", "ux"],
            failure_reasons=["Low agreement"],
            requires_human_review=True
        )
        
        # Should trigger even for implementation docs if consensus is low
        assert interface.should_trigger_review("architecture", [], low_consensus)