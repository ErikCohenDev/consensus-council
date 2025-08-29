"""Pytest configuration and shared fixtures."""
import pytest
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture 
def sample_quality_gates():
    """Sample quality gates configuration for testing."""
    return {
        "consensus_thresholds": {
            "vision_to_prd": {
                "score_threshold": 3.8,
                "approval_threshold": 0.67,
                "alignment_threshold": 4.0,
                "required_auditors": ["pm", "ux", "cost"]
            }
        },
        "auditor_config": {
            "available_roles": ["pm", "infrastructure", "data_eval", "security", "ux", "cost"],
            "parallel_execution": True,
            "timeout_seconds": 60,
            "max_retries": 3
        },
        "blocking_severity_gates": {
            "critical": 0,
            "high": 2,
            "medium": 5,
            "low": 10
        }
    }


@pytest.fixture
def sample_auditor_response():
    """Sample valid auditor response for testing."""
    return {
        "auditor_role": "pm",
        "document_analyzed": "vision", 
        "audit_timestamp": "2025-08-29T12:00:00Z",
        "scores_detailed": {
            "simplicity": {
                "score": 4,
                "pass": True,
                "justification": "Document is clear and well-structured with good explanations",
                "improvements": ["Consider adding more concrete examples"]
            },
            "conciseness": {
                "score": 3,
                "pass": True,
                "justification": "Mostly concise but some sections could be tightened up",
                "improvements": ["Remove redundant explanations in section 2"]
            },
            "actionability": {
                "score": 4,
                "pass": True,
                "justification": "Clear action items and implementation guidance provided",
                "improvements": ["Add specific timeline estimates"]
            },
            "readability": {
                "score": 5,
                "pass": True,
                "justification": "Excellent structure with clear headings and logical flow",
                "improvements": ["Perfect as-is"]
            },
            "options_tradeoffs": {
                "score": 3,
                "pass": True,
                "justification": "Some alternatives considered but could explore more options",
                "improvements": ["Add comparison table of alternatives"]
            },
            "evidence_specificity": {
                "score": 4,
                "pass": True,
                "justification": "Good use of specific examples and data points throughout the document with concrete metrics",
                "improvements": ["Include more quantitative data"]
            }
        },
        "overall_assessment": {
            "average_score": 3.83,
            "overall_pass": True,
            "summary": "Strong vision document with clear direction and good implementation guidance",
            "top_strengths": ["Clear structure", "Actionable guidance", "Good examples"],
            "top_risks": ["Scope creep potential", "Timeline aggressive"],
            "quick_wins": ["Add timeline estimates", "Include comparison table"]
        },
        "blocking_issues": [],
        "alignment_feedback": {
            "upstream_consistency": {
                "score": 4,
                "issues": [],
                "suggestions": ["Ensure market scan conclusions align with vision"]
            },
            "internal_consistency": {
                "score": 5,
                "issues": [],
                "suggestions": []
            }
        },
        "role_specific_insights": {
            "market_analysis": "Strong product-market fit validation",
            "user_feedback": "Need user interview validation",
            "competitive_insights": "Clear differentiation from competitors"
        },
        "confidence_level": 4
    }


@pytest.fixture
def sample_template_config():
    """Sample template configuration for testing."""
    return {
        "project_info": {
            "name": "Test Template",
            "description": "Template for testing",
            "stages": ["vision", "prd", "architecture"]
        },
        "auditor_questions": {
            "vision": {
                "pm": {
                    "focus_areas": ["product_strategy", "user_value"],
                    "key_questions": [
                        "Is the value proposition clear?",
                        "Are target users specific?"
                    ]
                },
                "ux": {
                    "focus_areas": ["user_experience"],
                    "key_questions": [
                        "Is the user journey clear?"
                    ]
                }
            },
            "prd": {
                "pm": {
                    "focus_areas": ["requirements"],
                    "key_questions": [
                        "Are requirements clear?"
                    ]
                }
            },
            "architecture": {
                "pm": {
                    "focus_areas": ["technical_design"],
                    "key_questions": [
                        "Is the architecture sound?"
                    ]
                }
            }
        },
        "scoring_weights": {
            "vision": {
                "pm": 1.2,
                "ux": 1.1
            }
        }
    }


@pytest.fixture
def sample_document_content():
    """Sample document content for testing."""
    return """# Test Vision Document

## Problem Statement
Users struggle with managing complex project documentation workflows.

## Solution
An LLM-based audit system that provides structured feedback and consensus-based quality gates.

## Success Metrics
- 90% user satisfaction
- 50% reduction in document review time
- 95% quality gate accuracy
"""