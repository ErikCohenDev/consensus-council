"""
Tests for the provenance tracking service.
"""

import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.llm_council.services.provenance_tracker import ProvenanceTracker
from src.llm_council.models.code_artifact_models import ArtifactType, DriftType


class TestProvenanceTracker:
    """Test cases for ProvenanceTracker."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = ProvenanceTracker(self.temp_dir)
    
    def test_extract_requirements_from_prd(self, tmp_path):
        """Test extraction of REQ-XXX patterns from PRD documents."""
        prd_content = """
        # Product Requirements Document
        
        ## REQ-AUTH-001: User Authentication
        The system must support user authentication via OAuth2
        
        ## REQ-DATA-002: Data Storage
        All user data must be stored securely in encrypted format
        
        ## REQ-API-003: REST API
        Provide RESTful API endpoints for all operations
        """
        
        prd_path = tmp_path / "PRD.md"
        prd_path.write_text(prd_content)
        
        requirements = self.tracker.extract_requirements_from_prd(str(prd_path))
        
        assert len(requirements) == 3
        assert "REQ-AUTH-001" in requirements
        assert "REQ-DATA-002" in requirements
        assert "REQ-API-003" in requirements
        assert "OAuth2" in requirements["REQ-AUTH-001"]
    
    def test_extract_task_ids_from_implementation(self, tmp_path):
        """Test extraction of T-XXX patterns from implementation documents."""
        impl_content = """
        # Implementation Plan
        
        ## T-AUTH-001: Implement OAuth2 Integration
        Set up OAuth2 client with Google and GitHub providers
        
        ## T-DATA-001: Database Schema Design
        Create user and session tables with proper indexing
        """
        
        impl_path = tmp_path / "IMPLEMENTATION.md"
        impl_path.write_text(impl_content)
        
        tasks = self.tracker.extract_task_ids_from_implementation(str(impl_path))
        
        assert len(tasks) == 2
        assert "T-AUTH-001" in tasks
        assert "T-DATA-001" in tasks
        assert "OAuth2" in tasks["T-AUTH-001"]
    
    def test_analyze_code_file_with_provenance(self, tmp_path):
        """Test analysis of code file with provenance header."""
        code_content = """#
# GENERATED_FROM: PRD Section 3.2
# REQUIREMENTS: REQ-AUTH-001, REQ-API-003
# TASKS: T-AUTH-001
# GENERATED: 2024-01-15T10:30:00
#

\"\"\"
Authentication service implementation.
\"\"\"

class AuthService:
    def authenticate(self, token):
        # REQ-AUTH-001: Validate OAuth2 token
        return True
"""
        
        code_path = tmp_path / "auth_service.py"
        code_path.write_text(code_content)
        
        artifact = self.tracker.analyze_code_file(code_path)
        
        assert artifact.artifact_type == ArtifactType.SOURCE_CODE
        assert artifact.provenance_header is not None
        assert "REQ-AUTH-001" in artifact.provenance_header.requirements
        assert "T-AUTH-001" in artifact.provenance_header.tasks
        assert "REQ-AUTH-001" in artifact.referenced_requirements
    
    def test_determine_artifact_type(self, tmp_path):
        """Test artifact type determination based on file patterns."""
        test_cases = [
            ("test_auth.py", ArtifactType.TEST),
            ("auth.spec.js", ArtifactType.TEST),
            ("config.yaml", ArtifactType.CONFIG),
            ("README.md", ArtifactType.DOCUMENTATION),
            ("service.py", ArtifactType.SOURCE_CODE),
            ("component.tsx", ArtifactType.SOURCE_CODE),
            ("data.json", ArtifactType.CONFIG)
        ]
        
        for filename, expected_type in test_cases:
            file_path = tmp_path / filename
            file_path.write_text("# dummy content")
            
            determined_type = self.tracker._determine_artifact_type(file_path)
            assert determined_type == expected_type
    
    def test_extract_requirement_references(self):
        """Test extraction of requirement references from code."""
        code_content = """
        # This implements REQ-AUTH-001 and REQ-DATA-002
        def process():
            # See REQ-API-003 for details
            pass
        """
        
        refs = self.tracker._extract_requirement_references(code_content)
        
        assert len(refs) == 3
        assert "REQ-AUTH-001" in refs
        assert "REQ-DATA-002" in refs
        assert "REQ-API-003" in refs
    
    def test_extract_task_references(self):
        """Test extraction of task references from code."""
        code_content = """
        # Implements T-AUTH-001
        def authenticate():
            # TODO: Complete T-DATA-001 integration
            pass
        """
        
        refs = self.tracker._extract_task_references(code_content)
        
        assert len(refs) == 2
        assert "T-AUTH-001" in refs
        assert "T-DATA-001" in refs
    
    def test_build_trace_matrix(self, tmp_path):
        """Test building complete traceability matrix."""
        # Create mock files
        src_path = tmp_path / "src"
        test_path = tmp_path / "tests"
        src_path.mkdir()
        test_path.mkdir()
        
        # Source file
        auth_file = src_path / "auth.py"
        auth_file.write_text("""
