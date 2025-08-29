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
    
    def test_validate_missing_research_brief(self):
        """Test validation when research brief is missing."""
        validator = AlignmentValidator()
        
        # Missing research brief should cause market_scan alignment to fail
        documents = {
            "research_brief": "",  # Empty/missing
            "market_scan": "# Market Scan\nCompetitive analysis shows CLI tools are viable.",
        }
        
        results = validator.validate_document_chain(documents)
        research_to_market = [r for r in results if r.source_stage == "research_brief"][0]
        
        assert not research_to_market.is_aligned
        assert "missing" in research_to_market.misalignments[0].lower()
        assert "research_brief" in research_to_market.misalignments[0]
    
    def test_validate_research_brief_content_requirements(self):
        """Test that research brief validates required content for market scan."""
        validator = AlignmentValidator()
        
        # Research brief should validate methodology and sources
        incomplete_research = "# Research\nSome basic problem analysis."
        complete_research = """# Research Brief
        ## Problem Analysis
        Document review processes are manual and inconsistent.
        
        ## Methodology
        Primary research: 20 founder interviews
        Secondary research: Market analysis reports
        
        ## Key Sources
        - Developer productivity survey (Stack Overflow 2024)
        - Code review automation study (GitHub)
        - Enterprise workflow analysis (Forrester)
        """
        
        market_content = "# Market Scan\nCompetitive analysis shows opportunity."
        
        # Test incomplete research brief
        result1 = validator.validate_alignment("research_brief", "market_scan", incomplete_research, market_content)
        # Should pass basic validation since both docs exist
        assert result1.is_aligned
        
        # Test complete research brief 
        result2 = validator.validate_alignment("research_brief", "market_scan", complete_research, market_content)
        assert result2.is_aligned
    
    def test_validate_prd_mvp_versioning(self):
        """Test that PRD includes clear MVP delivery checkpoints."""
        validator = AlignmentValidator()
        
        vision_content = """# Vision
        Build CLI audit tool with multi-LLM consensus for document quality gates.
        MVP scope: basic auditing with 4 docs and simple consensus.
        """
        
        # PRD without MVP versioning should suggest adding it
        prd_no_versions = """# PRD
        ## Requirements
        R-001: CLI interface for document auditing
        R-002: Multi-LLM auditor council with consensus
        """
        
        # PRD with clear MVP versioning
        prd_with_versions = """# PRD
        ## MVP Delivery Strategy
        
        ### M1: Core Foundation (Week 1-2)
        - Basic CLI that ingests markdown docs
        - Single auditor execution with JSON output
        - Simple pass/fail decision
        
        ### M2: Multi-LLM Council (Week 3-4)  
        - Parallel execution of 6 specialized auditors
        - Consensus engine with trimmed mean algorithm
        - Human review interface for disagreements
        
        ### M3: Document Pipeline (Week 5-6)
        - Full Vision → PRD → Architecture workflow
        - Cross-document alignment validation
        - Quality gates with automated promotion
        
        ### Future Iterations (Post-MVP)
        - Research agent for internet context gathering
        - Iterative LLM-to-LLM refinement loops
        - Advanced revision strategies
        """
        
        # Test that MVP versioning improves alignment
        result1 = validator.validate_alignment("vision", "prd", vision_content, prd_no_versions)
        result2 = validator.validate_alignment("vision", "prd", vision_content, prd_with_versions)
        
        # Both should align, but versioned should have better score
        assert result1.is_aligned
        assert result2.is_aligned
        assert result2.alignment_score >= result1.alignment_score