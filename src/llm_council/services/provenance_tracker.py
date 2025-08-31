"""Complete provenance tracking system for idea-to-code traceability."""

from __future__ import annotations

import ast
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from ..database.neo4j_client import Neo4jClient
from ..models.se_models import (
    CodeArtifact,
    Service,
    Module, 
    Class,
    Function,
    Test,
    TraceabilityLink,
    ProvenanceHeader
)

logger = logging.getLogger(__name__)

class CodeScanner:
    """Scans codebase to build artifact graph with provenance tracking."""
    
    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j = neo4j_client
        self.supported_extensions = {'.py', '.ts', '.tsx', '.js', '.jsx', '.go', '.java'}
        self.artifact_cache = {}
    
    def scan_codebase(self, root_path: str) -> Dict[str, Any]:
        """Scan entire codebase and build artifact graph."""
        
        logger.info(f"Starting codebase scan of {root_path}")
        
        scan_results = {
            "services": {},
            "modules": {},
            "classes": {},
            "functions": {},
            "tests": {},
            "dependencies": [],
            "orphan_files": [],
            "total_files": 0,
            "scanned_files": 0
        }
        
        root = Path(root_path)
        
        # Walk through all files
        for file_path in root.rglob("*"):
            if not file_path.is_file() or file_path.suffix not in self.supported_extensions:
                continue
            
            scan_results["total_files"] += 1
            
            try:
                artifacts = self._scan_single_file(file_path)
                
                # Categorize artifacts
                for artifact in artifacts:
                    if artifact["type"] == "Service":
                        scan_results["services"][artifact["id"]] = artifact
                    elif artifact["type"] == "Module":
                        scan_results["modules"][artifact["id"]] = artifact
                    elif artifact["type"] == "Class":
                        scan_results["classes"][artifact["id"]] = artifact
                    elif artifact["type"] == "Function":
                        scan_results["functions"][artifact["id"]] = artifact
                    elif artifact["type"] == "Test":
                        scan_results["tests"][artifact["id"]] = artifact
                
                scan_results["scanned_files"] += 1
                
            except Exception as e:
                logger.error(f"Failed to scan {file_path}: {e}")
                scan_results["orphan_files"].append(str(file_path))
        
        # Extract dependencies
        scan_results["dependencies"] = self._extract_dependencies(scan_results)
        
        logger.info(f"Scan complete: {scan_results['scanned_files']}/{scan_results['total_files']} files processed")
        
        return scan_results
    
    def _scan_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a single file and extract all artifacts."""
        
        artifacts = []
        file_content = file_path.read_text(encoding='utf-8')
        
        # Extract provenance header if present
        provenance_header = self._extract_provenance_header(file_content)
        
        if file_path.suffix == '.py':
            artifacts = self._scan_python_file(file_path, file_content, provenance_header)
        elif file_path.suffix in {'.ts', '.tsx', '.js', '.jsx'}:
            artifacts = self._scan_typescript_file(file_path, file_content, provenance_header)
        elif file_path.suffix == '.go':
            artifacts = self._scan_go_file(file_path, file_content, provenance_header)
        
        return artifacts
    
    def _extract_provenance_header(self, file_content: str) -> Optional[Dict[str, Any]]:
        """Extract provenance header from file content."""
        
        # Look for comment block at top of file
        header_patterns = [
            # Python/TypeScript style
            r'/\*\n \* ([^\n]+)\n \* Implements: ([^\n]+)\n \* VerifiedBy: ([^\n]*)\n \* Generated: ([^\n]*)\n \* Provenance: ([^\n]*)\n \*/',
            # Python docstring style  
            r'"""\n([^\n]+)\nImplements: ([^\n]+)\nVerifiedBy: ([^\n]*)\nGenerated: ([^\n]*)\nProvenance: ([^\n]*)\n"""',
        ]
        
        for pattern in header_patterns:
            match = re.search(pattern, file_content, re.MULTILINE)
            if match:
                return {
                    "name": match.group(1).strip(),
                    "implements": [id.strip() for id in match.group(2).split(',') if id.strip()],
                    "verified_by": [id.strip() for id in match.group(3).split(',') if id.strip()],
                    "generated": match.group(4).strip(),
                    "provenance": match.group(5).strip()
                }
        
        return None
    
    def _scan_python_file(
        self, 
        file_path: Path, 
        content: str, 
        provenance_header: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Scan Python file using AST parsing."""
        
        artifacts = []
        
        try:
            tree = ast.parse(content)
            
            # Check if this is a service (contains FastAPI app, Flask app, or main function)
            is_service = self._is_python_service_file(tree)
            
            if is_service:
                service_artifact = {
                    "type": "Service",
                    "id": f"SVC-{file_path.stem.upper()}",
                    "name": file_path.stem.replace('_', ' ').title(),
                    "file_path": str(file_path),
                    "implements": provenance_header["implements"] if provenance_header else [],
                    "verified_by": provenance_header["verified_by"] if provenance_header else [],
                    "complexity": self._calculate_complexity(tree),
                    "lines_of_code": len(content.splitlines()),
                    "stage": "mvp",
                    "status": "implemented"
                }
                artifacts.append(service_artifact)
            
            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_artifact = {
                        "type": "Class",
                        "id": f"CLS-{file_path.stem}-{node.name}",
                        "name": node.name,
                        "file_path": str(file_path),
                        "parent_id": f"SVC-{file_path.stem.upper()}" if is_service else f"MOD-{file_path.stem}",
                        "implements": self._extract_class_requirements(node),
                        "complexity": self._calculate_class_complexity(node),
                        "lines_of_code": node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 10,
                        "stage": "mvp",
                        "status": "implemented"
                    }
                    artifacts.append(class_artifact)
                    
                    # Extract methods as functions
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef):
                            function_artifact = {
                                "type": "Function", 
                                "id": f"FN-{file_path.stem}-{node.name}-{method.name}",
                                "name": f"{node.name}.{method.name}",
                                "file_path": str(file_path),
                                "parent_id": class_artifact["id"],
                                "implements": self._extract_function_requirements(method),
                                "complexity": self._calculate_function_complexity(method),
                                "lines_of_code": method.end_lineno - method.lineno if hasattr(method, 'end_lineno') else 5,
                                "stage": "mvp",
                                "status": "implemented"
                            }
                            artifacts.append(function_artifact)
                
                elif isinstance(node, ast.FunctionDef) and not self._is_method(node, tree):
                    # Top-level function
                    function_artifact = {
                        "type": "Function",
                        "id": f"FN-{file_path.stem}-{node.name}",
                        "name": node.name,
                        "file_path": str(file_path),
                        "parent_id": f"SVC-{file_path.stem.upper()}" if is_service else f"MOD-{file_path.stem}",
                        "implements": self._extract_function_requirements(node),
                        "complexity": self._calculate_function_complexity(node),
                        "lines_of_code": node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 5,
                        "stage": "mvp",
                        "status": "implemented"
                    }
                    artifacts.append(function_artifact)
            
            # Check if this is a test file
            if self._is_test_file(file_path):
                test_functions = [a for a in artifacts if a["type"] == "Function" and a["name"].startswith(("test_", "test"))]
                for test_func in test_functions:
                    test_func["type"] = "Test"
                    test_func["test_type"] = self._determine_test_type(test_func["name"])
                    test_func["covers"] = self._extract_test_coverage(test_func["name"])
        
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
        
        return artifacts
    
    def _scan_typescript_file(
        self, 
        file_path: Path, 
        content: str, 
        provenance_header: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Scan TypeScript/JavaScript file using regex patterns."""
        
        artifacts = []
        
        # Check if this is a service (contains Express app, Fastify, or server setup)
        is_service = self._is_typescript_service_file(content)
        
        if is_service:
            service_artifact = {
                "type": "Service",
                "id": f"SVC-{file_path.stem.upper()}",
                "name": file_path.stem.replace('_', ' ').replace('-', ' ').title(),
                "file_path": str(file_path),
                "implements": provenance_header["implements"] if provenance_header else [],
                "verified_by": provenance_header["verified_by"] if provenance_header else [],
                "complexity": self._calculate_ts_complexity(content),
                "lines_of_code": len(content.splitlines()),
                "stage": "mvp", 
                "status": "implemented"
            }
            artifacts.append(service_artifact)
        
        # Extract classes
        class_pattern = r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*{'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            class_name = match.group(1)
            class_artifact = {
                "type": "Class",
                "id": f"CLS-{file_path.stem}-{class_name}",
                "name": class_name,
                "file_path": str(file_path),
                "parent_id": f"SVC-{file_path.stem.upper()}" if is_service else f"MOD-{file_path.stem}",
                "implements": [],
                "complexity": 5,  # Simplified
                "lines_of_code": 50,  # Simplified
                "stage": "mvp",
                "status": "implemented"
            }
            artifacts.append(class_artifact)
        
        # Extract functions
        function_patterns = [
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(',
            r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
            r'(\w+)\s*:\s*\([^)]*\)\s*=>\s*{',
        ]
        
        for pattern in function_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                func_name = match.group(1)
                if func_name in ['if', 'for', 'while', 'switch']:  # Skip keywords
                    continue
                
                function_artifact = {
                    "type": "Function",
                    "id": f"FN-{file_path.stem}-{func_name}",
                    "name": func_name,
                    "file_path": str(file_path),
                    "parent_id": f"SVC-{file_path.stem.upper()}" if is_service else f"MOD-{file_path.stem}",
                    "implements": [],
                    "complexity": 3,  # Simplified
                    "lines_of_code": 20,  # Simplified
                    "stage": "mvp",
                    "status": "implemented"
                }
                artifacts.append(function_artifact)
        
        # Check if this is a test file
        if self._is_test_file(file_path):
            test_functions = [a for a in artifacts if a["type"] == "Function" and 
                           any(keyword in a["name"].lower() for keyword in ["test", "spec", "describe", "it"])]
            for test_func in test_functions:
                test_func["type"] = "Test"
                test_func["test_type"] = self._determine_test_type(test_func["name"])
                test_func["covers"] = self._extract_test_coverage(test_func["name"])
        
        return artifacts
    
    def _scan_go_file(
        self,
        file_path: Path,
        content: str,
        provenance_header: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Scan Go file using regex patterns."""
        
        artifacts = []
        
        # Check if this is a service (contains main function or server setup)
        is_service = 'func main(' in content or 'http.ListenAndServe' in content
        
        if is_service:
            service_artifact = {
                "type": "Service",
                "id": f"SVC-{file_path.stem.upper()}",
                "name": file_path.stem.replace('_', ' ').title(),
                "file_path": str(file_path),
                "implements": provenance_header["implements"] if provenance_header else [],
                "verified_by": provenance_header["verified_by"] if provenance_header else [],
                "complexity": self._calculate_go_complexity(content),
                "lines_of_code": len(content.splitlines()),
                "stage": "mvp",
                "status": "implemented"
            }
            artifacts.append(service_artifact)
        
        # Extract structs (similar to classes)
        struct_pattern = r'type\s+(\w+)\s+struct\s*{'
        for match in re.finditer(struct_pattern, content, re.MULTILINE):
            struct_name = match.group(1)
            class_artifact = {
                "type": "Class",
                "id": f"CLS-{file_path.stem}-{struct_name}",
                "name": struct_name,
                "file_path": str(file_path),
                "parent_id": f"SVC-{file_path.stem.upper()}" if is_service else f"MOD-{file_path.stem}",
                "implements": [],
                "complexity": 3,
                "lines_of_code": 30,
                "stage": "mvp", 
                "status": "implemented"
            }
            artifacts.append(class_artifact)
        
        # Extract functions
        func_pattern = r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\([^)]*\)(?:\s*\([^)]*\))?\s*{'
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            func_name = match.group(1)
            function_artifact = {
                "type": "Function",
                "id": f"FN-{file_path.stem}-{func_name}",
                "name": func_name,
                "file_path": str(file_path),
                "parent_id": f"SVC-{file_path.stem.upper()}" if is_service else f"MOD-{file_path.stem}",
                "implements": [],
                "complexity": 4,
                "lines_of_code": 25,
                "stage": "mvp",
                "status": "implemented"
            }
            artifacts.append(function_artifact)
        
        return artifacts
    
    def _is_python_service_file(self, tree: ast.AST) -> bool:
        """Determine if Python file contains a service."""
        service_indicators = ['FastAPI', 'Flask', 'app', 'main', 'server', 'uvicorn']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in service_indicators:
                return True
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in service_indicators:
                        return True
        
        return False
    
    def _is_typescript_service_file(self, content: str) -> bool:
        """Determine if TypeScript file contains a service."""
        service_indicators = ['express', 'fastify', 'server', 'app.listen', 'createServer']
        return any(indicator in content for indicator in service_indicators)
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Determine if file is a test file."""
        test_indicators = ['test', 'spec', '__test__', '.test.', '.spec.']
        return any(indicator in str(file_path).lower() for indicator in test_indicators)
    
    def _is_method(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Check if function is a method inside a class."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef) and node in parent.body:
                return True
        return False
    
    def _extract_class_requirements(self, node: ast.ClassDef) -> List[str]:
        """Extract requirement IDs from class docstring or comments."""
        requirements = []
        
        if ast.get_docstring(node):
            docstring = ast.get_docstring(node)
            req_pattern = r'REQ-\d{3}'
            requirements.extend(re.findall(req_pattern, docstring))
        
        return requirements
    
    def _extract_function_requirements(self, node: ast.FunctionDef) -> List[str]:
        """Extract requirement IDs from function docstring or comments."""
        requirements = []
        
        if ast.get_docstring(node):
            docstring = ast.get_docstring(node)
            req_pattern = r'REQ-\d{3}'
            requirements.extend(re.findall(req_pattern, docstring))
        
        return requirements
    
    def _determine_test_type(self, test_name: str) -> str:
        """Determine test type based on naming conventions."""
        if any(keyword in test_name.lower() for keyword in ['integration', 'e2e', 'end_to_end']):
            return 'integration'
        elif any(keyword in test_name.lower() for keyword in ['unit', 'test_']):
            return 'unit'
        elif any(keyword in test_name.lower() for keyword in ['perf', 'performance', 'load']):
            return 'performance'
        else:
            return 'unit'
    
    def _extract_test_coverage(self, test_name: str) -> List[str]:
        """Extract what requirements this test covers."""
        # Simplified - in practice, would parse test content
        coverage = []
        req_pattern = r'REQ-\d{3}'
        coverage.extend(re.findall(req_pattern, test_name))
        return coverage
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of Python AST."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return min(complexity, 20)  # Cap at 20
    
    def _calculate_class_complexity(self, node: ast.ClassDef) -> int:
        """Calculate complexity of a class."""
        complexity = 1
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                complexity += self._calculate_function_complexity(item)
        return min(complexity, 50)
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
        return min(complexity, 15)
    
    def _calculate_ts_complexity(self, content: str) -> int:
        """Calculate TypeScript complexity using regex."""
        complexity = 1
        complexity += len(re.findall(r'\bif\s*\(', content))
        complexity += len(re.findall(r'\bfor\s*\(', content))
        complexity += len(re.findall(r'\bwhile\s*\(', content))
        complexity += len(re.findall(r'\bcatch\s*\(', content))
        return min(complexity, 20)
    
    def _calculate_go_complexity(self, content: str) -> int:
        """Calculate Go complexity using regex."""
        complexity = 1
        complexity += len(re.findall(r'\bif\s+', content))
        complexity += len(re.findall(r'\bfor\s+', content))
        complexity += len(re.findall(r'\bswitch\s+', content))
        return min(complexity, 20)
    
    def _extract_dependencies(self, scan_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract dependencies between artifacts."""
        dependencies = []
        
        # For now, create simple parent-child dependencies
        for artifact_type in ['classes', 'functions']:
            for artifact_id, artifact in scan_results[artifact_type].items():
                if artifact.get('parent_id'):
                    dependencies.append({
                        "from": artifact['parent_id'],
                        "to": artifact_id,
                        "type": "contains"
                    })
        
        return dependencies

class ProvenanceTracker:
    """Tracks complete provenance from requirements to code artifacts."""
    
    def __init__(self, neo4j_client: Neo4jClient, code_scanner: CodeScanner):
        self.neo4j = neo4j_client
        self.scanner = code_scanner
    
    def generate_provenance_header(
        self,
        artifact_name: str,
        artifact_type: str,
        requirements: List[str],
        tests: List[str],
        generation_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate standardized provenance header."""
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d")
        
        implements_str = ", ".join(requirements) if requirements else "None"
        verified_str = ", ".join(tests) if tests else "TBD"
        
        generation_str = "Manual"
        if generation_info:
            tool = generation_info.get("tool", "Unknown")
            version = generation_info.get("version", "1.0")
            generation_str = f"{tool}@{version}"
        
        # Find provenance chain
        provenance_chain = self._build_provenance_chain(requirements)
        
        if artifact_type in ["Service", "Module"]:
            header_template = f'''/*
 * {artifact_name}
 * Implements: {implements_str}
 * VerifiedBy: {verified_str}
 * Generated: {timestamp} by {generation_str}
 * Provenance: {provenance_chain}
 */'''
        else:  # For Python files
            header_template = f'''"""
{artifact_name}
Implements: {implements_str}
VerifiedBy: {verified_str}
Generated: {timestamp} by {generation_str}
Provenance: {provenance_chain}
"""'''
        
        return header_template
    
    def _build_provenance_chain(self, requirements: List[str]) -> str:
        """Build provenance chain from requirement back to original idea."""
        
        if not requirements:
            return "Unknown"
        
        # Get provenance from Neo4j for first requirement
        query = """
        MATCH (r:Requirement {id: $req_id})-[:DERIVES_FROM]->(p:Problem)<-[:CONTAINS]-(i:Idea)
        RETURN i.id as idea_id, p.statement as problem, r.description as requirement
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(query, {"req_id": requirements[0]})
            record = result.single()
            
            if record:
                return f"Idea({record['idea_id']}) -> Problem({record['problem'][:30]}...) -> Requirement({requirements[0]})"
            else:
                return f"Requirement({requirements[0]})"
    
    def validate_provenance_headers(self, root_path: str) -> Dict[str, Any]:
        """Validate that all code files have proper provenance headers."""
        
        validation_report = {
            "total_files": 0,
            "files_with_headers": 0,
            "files_without_headers": [],
            "invalid_headers": [],
            "orphan_artifacts": [],
            "coverage_rate": 0.0
        }
        
        root = Path(root_path)
        
        for file_path in root.rglob("*"):
            if not file_path.is_file() or file_path.suffix not in self.scanner.supported_extensions:
                continue
            
            # Skip test files and generated files
            if any(skip in str(file_path) for skip in ['test', '__pycache__', 'node_modules', '.git']):
                continue
            
            validation_report["total_files"] += 1
            
            try:
                content = file_path.read_text(encoding='utf-8')
                header = self.scanner._extract_provenance_header(content)
                
                if header:
                    validation_report["files_with_headers"] += 1
                    
                    # Validate header completeness
                    if not header.get("implements") or not header["implements"][0]:
                        validation_report["orphan_artifacts"].append({
                            "file": str(file_path),
                            "reason": "No requirement links"
                        })
                    
                    # Check if requirements exist in Neo4j
                    for req_id in header.get("implements", []):
                        if not self._requirement_exists(req_id):
                            validation_report["invalid_headers"].append({
                                "file": str(file_path),
                                "reason": f"Invalid requirement ID: {req_id}"
                            })
                else:
                    validation_report["files_without_headers"].append(str(file_path))
            
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                validation_report["invalid_headers"].append({
                    "file": str(file_path),
                    "reason": f"Read error: {e}"
                })
        
        if validation_report["total_files"] > 0:
            validation_report["coverage_rate"] = (
                validation_report["files_with_headers"] / validation_report["total_files"]
            )
        
        return validation_report
    
    def _requirement_exists(self, req_id: str) -> bool:
        """Check if requirement exists in Neo4j."""
        
        query = "MATCH (r:Requirement {id: $req_id}) RETURN count(r) > 0 as exists"
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(query, {"req_id": req_id})
            return result.single()["exists"]
    
    def update_artifact_headers(
        self, 
        file_path: str, 
        new_requirements: List[str],
        new_tests: Optional[List[str]] = None
    ) -> bool:
        """Update provenance headers in existing file."""
        
        try:
            path = Path(file_path)
            content = path.read_text(encoding='utf-8')
            
            # Extract current header
            current_header = self.scanner._extract_provenance_header(content)
            
            # Generate new header
            artifact_name = current_header["name"] if current_header else path.stem.title()
            artifact_type = "Service" if "service" in path.stem.lower() else "Module"
            
            updated_tests = new_tests if new_tests else (
                current_header["verified_by"] if current_header else []
            )
            
            new_header = self.generate_provenance_header(
                artifact_name=artifact_name,
                artifact_type=artifact_type,
                requirements=new_requirements,
                tests=updated_tests
            )
            
            # Replace header in content
            if current_header:
                # Find and replace existing header
                header_patterns = [
                    r'/\*\n \* [^\n]+\n \* Implements: [^\n]+\n \* VerifiedBy: [^\n]*\n \* Generated: [^\n]*\n \* Provenance: [^\n]*\n \*/',
                    r'"""\n[^\n]+\nImplements: [^\n]+\nVerifiedBy: [^\n]*\nGenerated: [^\n]*\nProvenance: [^\n]*\n"""'
                ]
                
                updated_content = content
                for pattern in header_patterns:
                    updated_content = re.sub(pattern, new_header, updated_content, count=1)
                
            else:
                # Add header at the top
                updated_content = new_header + "\n\n" + content
            
            # Write back to file
            path.write_text(updated_content, encoding='utf-8')
            
            logger.info(f"Updated provenance header for {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update header for {file_path}: {e}")
            return False
    
    def sync_artifacts_to_neo4j(self, scan_results: Dict[str, Any]) -> None:
        """Sync scanned code artifacts to Neo4j graph."""
        
        # Sync all artifacts
        all_artifacts = []
        for artifact_type in ['services', 'modules', 'classes', 'functions', 'tests']:
            all_artifacts.extend(list(scan_results[artifact_type].values()))
        
        self.neo4j.sync_code_artifacts(all_artifacts)
        
        # Create dependency relationships
        for dep in scan_results["dependencies"]:
            self._create_dependency_relationship(dep["from"], dep["to"], dep["type"])
    
    def _create_dependency_relationship(self, from_id: str, to_id: str, relationship_type: str) -> None:
        """Create dependency relationship in Neo4j."""
        
        query = f"""
        MATCH (a {{id: $from_id}})
        MATCH (b {{id: $to_id}})
        MERGE (a)-[:{relationship_type.upper()}]->(b)
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            session.run(query, {"from_id": from_id, "to_id": to_id})
    
    def generate_impact_report(self, changed_artifacts: List[str]) -> Dict[str, Any]:
        """Generate impact report for changed artifacts."""
        
        impact_report = {
            "changed_artifacts": changed_artifacts,
            "upstream_requirements": [],
            "upstream_problems": [],
            "downstream_tests": [],
            "downstream_services": [],
            "affected_features": [],
            "risk_assessment": "low",
            "recommended_actions": []
        }
        
        # Calculate impact using Neo4j
        impact_data = self.neo4j.calculate_change_impact(changed_artifacts)
        impact_report.update(impact_data)
        
        # Assess risk level
        risk_score = (
            len(impact_report["upstream_requirements"]) * 0.3 +
            len(impact_report["downstream_tests"]) * 0.2 +
            len(impact_report["downstream_services"]) * 0.5
        )
        
        if risk_score >= 10:
            impact_report["risk_assessment"] = "high"
        elif risk_score >= 5:
            impact_report["risk_assessment"] = "medium"
        else:
            impact_report["risk_assessment"] = "low"
        
        # Generate recommendations
        recommendations = []
        if impact_report["upstream_requirements"]:
            recommendations.append("Review requirement changes and update documentation")
        if impact_report["downstream_tests"]:
            recommendations.append(f"Run {len(impact_report['downstream_tests'])} affected tests")
        if impact_report["downstream_services"]:
            recommendations.append("Perform integration testing of dependent services")
        
        impact_report["recommended_actions"] = recommendations
        
        return impact_report
