"""Tests for alignment validation system."""
import pytest
import tempfile
from pathlib import Path
from typing import Dict, List

from llm_council.alignment import AlignmentValidator, AlignmentResult, DocumentDependency


class TestDocumentDependency:
    """Test document dependency definitions."""
    
    def test_document_dependency_creation(self):
        """Test creating document dependencies."""
        dep = DocumentDependency(
            source_stage="vision",
            target_stage="prd", 
            relationship="defines_requirements_for"
        )
        
        assert dep.source_stage == "vision"
        assert dep.target_stage == "prd"
        assert dep.relationship == "defines_requirements_for"
    
    def test_dependency_chain_creation(self):
        """Test creating dependency chains."""
        deps = [
            DocumentDependency("research_brief", "market_scan", "informs"),
            DocumentDependency("market_scan", "vision", "validates"),
            DocumentDependency("vision", "prd", "defines_requirements_for"),
            DocumentDependency("prd", "architecture", "specifies_implementation_for"),
            DocumentDependency("architecture", "implementation_plan", "guides_tasks_for")
        ]
        
        assert len(deps) == 5
        assert deps[0].source_stage == "research_brief"
        assert deps[-1].target_stage == "implementation_plan"


class TestAlignmentResult:
    """Test alignment validation results."""
    
    def test_alignment_result_creation(self):
        """Test creating alignment results."""
        result = AlignmentResult(
            source_stage="vision",
            target_stage="prd",
            alignment_score=4.2,
            is_aligned=True,
            misalignments=[],
            suggestions=["Add more specificity to metrics"]
        )
        
        assert result.source_stage == "vision"
        assert result.target_stage == "prd"
        assert result.alignment_score == 4.2
        assert result.is_aligned
        assert len(result.misalignments) == 0
        assert len(result.suggestions) == 1
    
    def test_alignment_result_with_misalignments(self):
        """Test alignment result with detected misalignments."""
        misalignments = [
            "PRD specifies web interface, but Vision mentions CLI only",
            "Vision targets $2/run cost, PRD has no cost constraints"
        ]
        
        result = AlignmentResult(
            source_stage="vision",
            target_stage="prd",
            alignment_score=2.1,
            is_aligned=False,
            misalignments=misalignments,
            suggestions=["Align interface requirements", "Add cost constraints to PRD"]
        )
        
        assert not result.is_aligned
        assert len(result.misalignments) == 2
        assert "web interface" in result.misalignments[0]
        assert "$2/run cost" in result.misalignments[1]


