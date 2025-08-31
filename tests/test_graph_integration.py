"""
Tests for the graph integration service.
"""

import json
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.llm_council.services.graph_integration import GraphIntegrationService
from src.llm_council.models.se_models import SystemsEntity, ImplementationTask, ArchitecturalComponent
from src.llm_council.models.code_artifact_models import TraceabilityType, ArtifactType


class TestGraphIntegrationService:
    """Test cases for GraphIntegrationService."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = GraphIntegrationService(self.temp_dir)
    
    def test_build_complete_traceability_graph(self, tmp_path):
        """Test building complete traceability graph."""
        # Create mock documents
        prd_path = tmp_path / "PRD.md"
        prd_path.write_text("""
        ## REQ-AUTH-001: User Authentication
        The system must support user login
        
        ## REQ-DATA-001: Data Storage  
        Store user data securely
        """)
        
        impl_path = tmp_path / "IMPLEMENTATION.md"
        impl_path.write_text("""
        ## T-AUTH-001: Implement Login
        Create login functionality
        
        ## T-DATA-001: Database Setup
        Set up user database
        """)
        
        arch_path = tmp_path / "ARCHITECTURE.md"
        arch_path.write_text("""
        ## Authentication Component
        Handles user authentication
        
        ## Data Component
        Manages data persistence
        """)
        
        # Mock the repository structure building
        with patch.object(self.service.provenance_tracker, 'build_repository_structure') as mock_build:
            mock_structure = Mock()
            mock_build.return_value = mock_structure
            
            with patch.object(self.service.provenance_tracker, 'build_trace_matrix') as mock_trace:
                mock_matrix = Mock()
                mock_trace.return_value = mock_matrix
                
                trace_matrix, repo_structure = self.service.build_complete_traceability_graph(
                    str(prd_path), str(impl_path), str(arch_path)
                )
        
        assert trace_matrix == mock_matrix
        assert repo_structure == mock_structure
    
    def test_generate_implementation_from_se_pipeline(self):
        """Test generating implementation from SE pipeline artifacts."""
        entities = [
            Mock(name="User Entity", description="User data model")
        ]
        
        tasks = [
            Mock(
                task_id="T-AUTH-001",
                description="Implement authentication service",
                priority="high"
            )
        ]
        
        components = [
            Mock(
                name="Auth Service",
                description="Authentication component",
                technologies=["Python", "FastAPI"]
            )
        ]
        
        requirements = {
            "REQ-AUTH-001": "User authentication requirement"
        }
        
        # Mock the code generation methods
        with patch.object(self.service.codegen_engine, 'generate_component_stubs') as mock_comp:
            mock_comp.return_value = [("src/auth.py", "# Auth component")]
            
            with patch.object(self.service.codegen_engine, 'generate_implementation_stubs') as mock_impl:
                mock_impl.return_value = [("src/auth_impl.py", "# Auth implementation")]
                
                with patch.object(self.service.codegen_engine, 'generate_requirements_traceability_matrix') as mock_matrix:
                    mock_matrix.return_value = "# Traceability Matrix"
                    
                    files = self.service.generate_implementation_from_se_pipeline(
                        entities, tasks, components, requirements
                    )
        
        assert len(files) >= 3  # Component + task + matrix
        
        # Check that traceability matrix is included
        matrix_files = [f for f, c in files if "TRACEABILITY_MATRIX.md" in f]
        assert len(matrix_files) == 1
    
    def test_validate_implementation_completeness(self):
        """Test validation of implementation completeness."""
        requirements = {
            "REQ-AUTH-001": "Authentication requirement",
            "REQ-DATA-001": "Data storage requirement"
        }
        
        tasks = [
            Mock(task_id="T-AUTH-001", description="Auth task"),
            Mock(task_id="T-DATA-001", description="Data task")
        ]
        
        # Mock artifacts with partial implementation
        mock_artifact = Mock()
        mock_artifact.artifact_type = ArtifactType.SOURCE_CODE
        mock_artifact.referenced_requirements = ["REQ-AUTH-001"]  # Only one requirement
        mock_artifact.referenced_tasks = ["T-AUTH-001"]  # Only one task
        mock_artifact.file_path = "src/auth.py"
        
        self.service.provenance_tracker.artifacts = {"src/auth.py": mock_artifact}
        self.service.provenance_tracker.trace_matrix.code_to_tests = {"src/auth.py": []}
        
        validation = self.service.validate_implementation_completeness(requirements, tasks)
        
        assert validation['coverage_percentage'] == 50.0  # 1 of 2 requirements
        assert "REQ-DATA-001" in validation['missing_requirements']
        assert "T-DATA-001" in validation['missing_tasks']
        assert "src/auth.py" in validation['test_coverage_gaps']
    
    def test_generate_end_to_end_trace(self):
        """Test generation of end-to-end trace from requirement to tests."""
        # Set up mock trace matrix
        trace_matrix = Mock()
        trace_matrix.requirements_to_code = {
            "REQ-AUTH-001": [
                Mock(target_id="src/auth.py", relationship_type=TraceabilityType.IMPLEMENTS)
            ]
        }
        trace_matrix.code_to_tests = {
            "src/auth.py": [
                Mock(target_id="tests/test_auth.py", relationship_type=TraceabilityType.TESTED_BY)
            ]
        }
        trace_matrix.tests_to_schemas = {
            "tests/test_auth.py": [
                Mock(target_id="schemas/auth.py", relationship_type=TraceabilityType.VALIDATES)
            ]
        }
        
        trace = self.service.generate_end_to_end_trace("REQ-AUTH-001", trace_matrix)
        
        assert trace['requirement'] == "REQ-AUTH-001"
        assert "src/auth.py" in trace['implementing_code']
        assert "tests/test_auth.py" in trace['test_files']
        assert "schemas/auth.py" in trace['schema_files']
    
    def test_create_impact_analysis(self):
        """Test impact analysis for code changes."""
        changed_files = ["src/auth.py"]
        
        # Mock trace matrix with relationships
        trace_matrix = Mock()
        trace_matrix.requirements_to_code = {
            "REQ-AUTH-001": [Mock(target_id="src/auth.py")]
        }
        trace_matrix.code_to_tests = {
            "src/auth.py": [Mock(target_id="tests/test_auth.py")]
        }
        
        impact = self.service.create_impact_analysis(changed_files, trace_matrix)
        
        assert "REQ-AUTH-001" in impact['affected_requirements']
        assert "tests/test_auth.py" in impact['affected_tests']
        assert len(impact['recommended_actions']) > 0
        assert any("Run tests" in action for action in impact['recommended_actions'])
    
    def test_generate_provenance_report(self):
        """Test generation of comprehensive provenance report."""
        requirements = {
            "REQ-AUTH-001": "Authentication requirement"
        }
        
        tasks = [
            Mock(
                task_id="T-AUTH-001",
                description="Implement authentication",
                priority="high"
            )
        ]
        
        # Mock validation results
        with patch.object(self.service, 'validate_implementation_completeness') as mock_validate:
            mock_validate.return_value = {
                'coverage_percentage': 75.0,
                'missing_requirements': [],
                'missing_tasks': [],
                'orphaned_code': [],
                'test_coverage_gaps': []
            }
            
            # Mock artifacts
            mock_artifact = Mock()
            mock_artifact.file_path = "src/auth.py"
            mock_artifact.lines_of_code = 150
            mock_artifact.referenced_requirements = ["REQ-AUTH-001"]
            mock_artifact.referenced_tasks = ["T-AUTH-001"]
            
            self.service.provenance_tracker.artifacts = {"src/auth.py": mock_artifact}
            
            report = self.service.generate_provenance_report(requirements, tasks)
        
        assert "Provenance & Traceability Report" in report
        assert "Implementation Completeness" in report
        assert "75.0%" in report
        assert "REQ-AUTH-001" in report
        assert "T-AUTH-001" in report
    
    def test_export_graph_data(self, tmp_path):
        """Test exporting graph data for visualization."""
        # Mock the required methods
        with patch.object(self.service.provenance_tracker, 'save_trace_matrix'):
            with patch.object(self.service.provenance_tracker, 'build_repository_structure') as mock_build:
                mock_structure = Mock()
                mock_structure.dict.return_value = {"total_files": 10}
                mock_build.return_value = mock_structure
                
                # Set up mock artifacts
                self.service.provenance_tracker.artifacts = {
                    "src/test.py": Mock(dict=lambda: {"file_path": "src/test.py"})
                }
                
                output_dir = str(tmp_path / "export")
                exported = self.service.export_graph_data(output_dir)
        
        assert 'trace_matrix' in exported
        assert 'repository_structure' in exported
        assert 'artifacts_catalog' in exported
        
        # Check that export directory was created
        assert Path(output_dir).exists()
    
    def test_sync_with_se_pipeline(self):
        """Test synchronization with SE pipeline updates."""
        se_output = {
            'requirements': {
                "REQ-NEW-001": "New requirement from SE pipeline"
            },
            'deprecated_entities': ["Old Component"]
        }
        
        # Mock current artifacts
        mock_artifact = Mock()
        mock_artifact.referenced_requirements = ["REQ-OLD-001"]
        self.service.provenance_tracker.artifacts = {"src/old.py": mock_artifact}
        
        # Mock find component files for obsolete detection
        with patch.object(self.service.codegen_engine, '_find_component_files') as mock_find:
            mock_find.return_value = ["src/old_component.py"]
            
            sync_results = self.service.sync_with_se_pipeline(se_output)
        
        assert "REQ-NEW-001" in sync_results['new_requirements']
        assert "src/old_component.py" in sync_results['obsolete_code']
        assert 'sync_timestamp' in sync_results


class TestIntegrationWorkflow:
    """Test cases for complete integration workflow."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = GraphIntegrationService(self.temp_dir)
    
    def test_end_to_end_integration_workflow(self, tmp_path):
        """Test complete end-to-end integration workflow."""
        # Create test documents
        prd_path = tmp_path / "PRD.md"
        prd_path.write_text("## REQ-AUTH-001: User Authentication\nImplement user login")
        
        impl_path = tmp_path / "IMPLEMENTATION.md"  
        impl_path.write_text("## T-AUTH-001: Login Implementation\nCreate login service")
        
        arch_path = tmp_path / "ARCHITECTURE.md"
        arch_path.write_text("## Authentication Component\nHandles user auth")
        
        # Create mock source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        auth_file = src_dir / "auth.py"
        auth_file.write_text("""
# REQ-AUTH-001: Authentication implementation
# T-AUTH-001: Login service
class AuthService:
    def login(self): pass
""")
        
        # Update service repo path
        self.service.repo_path = tmp_path
        self.service.provenance_tracker.repo_path = tmp_path
        
        # Run complete workflow
        trace_matrix, repo_structure = self.service.build_complete_traceability_graph(
            str(prd_path), str(impl_path), str(arch_path)
        )
        
        assert trace_matrix is not None
        assert repo_structure is not None
        assert repo_structure.total_files >= 1
        
        # Validate that requirements were found
        requirements = self.service.provenance_tracker.extract_requirements_from_prd(str(prd_path))
        assert "REQ-AUTH-001" in requirements
        
        # Test validation
        tasks = [Mock(task_id="T-AUTH-001", description="Login task")]
        validation = self.service.validate_implementation_completeness(requirements, tasks)
        assert 'coverage_percentage' in validation