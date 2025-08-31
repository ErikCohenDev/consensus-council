"""
Integration service for Code Artifact Graph with SE pipeline.

This service provides end-to-end traceability by integrating the Code Artifact Graph
with the Systems Engineering pipeline, enabling provenance tracking from vision
documents through to actual implementation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..models.se_models import (
    SystemsEntity, ImplementationTask, ArchitecturalComponent,
    WSJFMetrics, SEStage
)
from ..models.code_artifact_models import (
    CodeArtifact, TraceMatrix, RepositoryStructure,
    DriftDetection, TraceabilityLink, TraceabilityType
)
from .provenance_tracker import ProvenanceTracker
from .codegen_engine import CodeGenEngine
# from .se_integration import SEIntegrationService  # Commented to avoid circular import


class GraphIntegrationService:
    """Integrates Code Artifact Graph with SE pipeline for complete traceability."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.provenance_tracker = ProvenanceTracker(str(repo_path))
        self.codegen_engine = CodeGenEngine(str(repo_path))
        self.se_service = SEIntegrationService()
    
    def build_complete_traceability_graph(self,
                                        prd_path: str,
                                        implementation_path: str,
                                        architecture_path: str) -> Tuple[TraceMatrix, RepositoryStructure]:
        """Build complete traceability from requirements through implementation."""
        
        # Extract requirements and tasks from documents
        requirements = self.provenance_tracker.extract_requirements_from_prd(prd_path)
        tasks = self.provenance_tracker.extract_task_ids_from_implementation(implementation_path)
        
        # Build repository structure
        repo_structure = self.provenance_tracker.build_repository_structure()
        
        # Build trace matrix
        trace_matrix = self.provenance_tracker.build_trace_matrix(requirements, tasks)
        
        # Enhance with SE pipeline data
        self._enhance_with_se_data(trace_matrix, architecture_path)
        
        return trace_matrix, repo_structure
    
    def _enhance_with_se_data(self, trace_matrix: TraceMatrix, architecture_path: str) -> None:
        """Enhance trace matrix with SE pipeline architectural data."""
        try:
            with open(architecture_path, 'r') as f:
                arch_content = f.read()
            
            # Extract architectural components mentioned in the document
            component_pattern = r'##\s+([^#\n]+Component[^#\n]*)'
            components = re.findall(component_pattern, arch_content)
            
            # Link components to code artifacts
            for component_name in components:
                component_files = self._find_component_files(component_name)
                for file_path in component_files:
                    if file_path in self.provenance_tracker.artifacts:
                        # Add architectural traceability link
                        link = TraceabilityLink(
                            source_id=component_name,
                            target_id=file_path,
                            relationship_type=TraceabilityType.IMPLEMENTS,
                            confidence_score=0.7,
                            last_verified=datetime.now()
                        )
                        
                        # Add to trace matrix (extend existing structure)
                        if 'architecture_to_code' not in trace_matrix.__dict__:
                            trace_matrix.__dict__['architecture_to_code'] = {}
                        
                        if component_name not in trace_matrix.__dict__['architecture_to_code']:
                            trace_matrix.__dict__['architecture_to_code'][component_name] = []
                        
                        trace_matrix.__dict__['architecture_to_code'][component_name].append(link)
        
        except Exception as e:
            print(f"Warning: Could not enhance with SE data: {e}")
    
    def _find_component_files(self, component_name: str) -> List[str]:
        """Find code files likely implementing an architectural component."""
        component_files = []
        
        # Convert component name to potential file patterns
        clean_name = component_name.lower().replace(' component', '').replace(' ', '_')
        patterns = [
            f"*{clean_name}*",
            f"*{clean_name.replace('_', '')}*",
            f"*{clean_name.replace('_', '-')}*"
        ]
        
        for artifact in self.provenance_tracker.artifacts.values():
            file_name = Path(artifact.file_path).name.lower()
            
            for pattern in patterns:
                pattern_clean = pattern.replace('*', '')
                if pattern_clean in file_name:
                    component_files.append(artifact.file_path)
                    break
        
        return component_files
    
    def generate_implementation_from_se_pipeline(self,
                                               entities: List[SystemsEntity],
                                               tasks: List[ImplementationTask],
                                               components: List[ArchitecturalComponent],
                                               requirements: Dict[str, str]) -> List[Tuple[str, str]]:
        """Generate code implementations from SE pipeline artifacts."""
        
        # Generate component stubs
        component_files = self.codegen_engine.generate_component_stubs(components, requirements)
        
        # Generate task implementation stubs
        task_files = self.codegen_engine.generate_implementation_stubs(tasks, components, requirements)
        
        # Combine all generated files
        all_files = component_files + task_files
        
        # Generate traceability matrix document
        matrix_doc = self.codegen_engine.generate_requirements_traceability_matrix(
            requirements, all_files
        )
        all_files.append(("docs/TRACEABILITY_MATRIX.md", matrix_doc))
        
        return all_files
    
    def validate_implementation_completeness(self,
                                           requirements: Dict[str, str],
                                           tasks: List[ImplementationTask]) -> Dict[str, any]:
        """Validate that implementation covers all requirements and tasks."""
        validation_results = {
            'coverage_percentage': 0.0,
            'missing_requirements': [],
            'missing_tasks': [],
            'orphaned_code': [],
            'test_coverage_gaps': [],
            'validation_timestamp': datetime.now().isoformat()
        }
        
        # Check requirement coverage
        implemented_reqs = set()
        for artifact in self.provenance_tracker.artifacts.values():
            implemented_reqs.update(artifact.referenced_requirements)
        
        total_reqs = set(requirements.keys())
        missing_reqs = total_reqs - implemented_reqs
        validation_results['missing_requirements'] = list(missing_reqs)
        
        if total_reqs:
            validation_results['coverage_percentage'] = len(implemented_reqs) / len(total_reqs) * 100
        
        # Check task implementation
        implemented_tasks = set()
        for artifact in self.provenance_tracker.artifacts.values():
            implemented_tasks.update(artifact.referenced_tasks)
        
        total_task_ids = {task.task_id for task in tasks}
        missing_tasks = total_task_ids - implemented_tasks
        validation_results['missing_tasks'] = list(missing_tasks)
        
        # Check for orphaned code (no requirements)
        for artifact in self.provenance_tracker.artifacts.values():
            if (artifact.artifact_type.value == 'source_code' and 
                not artifact.referenced_requirements and 
                not artifact.referenced_tasks):
                validation_results['orphaned_code'].append(artifact.file_path)
        
        # Check test coverage gaps
        for file_path, links in self.provenance_tracker.trace_matrix.code_to_tests.items():
            if not links:
                validation_results['test_coverage_gaps'].append(file_path)
        
        return validation_results
    
    def generate_provenance_report(self,
                                 requirements: Dict[str, str],
                                 tasks: List[ImplementationTask]) -> str:
        """Generate comprehensive provenance and traceability report."""
        report = []
        report.append("# Provenance & Traceability Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        # Validation summary
        validation = self.validate_implementation_completeness(requirements, tasks)
        report.append("## Implementation Completeness")
        report.append(f"- **Coverage**: {validation['coverage_percentage']:.1f}%")
        report.append(f"- **Missing Requirements**: {len(validation['missing_requirements'])}")
        report.append(f"- **Missing Tasks**: {len(validation['missing_tasks'])}")
        report.append(f"- **Orphaned Code**: {len(validation['orphaned_code'])}")
        report.append(f"- **Test Coverage Gaps**: {len(validation['test_coverage_gaps'])}")
        report.append("")
        
        # Detailed traceability
        report.append("## Requirements Traceability")
        for req_id, req_desc in requirements.items():
            report.append(f"### {req_id}")
            report.append(f"**Description**: {req_desc[:100]}...")
            
            # Find implementing files
            implementing_files = []
            for artifact in self.provenance_tracker.artifacts.values():
                if req_id in artifact.referenced_requirements:
                    implementing_files.append(artifact.file_path)
            
            if implementing_files:
                report.append("**Implementation**:")
                for file_path in implementing_files:
                    artifact = self.provenance_tracker.artifacts[file_path]
                    report.append(f"- `{file_path}` ({artifact.lines_of_code} LOC)")
            else:
                report.append("**Implementation**: ⚠️ NOT IMPLEMENTED")
            
            report.append("")
        
        # Task implementation status
        report.append("## Task Implementation Status")
        for task in tasks:
            report.append(f"### {task.task_id}")
            report.append(f"**Description**: {task.description}")
            report.append(f"**Priority**: {task.priority}")
            
            # Find implementing files
            implementing_files = []
            for artifact in self.provenance_tracker.artifacts.values():
                if task.task_id in artifact.referenced_tasks:
                    implementing_files.append(artifact.file_path)
            
            if implementing_files:
                report.append("**Implementation**:")
                for file_path in implementing_files:
                    report.append(f"- `{file_path}`")
            else:
                report.append("**Implementation**: ⚠️ NOT IMPLEMENTED")
            
            report.append("")
        
        # Drift detections
        if self.provenance_tracker.trace_matrix.drift_detections:
            report.append("## Drift Detections")
            for drift in self.provenance_tracker.trace_matrix.drift_detections:
                report.append(f"- **{drift.drift_type}** ({drift.severity}): {drift.description}")
            report.append("")
        
        return '\n'.join(report)
    
    def export_graph_data(self, output_dir: str) -> Dict[str, str]:
        """Export all graph data for visualization and analysis."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        # Export trace matrix
        trace_matrix_path = output_path / "trace_matrix.json"
        self.provenance_tracker.save_trace_matrix(str(trace_matrix_path))
        exported_files['trace_matrix'] = str(trace_matrix_path)
        
        # Export repository structure
        repo_structure = self.provenance_tracker.build_repository_structure()
        repo_structure_path = output_path / "repository_structure.json"
        with open(repo_structure_path, 'w') as f:
            json.dump(repo_structure.dict(), f, indent=2, default=str)
        exported_files['repository_structure'] = str(repo_structure_path)
        
        # Export artifacts catalog
        artifacts_path = output_path / "artifacts_catalog.json"
        artifacts_dict = {
            path: artifact.dict() for path, artifact in self.provenance_tracker.artifacts.items()
        }
        with open(artifacts_path, 'w') as f:
            json.dump(artifacts_dict, f, indent=2, default=str)
        exported_files['artifacts_catalog'] = str(artifacts_path)
        
        return exported_files
    
    def import_se_pipeline_results(self, se_results_path: str) -> None:
        """Import SE pipeline results and update traceability graph."""
        try:
            with open(se_results_path, 'r') as f:
                se_data = json.load(f)
            
            # Update artifacts with SE pipeline metadata
            if 'entities' in se_data:
                self._link_entities_to_code(se_data['entities'])
            
            if 'components' in se_data:
                self._link_components_to_code(se_data['components'])
            
            if 'tasks' in se_data:
                self._link_tasks_to_code(se_data['tasks'])
        
        except Exception as e:
            print(f"Warning: Could not import SE pipeline results: {e}")
    
    def _link_entities_to_code(self, entities: List[Dict]) -> None:
        """Link SE entities to code artifacts."""
        for entity_data in entities:
            entity_name = entity_data.get('name', '')
            
            # Find code files that might implement this entity
            matching_files = []
            for artifact in self.provenance_tracker.artifacts.values():
                if self._entity_matches_artifact(entity_name, artifact):
                    matching_files.append(artifact.file_path)
            
            # Store entity-to-code relationships
            if matching_files and 'entity_to_code' not in self.provenance_tracker.trace_matrix.__dict__:
                self.provenance_tracker.trace_matrix.__dict__['entity_to_code'] = {}
            
            if matching_files:
                self.provenance_tracker.trace_matrix.__dict__['entity_to_code'][entity_name] = [
                    TraceabilityLink(
                        source_id=entity_name,
                        target_id=file_path,
                        relationship_type=TraceabilityType.IMPLEMENTS,
                        confidence_score=0.6,
                        last_verified=datetime.now()
                    ) for file_path in matching_files
                ]
    
    def _link_components_to_code(self, components: List[Dict]) -> None:
        """Link architectural components to code artifacts."""
        for comp_data in components:
            comp_name = comp_data.get('name', '')
            
            # Find implementing files
            implementing_files = self.codegen_engine._find_component_files(comp_name)
            
            if implementing_files and 'components_to_code' not in self.provenance_tracker.trace_matrix.__dict__:
                self.provenance_tracker.trace_matrix.__dict__['components_to_code'] = {}
            
            if implementing_files:
                self.provenance_tracker.trace_matrix.__dict__['components_to_code'][comp_name] = [
                    TraceabilityLink(
                        source_id=comp_name,
                        target_id=file_path,
                        relationship_type=TraceabilityType.IMPLEMENTS,
                        confidence_score=0.8,
                        last_verified=datetime.now()
                    ) for file_path in implementing_files
                ]
    
    def _link_tasks_to_code(self, tasks: List[Dict]) -> None:
        """Link implementation tasks to code artifacts."""
        for task_data in tasks:
            task_id = task_data.get('task_id', '')
            
            # Find implementing files
            implementing_files = []
            for artifact in self.provenance_tracker.artifacts.values():
                if task_id in artifact.referenced_tasks:
                    implementing_files.append(artifact.file_path)
            
            if implementing_files and 'tasks_to_code' not in self.provenance_tracker.trace_matrix.__dict__:
                self.provenance_tracker.trace_matrix.__dict__['tasks_to_code'] = {}
            
            if implementing_files:
                self.provenance_tracker.trace_matrix.__dict__['tasks_to_code'][task_id] = [
                    TraceabilityLink(
                        source_id=task_id,
                        target_id=file_path,
                        relationship_type=TraceabilityType.IMPLEMENTS,
                        confidence_score=0.9,
                        last_verified=datetime.now()
                    ) for file_path in implementing_files
                ]
    
    def _entity_matches_artifact(self, entity_name: str, artifact: CodeArtifact) -> bool:
        """Check if an SE entity matches a code artifact."""
        entity_keywords = set(entity_name.lower().split())
        artifact_keywords = set(Path(artifact.file_path).stem.lower().split('_'))
        
        # Simple keyword overlap heuristic
        return len(entity_keywords & artifact_keywords) >= 1
    
    def generate_end_to_end_trace(self,
                                requirement_id: str,
                                trace_matrix: TraceMatrix) -> Dict[str, List[str]]:
        """Generate end-to-end trace from requirement to tests."""
        trace = {
            'requirement': requirement_id,
            'implementing_code': [],
            'test_files': [],
            'schema_files': [],
            'architectural_components': [],
            'implementation_tasks': []
        }
        
        # Follow the trace chain
        # REQ -> Code
        if requirement_id in trace_matrix.requirements_to_code:
            code_files = [link.target_id for link in trace_matrix.requirements_to_code[requirement_id]]
            trace['implementing_code'] = code_files
            
            # Code -> Tests
            for code_file in code_files:
                if code_file in trace_matrix.code_to_tests:
                    test_files = [link.target_id for link in trace_matrix.code_to_tests[code_file]]
                    trace['test_files'].extend(test_files)
                    
                    # Tests -> Schemas
                    for test_file in test_files:
                        if test_file in trace_matrix.tests_to_schemas:
                            schema_files = [link.target_id for link in trace_matrix.tests_to_schemas[test_file]]
                            trace['schema_files'].extend(schema_files)
        
        # Remove duplicates
        for key in trace:
            if isinstance(trace[key], list):
                trace[key] = list(set(trace[key]))
        
        return trace
    
    def create_impact_analysis(self,
                             changed_files: List[str],
                             trace_matrix: TraceMatrix) -> Dict[str, List[str]]:
        """Analyze impact of code changes using traceability graph."""
        impact = {
            'affected_requirements': [],
            'affected_tests': [],
            'affected_components': [],
            'affected_tasks': [],
            'recommended_actions': []
        }
        
        for changed_file in changed_files:
            # Find requirements affected by this change
            for req_id, links in trace_matrix.requirements_to_code.items():
                if any(link.target_id == changed_file for link in links):
                    impact['affected_requirements'].append(req_id)
            
            # Find tests that should be run
            if changed_file in trace_matrix.code_to_tests:
                test_files = [link.target_id for link in trace_matrix.code_to_tests[changed_file]]
                impact['affected_tests'].extend(test_files)
            
            # Find tasks that might be affected
            if hasattr(trace_matrix, 'tasks_to_code'):
                for task_id, links in trace_matrix.tasks_to_code.items():
                    if any(link.target_id == changed_file for link in links):
                        impact['affected_tasks'].append(task_id)
        
        # Generate recommendations
        if impact['affected_tests']:
            impact['recommended_actions'].append(f"Run tests: {', '.join(set(impact['affected_tests']))}")
        
        if impact['affected_requirements']:
            impact['recommended_actions'].append(f"Review requirements: {', '.join(set(impact['affected_requirements']))}")
        
        if not impact['affected_tests'] and changed_file.endswith('.py'):
            impact['recommended_actions'].append(f"Consider adding tests for {changed_file}")
        
        # Remove duplicates
        for key in impact:
            if isinstance(impact[key], list):
                impact[key] = list(set(impact[key]))
        
        return impact
    
    def sync_with_se_pipeline(self,
                            se_pipeline_output: Dict) -> Dict[str, any]:
        """Synchronize Code Artifact Graph with SE pipeline updates."""
        sync_results = {
            'updated_artifacts': [],
            'new_requirements': [],
            'obsolete_code': [],
            'sync_timestamp': datetime.now().isoformat()
        }
        
        # Extract new or updated requirements
        if 'requirements' in se_pipeline_output:
            current_reqs = set()
            for artifact in self.provenance_tracker.artifacts.values():
                current_reqs.update(artifact.referenced_requirements)
            
            new_reqs = set(se_pipeline_output['requirements'].keys()) - current_reqs
            sync_results['new_requirements'] = list(new_reqs)
        
        # Identify potentially obsolete code
        if 'deprecated_entities' in se_pipeline_output:
            for entity_name in se_pipeline_output['deprecated_entities']:
                obsolete_files = self.codegen_engine._find_component_files(entity_name)
                sync_results['obsolete_code'].extend(obsolete_files)
        
        return sync_results


def create_graph_integration_service(repo_path: str) -> GraphIntegrationService:
    """Factory function to create graph integration service."""
    return GraphIntegrationService(repo_path)