# REQ-AUTH-001: Authentication service
class AuthService:
    pass
""")
        
        # Test file
        test_file = test_path / "test_auth.py"
        test_file.write_text("""
# Test for auth service
import pytest
from src.auth import AuthService

def test_auth():
    pass
""")
        
        # Update tracker repo path and analyze files
        self.tracker.repo_path = tmp_path
        auth_artifact = self.tracker.analyze_code_file(auth_file)
        test_artifact = self.tracker.analyze_code_file(test_file)
        
        self.tracker.artifacts[str(auth_artifact.file_path)] = auth_artifact
        self.tracker.artifacts[str(test_artifact.file_path)] = test_artifact
        
        # Build trace matrix
        requirements = {"REQ-AUTH-001": "User authentication requirement"}
        tasks = {"T-AUTH-001": "Implement authentication"}
        
        trace_matrix = self.tracker.build_trace_matrix(requirements, tasks)
        
        assert "REQ-AUTH-001" in trace_matrix.requirements_to_code
        assert len(trace_matrix.requirements_to_code["REQ-AUTH-001"]) > 0
    
    def test_detect_drift_orphaned_requirements(self):
        """Test detection of orphaned requirements."""
        # Set up requirements with no implementing code
        requirements = {
            "REQ-MISSING-001": "This requirement has no implementation"
        }
        
        self.tracker.trace_matrix.requirements_to_code = {"REQ-MISSING-001": []}
        
        drift_detections = self.tracker.detect_drift(datetime.now())
        
        orphaned_drifts = [d for d in drift_detections if d.drift_type == DriftType.ORPHANED_REQUIREMENT]
        assert len(orphaned_drifts) > 0
        assert "REQ-MISSING-001" in orphaned_drifts[0].source_artifact
    
    def test_detect_drift_missing_tests(self, tmp_path):
        """Test detection of source files without tests."""
        # Create source file without tests
        src_file = tmp_path / "large_service.py"
        src_file.write_text("# " * 60 + "\n# Large file without tests\nclass Service: pass")
        
        self.tracker.repo_path = tmp_path
        artifact = self.tracker.analyze_code_file(src_file)
        self.tracker.artifacts[str(artifact.file_path)] = artifact
        self.tracker.trace_matrix.code_to_tests = {str(artifact.file_path): []}
        
        drift_detections = self.tracker.detect_drift(datetime.now())
        
        missing_test_drifts = [d for d in drift_detections if d.drift_type == DriftType.MISSING_TESTS]
        assert len(missing_test_drifts) > 0
    
    def test_generate_provenance_header(self):
        """Test generation of provenance headers."""
        header = self.tracker._generate_provenance_header(
            "Test Document",
            ["REQ-001", "REQ-002"],
            ["T-001"]
        )
        
        assert "GENERATED_FROM: Test Document" in header
        assert "REQUIREMENTS: REQ-001, REQ-002" in header
        assert "TASKS: T-001" in header
        assert "GENERATED:" in header
    
    def test_create_traceability_report(self):
        """Test creation of traceability report."""
        # Set up minimal trace matrix
        self.tracker.trace_matrix.requirements_to_code = {
            "REQ-001": [],  # Missing implementation
            "REQ-002": [Mock(target_id="src/impl.py")]  # Has implementation
        }
        
        report = self.tracker.create_traceability_report()
        
        assert "Traceability Report" in report
        assert "REQ-001" in report
        assert "REQ-002" in report
        assert "NOT IMPLEMENTED" in report


class TestProvenanceHeaderExtraction:
    """Test cases for provenance header extraction."""
    
    def setup_method(self):
        """Set up test environment."""
        self.tracker = ProvenanceTracker("/tmp")
    
    def test_extract_complete_provenance_header(self):
        """Test extraction of complete provenance header."""
        content = """#
# GENERATED_FROM: PRD Section 2.1
# REQUIREMENTS: REQ-AUTH-001, REQ-DATA-002
# TASKS: T-AUTH-001, T-DATA-001
# GENERATED: 2024-01-15T10:30:00
#

def main():
    pass
"""
        
        header = self.tracker._extract_provenance_header(content)
        
        assert header is not None
        assert header.generated_from == "PRD Section 2.1"
        assert "REQ-AUTH-001" in header.requirements
        assert "REQ-DATA-002" in header.requirements
        assert "T-AUTH-001" in header.tasks
        assert "T-DATA-001" in header.tasks
        assert header.generation_timestamp is not None
    
    def test_extract_partial_provenance_header(self):
        """Test extraction when only some fields are present."""
        content = """#
# GENERATED_FROM: Manual creation
# REQUIREMENTS: REQ-001
#

def partial():
    pass
"""
        
        header = self.tracker._extract_provenance_header(content)
        
        assert header is not None
        assert header.generated_from == "Manual creation"
        assert "REQ-001" in header.requirements
        assert header.tasks == []
    
    def test_no_provenance_header(self):
        """Test when no provenance header is present."""
        content = """
def regular_function():
    return "no header"
"""
        
        header = self.tracker._extract_provenance_header(content)
        
        assert header is None