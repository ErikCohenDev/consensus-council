"""
Tests for the code generation engine.
"""

import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from src.llm_council.services.codegen_engine import CodeGenEngine
from src.llm_council.models.se_models import ImplementationTask, ArchitecturalComponent


class TestCodeGenEngine:
    """Test cases for CodeGenEngine."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.engine = CodeGenEngine(self.temp_dir)
    
    def test_generate_provenance_header(self):
        """Test generation of provenance headers."""
        header = self.engine._generate_provenance_header(
            "Test Source",
            ["REQ-001", "REQ-002"],
            ["T-001"]
        )
        
        assert "GENERATED_FROM: Test Source" in header
        assert "REQUIREMENTS: REQ-001, REQ-002" in header
        assert "TASKS: T-001" in header
        assert "GENERATED:" in header
    
    def test_infer_language_from_task(self):
        """Test language inference from task descriptions."""
        python_task = Mock()
        python_task.description = "Implement Python FastAPI endpoint"
        
        js_task = Mock()
        js_task.description = "Create JavaScript React component"
        
        ts_task = Mock()
        ts_task.description = "Build TypeScript service class"
        
        assert self.engine._infer_language_from_task(python_task) == "python"
        assert self.engine._infer_language_from_task(js_task) == "javascript"
        assert self.engine._infer_language_from_task(ts_task) == "typescript"
    
    def test_generate_file_paths_for_task(self):
        """Test file path generation for implementation tasks."""
        task = Mock()
        task.task_id = "T-AUTH-001"
        task.description = "Implement authentication service"
        
        paths = self.engine._generate_file_paths_for_task(task, "python")
        
        assert len(paths) > 0
        file_path, stub_type = paths[0]
        assert "t_auth_001" in file_path
        assert file_path.endswith(".py")
    
    def test_python_class_template(self):
        """Test Python class template generation."""
        component = Mock()
        component.name = "Auth Service"
        component.description = "Authentication service component"
        
        header = "# Test header\n"
        
        code = self.engine._python_class_template(component, [], header)
        
        assert "class AuthService:" in code
        assert "Authentication service component" in code
        assert header in code
        assert "TODO: Initialize AuthService" in code
    
    def test_typescript_class_template(self):
        """Test TypeScript class template generation."""
        component = Mock()
        component.name = "Data Processor"
        component.description = "Data processing component"
        
        header = "// Test header\n"
        
        code = self.engine._ts_class_template(component, [], header)
        
        assert "export class DataProcessor" in code
        assert "DataProcessorConfig" in code
        assert "Data processing component" in code
        assert "Implementation required" in code
    
    def test_generate_implementation_stubs(self):
        """Test generation of implementation stubs for tasks."""
        tasks = [
            Mock(
                task_id="T-AUTH-001",
                description="Implement user authentication",
                priority="high"
            ),
            Mock(
                task_id="T-DATA-001", 
                description="Create data models",
                priority="medium"
            )
        ]
        
        components = []
        requirements = {
            "REQ-AUTH-001": "User authentication requirement"
        }
        
        # Mock the requirement finding to return specific results
        with patch.object(self.engine, '_find_related_requirements', return_value=["REQ-AUTH-001"]):
            stubs = self.engine.generate_implementation_stubs(tasks, components, requirements)
        
        assert len(stubs) >= 2  # At least one stub per task
        
        # Check that provenance headers are included
        for file_path, content in stubs:
            assert "GENERATED_FROM:" in content
            assert "T-AUTH-001" in content or "T-DATA-001" in content
    
    def test_generate_component_stubs(self):
        """Test generation of component stubs."""
        components = [
            Mock(
                name="Authentication Service",
                description="Handles user authentication",
                technologies=["Python", "FastAPI"],
                interfaces=[]
            )
        ]
        
        requirements = {
            "REQ-AUTH-001": "Authentication requirement"
        }
        
        stubs = self.engine.generate_component_stubs(components, requirements)
        
        assert len(stubs) >= 2  # Main file + test file
        
        # Check main component file
        main_files = [f for f, c in stubs if not 'test' in f]
        assert len(main_files) > 0
        
        main_path, main_content = [(f, c) for f, c in stubs if not 'test' in f][0]
        assert "class AuthenticationService" in main_content or "AuthenticationService" in main_content
        assert "GENERATED_FROM:" in main_content
    
    def test_find_related_requirements(self):
        """Test finding requirements related to implementation tasks."""
        task = Mock()
        task.description = "implement user authentication with oauth2 provider"
        
        requirements = {
            "REQ-AUTH-001": "user authentication system with oauth2 support",
            "REQ-DATA-001": "data storage and persistence layer",
            "REQ-UI-001": "user interface design guidelines"
        }
        
        related = self.engine._find_related_requirements(task, requirements)
        
        # Should find REQ-AUTH-001 due to keyword overlap
        assert "REQ-AUTH-001" in related
        # Should not find REQ-UI-001 due to lack of keyword overlap
        assert "REQ-UI-001" not in related
    
    def test_extract_keywords(self):
        """Test keyword extraction from text."""
        text = "implement user authentication with oauth2 provider and database"
        
        keywords = self.engine._extract_keywords(text)
        
        # Should include meaningful keywords
        assert "implement" in keywords
        assert "user" in keywords
        assert "authentication" in keywords
        assert "oauth2" in keywords
        assert "provider" in keywords
        assert "database" in keywords
        
        # Should exclude common words
        assert "and" not in keywords
        assert "with" not in keywords
    
    def test_generate_requirements_traceability_matrix(self):
        """Test generation of requirements traceability matrix."""
        requirements = {
            "REQ-AUTH-001": "User authentication requirement",
            "REQ-DATA-001": "Data storage requirement"
        }
        
        generated_files = [
            ("src/auth.py", "# REQ-AUTH-001: Implementation\nclass Auth: pass"),
            ("tests/test_auth.py", "# Test for REQ-AUTH-001\ndef test_auth(): pass"),
            ("src/data.py", "# REQ-DATA-001: Implementation\nclass Data: pass")
        ]
        
        matrix = self.engine.generate_requirements_traceability_matrix(requirements, generated_files)
        
        assert "Requirements Traceability Matrix" in matrix
        assert "REQ-AUTH-001" in matrix
        assert "REQ-DATA-001" in matrix
        assert "src/auth.py" in matrix
        assert "tests/test_auth.py" in matrix
    
    def test_write_generated_files_dry_run(self, capsys):
        """Test dry run mode for file writing."""
        generated_files = [
            ("src/test.py", "# Test content"),
            ("tests/test_test.py", "# Test content")
        ]
        
        written = self.engine.write_generated_files(generated_files, dry_run=True)
        
        # Should not write files in dry run
        assert len(written) == 0
        
        # Should print what would be created
        captured = capsys.readouterr()
        assert "Would create: src/test.py" in captured.out
        assert "Would create: tests/test_test.py" in captured.out


class TestLanguageTemplates:
    """Test cases for language-specific templates."""
    
    def setup_method(self):
        """Set up test environment."""
        self.engine = CodeGenEngine("/tmp")
    
    def test_python_function_template(self):
        """Test Python function template."""
        task = Mock()
        task.task_id = "T-CALC-001"
        task.description = "Calculate user metrics"
        
        header = "# Header\n"
        
        code = self.engine._python_function_template(task, [], header)
        
        assert "def t_calc_001():" in code
        assert "Calculate user metrics" in code
        assert "NotImplementedError" in code
        assert header in code
    
    def test_python_test_template(self):
        """Test Python test template."""
        component = Mock()
        component.name = "Calculator"
        component.description = "Math calculator component"
        
        header = "# Header\n"
        
        code = self.engine._python_test_template(component, [], header)
        
        assert "class TestCalculator:" in code
        assert "test_basic_functionality" in code
        assert "test_error_handling" in code
        assert "test_edge_cases" in code
        assert header in code
    
    def test_typescript_module_template(self):
        """Test TypeScript module template."""
        task = Mock()
        task.task_id = "T-API-001"
        task.description = "API client implementation"
        
        header = "// Header\n"
        
        code = self.engine._ts_module_template(task, [], header)
        
        assert "API client implementation" in code
        assert "T-API-001" in code
        assert "export const config" in code
        assert "export default" in code
        assert header.replace('#', '//') in code