class TestAlignmentValidator:
    """Test alignment validation logic."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = AlignmentValidator()
        
        assert validator is not None
        assert hasattr(validator, 'validate_alignment')
        assert hasattr(validator, 'generate_backlog_file')
    
    def test_validate_alignment_basic(self):
        """Test basic alignment validation between two documents."""
        validator = AlignmentValidator()
        
        vision_content = """# Vision
        Build a CLI tool for document auditing that costs ≤$2 per run.
        Target users are founders and PMs who need fast feedback.
        """
        
        prd_content = """# PRD  
        ## Requirements
        R-001: CLI interface for document auditing
        R-002: Cost constraint of ≤$2 per audit run
        R-003: Target audience: founders, PMs, engineers
        """
        
        result = validator.validate_alignment("vision", "prd", vision_content, prd_content)
        
        assert isinstance(result, AlignmentResult)
        assert result.source_stage == "vision"
        assert result.target_stage == "prd"
        assert result.alignment_score >= 3.0  # Should be well aligned
        assert result.is_aligned
        assert len(result.misalignments) == 0
    
    def test_validate_alignment_with_conflicts(self):
        """Test alignment validation detecting conflicts."""
        validator = AlignmentValidator()
        
        vision_content = """# Vision
        Build a CLI tool for document auditing.
        Target cost: $2 per run maximum.
        Web interface in future versions.
        """
        
        prd_content = """# PRD
        ## Requirements  
        R-001: Web application with dashboard
        R-002: No cost constraints specified
        R-003: Real-time collaboration features required
        """
        
        result = validator.validate_alignment("vision", "prd", vision_content, prd_content)
        
        assert isinstance(result, AlignmentResult)
        assert not result.is_aligned
        assert result.alignment_score < 3.5  # Should detect conflicts
        assert len(result.misalignments) > 0
        assert len(result.suggestions) > 0
    
    def test_validate_missing_upstream_document(self):
        """Test validation when upstream document is missing."""
        validator = AlignmentValidator()
        
        result = validator.validate_alignment("vision", "prd", "", "# PRD content")
        
        assert isinstance(result, AlignmentResult)
        assert not result.is_aligned
        assert "missing" in str(result.misalignments[0]).lower()
    
    def test_validate_empty_target_document(self):
        """Test validation when target document is empty."""
        validator = AlignmentValidator()
        
        result = validator.validate_alignment("vision", "prd", "# Vision content", "")
        
        assert isinstance(result, AlignmentResult)
        assert not result.is_aligned
        assert len(result.misalignments) > 0
    
    def test_generate_backlog_file(self):
        """Test backlog file generation for misalignments."""
        validator = AlignmentValidator()
        
        misalignments = [
            "PRD interface differs from Vision (web vs CLI)",
            "Missing cost constraints in PRD"
        ]
        
        suggestions = [
            "Align interface requirements between Vision and PRD",
            "Add cost constraints section to PRD"
        ]
        
        result = AlignmentResult(
            source_stage="vision",
            target_stage="prd", 
            alignment_score=2.5,
            is_aligned=False,
            misalignments=misalignments,
            suggestions=suggestions
        )
        
        backlog_content = validator.generate_backlog_file(result)
        
        assert isinstance(backlog_content, str)
        assert "ALIGNMENT BACKLOG" in backlog_content
        assert "vision" in backlog_content.lower()
        assert "prd" in backlog_content.lower()
        assert "web vs CLI" in backlog_content
        assert "cost constraints" in backlog_content
        assert len(backlog_content) > 100  # Should be substantial content
    
    def test_get_document_dependencies(self):
        """Test getting dependencies for document stages."""
        validator = AlignmentValidator()
        
        # Vision should depend on market_scan
        deps = validator.get_document_dependencies("vision")
        assert len(deps) > 0
        assert any(dep.source_stage == "market_scan" for dep in deps)
        
        # PRD should depend on vision
        deps = validator.get_document_dependencies("prd") 
        assert any(dep.source_stage == "vision" for dep in deps)
        
        # Implementation plan should depend on architecture
        deps = validator.get_document_dependencies("implementation_plan")
        assert any(dep.source_stage == "architecture" for dep in deps)
    
    def test_validate_full_document_chain(self):
        """Test validating alignment across full document chain."""
        validator = AlignmentValidator()
        
        documents = {
            "research_brief": "# Research\nCLI tools market analysis shows demand for audit automation.",
            "market_scan": "# Market Scan\nCompetitive analysis shows CLI-first approach viable.",
            "vision": "# Vision\nBuild CLI audit tool for document quality gates.",
            "prd": "# PRD\nR-001: CLI interface required\nR-002: Document audit functionality",
            "architecture": "# Architecture\nCLI framework: Click\nCore: AuditorOrchestrator class",
            "implementation_plan": "# Implementation\nT-001: Build CLI\nT-002: Implement orchestrator"
        }
        
        all_results = validator.validate_document_chain(documents)
        
        assert isinstance(all_results, list)
        assert len(all_results) > 0
        
        # Should have results for each dependency relationship
        stage_pairs = [(r.source_stage, r.target_stage) for r in all_results]
        expected_pairs = [("market_scan", "vision"), ("vision", "prd"), ("prd", "architecture")]
        
        for expected in expected_pairs:
            assert expected in stage_pairs