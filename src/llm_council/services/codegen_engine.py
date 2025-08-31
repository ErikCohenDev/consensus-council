"""
Code generation engine for creating implementation stubs from specifications.

This service generates code scaffolding with provenance headers that link
back to requirements and tasks, enabling full traceability from specs to code.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..models.code_artifact_models import ProvenanceHeader, ArtifactType
from ..models.se_models import ImplementationTask, ArchitecturalComponent


class CodeGenEngine:
    """Generates code stubs with provenance tracking from specifications."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.language_templates = {
            'python': {
                'class': self._python_class_template,
                'function': self._python_function_template,
                'module': self._python_module_template,
                'test': self._python_test_template
            },
            'javascript': {
                'class': self._js_class_template,
                'function': self._js_function_template,
                'module': self._js_module_template,
                'test': self._js_test_template
            },
            'typescript': {
                'class': self._ts_class_template,
                'function': self._ts_function_template,
                'module': self._ts_module_template,
                'test': self._ts_test_template
            }
        }
    
    def generate_implementation_stubs(self,
                                    tasks: List[ImplementationTask],
                                    components: List[ArchitecturalComponent],
                                    requirements: Dict[str, str]) -> List[Tuple[str, str]]:
        """Generate code stubs for implementation tasks with provenance headers."""
        generated_files = []
        
        for task in tasks:
            # Determine target language and file structure
            language = self._infer_language_from_task(task)
            file_paths = self._generate_file_paths_for_task(task, language)
            
            for file_path, stub_type in file_paths:
                # Generate provenance header
                related_reqs = self._find_related_requirements(task, requirements)
                header = self._generate_provenance_header(
                    f"Implementation Task {task.task_id}",
                    related_reqs,
                    [task.task_id]
                )
                
                # Generate code stub
                stub_content = self._generate_code_stub(
                    task, stub_type, language, components, header
                )
                
                generated_files.append((file_path, stub_content))
        
        return generated_files
    
    def generate_component_stubs(self,
                               components: List[ArchitecturalComponent],
                               requirements: Dict[str, str]) -> List[Tuple[str, str]]:
        """Generate code stubs for architectural components."""
        generated_files = []
        
        for component in components:
            language = self._infer_language_from_component(component)
            
            # Generate main component file
            main_file_path = self._generate_component_file_path(component, language)
            related_reqs = [req for req in requirements.keys() if req in str(component)]
            
            header = self._generate_provenance_header(
                f"Architectural Component {component.name}",
                related_reqs,
                []
            )
            
            stub_content = self._generate_component_stub(component, language, header)
            generated_files.append((main_file_path, stub_content))
            
            # Generate corresponding test file
            test_file_path = self._generate_test_file_path(main_file_path, language)
            test_content = self._generate_test_stub(component, language, header)
            generated_files.append((test_file_path, test_content))
        
        return generated_files
    
    def _generate_provenance_header(self, 
                                  generated_from: str,
                                  requirements: List[str],
                                  tasks: List[str]) -> str:
        """Generate provenance header for code files."""
        header = ProvenanceHeader(
            generated_from=generated_from,
            requirements=requirements,
            tasks=tasks,
            generation_timestamp=datetime.now()
        )
        
        return f"""#
# GENERATED_FROM: {header.generated_from}
# REQUIREMENTS: {', '.join(header.requirements)}
# TASKS: {', '.join(header.tasks)}
# GENERATED: {header.generation_timestamp.isoformat()}
#

"""
    
    def _infer_language_from_task(self, task: ImplementationTask) -> str:
        """Infer programming language from task description and context."""
        description = task.description.lower()
        
        if any(term in description for term in ['python', 'django', 'flask', 'fastapi', '.py']):
            return 'python'
        elif any(term in description for term in ['javascript', 'js', 'node', 'express', '.js']):
            return 'javascript'
        elif any(term in description for term in ['typescript', 'ts', 'react', 'next', '.ts']):
            return 'typescript'
        
        # Default based on existing codebase
        if any(self.repo_path.glob('**/*.py')):
            return 'python'
        elif any(self.repo_path.glob('**/*.ts')):
            return 'typescript'
        elif any(self.repo_path.glob('**/*.js')):
            return 'javascript'
        
        return 'python'  # Default fallback
    
    def _infer_language_from_component(self, component: ArchitecturalComponent) -> str:
        """Infer programming language from component technology stack."""
        technologies = [tech.lower() for tech in component.technologies]
        
        if any(tech in ['python', 'django', 'flask', 'fastapi'] for tech in technologies):
            return 'python'
        elif any(tech in ['typescript', 'react', 'nextjs'] for tech in technologies):
            return 'typescript'
        elif any(tech in ['javascript', 'node', 'express'] for tech in technologies):
            return 'javascript'
        
        return 'python'  # Default fallback
    
    def _generate_file_paths_for_task(self, task: ImplementationTask, language: str) -> List[Tuple[str, str]]:
        """Generate file paths for implementation task."""
        paths = []
        
        # Convert task ID to file-friendly name
        file_base = task.task_id.lower().replace('-', '_')
        
        if language == 'python':
            if 'test' in task.description.lower():
                paths.append((f"tests/test_{file_base}.py", "test"))
            elif 'model' in task.description.lower() or 'schema' in task.description.lower():
                paths.append((f"src/llm_council/models/{file_base}.py", "module"))
            elif 'service' in task.description.lower():
                paths.append((f"src/llm_council/services/{file_base}.py", "module"))
            else:
                paths.append((f"src/llm_council/{file_base}.py", "module"))
        
        elif language in ['javascript', 'typescript']:
            ext = 'ts' if language == 'typescript' else 'js'
            if 'test' in task.description.lower():
                paths.append((f"frontend/src/__tests__/{file_base}.test.{ext}", "test"))
            elif 'component' in task.description.lower():
                paths.append((f"frontend/src/components/{file_base}.{ext}", "class"))
            else:
                paths.append((f"frontend/src/{file_base}.{ext}", "module"))
        
        return paths
    
    def _generate_component_file_path(self, component: ArchitecturalComponent, language: str) -> str:
        """Generate file path for architectural component."""
        name = component.name.lower().replace(' ', '_').replace('-', '_')
        
        if language == 'python':
            if 'service' in component.name.lower():
                return f"src/llm_council/services/{name}.py"
            elif 'model' in component.name.lower():
                return f"src/llm_council/models/{name}.py"
            else:
                return f"src/llm_council/{name}.py"
        
        elif language in ['javascript', 'typescript']:
            ext = 'ts' if language == 'typescript' else 'js'
            return f"frontend/src/components/{name}.{ext}"
        
        return f"src/{name}.py"
    
    def _generate_test_file_path(self, main_file_path: str, language: str) -> str:
        """Generate corresponding test file path."""
        main_path = Path(main_file_path)
        
        if language == 'python':
            test_name = f"test_{main_path.stem}.py"
            return f"tests/{test_name}"
        
        elif language in ['javascript', 'typescript']:
            ext = 'ts' if language == 'typescript' else 'js'
            test_name = f"{main_path.stem}.test.{ext}"
            return f"frontend/src/__tests__/{test_name}"
        
        return f"tests/test_{main_path.stem}.py"
    
    def _find_related_requirements(self, task: ImplementationTask, requirements: Dict[str, str]) -> List[str]:
        """Find requirements related to an implementation task."""
        related = []
        task_text = task.description.lower()
        
        for req_id, req_description in requirements.items():
            req_text = req_description.lower()
            
            # Simple keyword matching - could be enhanced with semantic similarity
            common_keywords = self._extract_keywords(task_text) & self._extract_keywords(req_text)
            if len(common_keywords) >= 2:  # Require at least 2 matching keywords
                related.append(req_id)
        
        return related
    
    def _extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords from text."""
        # Remove common words and extract meaningful terms
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return set(words) - common_words
    
    def _generate_code_stub(self,
                          task: ImplementationTask,
                          stub_type: str,
                          language: str,
                          components: List[ArchitecturalComponent],
                          header: str) -> str:
        """Generate code stub based on task and language."""
        template_func = self.language_templates[language][stub_type]
        return template_func(task, components, header)
    
    def _generate_component_stub(self,
                               component: ArchitecturalComponent,
                               language: str,
                               header: str) -> str:
        """Generate code stub for architectural component."""
        template_func = self.language_templates[language]['class']
        return template_func(component, [], header)
    
    def _generate_test_stub(self,
                          component: ArchitecturalComponent,
                          language: str,
                          header: str) -> str:
        """Generate test stub for component."""
        template_func = self.language_templates[language]['test']
        return template_func(component, [], header)
    
    # Python templates
    def _python_class_template(self, item, components, header):
        if hasattr(item, 'name'):  # ArchitecturalComponent
            class_name = item.name.replace(' ', '').replace('-', '')
            description = item.description
        else:  # ImplementationTask
            class_name = item.task_id.replace('-', '').replace('_', '')
            description = item.description
        
        return f"""{header}\"\"\"
{description}
\"\"\"

from typing import Dict, List, Optional


class {class_name}:
    \"\"\"
    {description}
    \"\"\"
    
    def __init__(self):
        # TODO: Initialize {class_name} based on requirements
        pass
    
    def process(self) -> Dict:
        \"\"\"
        Main processing method for {class_name}.
        
        Returns:
            Dict: Processing results
        \"\"\"
        # TODO: Implement main processing logic
        raise NotImplementedError("Implementation required")
"""
    
    def _python_function_template(self, item, components, header):
        func_name = item.task_id.lower().replace('-', '_')
        return f"""{header}\"\"\"
{item.description}
\"\"\"

from typing import Dict, List, Optional


def {func_name}() -> Dict:
    \"\"\"
    {item.description}
    
    Returns:
        Dict: Function results
    \"\"\"
    # TODO: Implement {func_name} based on requirements
    raise NotImplementedError("Implementation required")
"""
    
    def _python_module_template(self, item, components, header):
        return f"""{header}\"\"\"
{item.description}
\"\"\"

from typing import Dict, List, Optional


# TODO: Implement module functionality for {item.task_id}
# Requirements: {', '.join(getattr(item, 'referenced_requirements', []))}


def main():
    \"\"\"Main module entry point.\"\"\"
    pass


if __name__ == "__main__":
    main()
"""
    
    def _python_test_template(self, item, components, header):
        test_class = f"Test{item.name.replace(' ', '')}" if hasattr(item, 'name') else f"Test{item.task_id.replace('-', '')}"
        return f"""{header}\"\"\"
Test cases for {item.description if hasattr(item, 'description') else item.task_id}
\"\"\"

import pytest
from unittest.mock import Mock, patch


class {test_class}:
    \"\"\"Test cases for {item.name if hasattr(item, 'name') else item.task_id}.\"\"\"
    
    def test_basic_functionality(self):
        \"\"\"Test basic functionality.\"\"\"
        # TODO: Implement test cases
        assert True  # Placeholder
    
    def test_error_handling(self):
        \"\"\"Test error handling scenarios.\"\"\"
        # TODO: Implement error case tests
        assert True  # Placeholder
    
    def test_edge_cases(self):
        \"\"\"Test edge cases and boundary conditions.\"\"\"
        # TODO: Implement edge case tests
        assert True  # Placeholder
"""
    
    # TypeScript templates
    def _ts_class_template(self, item, components, header):
        class_name = item.name.replace(' ', '').replace('-', '') if hasattr(item, 'name') else item.task_id.replace('-', '')
        return f"""/*
{header.replace('#', '//')}
*/

/**
 * {item.description if hasattr(item, 'description') else item.task_id}
 */

export interface {class_name}Config {{
  // TODO: Define configuration interface
}}

export class {class_name} {{
  private config: {class_name}Config;
  
  constructor(config: {class_name}Config) {{
    this.config = config;
  }}
  
  /**
   * Main processing method for {class_name}.
   */
  public async process(): Promise<Record<string, any>> {{
    // TODO: Implement main processing logic
    throw new Error('Implementation required');
  }}
}}
"""
    
    def _ts_function_template(self, item, components, header):
        func_name = item.task_id.lower().replace('-', '_') if hasattr(item, 'task_id') else 'processItem'
        return f"""/*
{header.replace('#', '//')}
*/

/**
 * {item.description if hasattr(item, 'description') else 'Function implementation'}
 */
export async function {func_name}(): Promise<Record<string, any>> {{
  // TODO: Implement {func_name} based on requirements
  throw new Error('Implementation required');
}}
"""
    
    def _ts_module_template(self, item, components, header):
        return f"""/*
{header.replace('#', '//')}
*/

/**
 * {item.description if hasattr(item, 'description') else item.task_id}
 */

// TODO: Implement module functionality for {item.task_id if hasattr(item, 'task_id') else 'module'}

export const config = {{
  // TODO: Define module configuration
}};

export default {{
  // TODO: Define module exports
}};
"""
    
    def _ts_test_template(self, item, components, header):
        test_name = item.name.replace(' ', '') if hasattr(item, 'name') else item.task_id.replace('-', '')
        return f"""/*
{header.replace('#', '//')}
*/

import {{ describe, test, expect }} from '@jest/globals';

describe('{test_name}', () => {{
  test('basic functionality', () => {{
    // TODO: Implement test cases
    expect(true).toBe(true); // Placeholder
  }});
  
  test('error handling', () => {{
    // TODO: Implement error case tests
    expect(true).toBe(true); // Placeholder
  }});
  
  test('edge cases', () => {{
    // TODO: Implement edge case tests
    expect(true).toBe(true); // Placeholder
  }});
}});
"""
    
    # JavaScript templates (similar to TypeScript but without types)
    def _js_class_template(self, item, components, header):
        class_name = item.name.replace(' ', '').replace('-', '') if hasattr(item, 'name') else item.task_id.replace('-', '')
        return f"""/*
{header.replace('#', '//')}
*/

/**
 * {item.description if hasattr(item, 'description') else item.task_id}
 */
class {class_name} {{
  constructor(config) {{
    this.config = config;
  }}
  
  /**
   * Main processing method for {class_name}.
   */
  async process() {{
    // TODO: Implement main processing logic
    throw new Error('Implementation required');
  }}
}}

module.exports = {class_name};
"""
    
    def _js_function_template(self, item, components, header):
        func_name = item.task_id.lower().replace('-', '_') if hasattr(item, 'task_id') else 'processItem'
        return f"""/*
{header.replace('#', '//')}
*/

/**
 * {item.description if hasattr(item, 'description') else 'Function implementation'}
 */
async function {func_name}() {{
  // TODO: Implement {func_name} based on requirements
  throw new Error('Implementation required');
}}

module.exports = {func_name};
"""
    
    def _js_module_template(self, item, components, header):
        return f"""/*
{header.replace('#', '//')}
*/

/**
 * {item.description if hasattr(item, 'description') else item.task_id}
 */

// TODO: Implement module functionality for {item.task_id if hasattr(item, 'task_id') else 'module'}

const config = {{
  // TODO: Define module configuration
}};

module.exports = {{
  config,
  // TODO: Define module exports
}};
"""
    
    def _js_test_template(self, item, components, header):
        test_name = item.name if hasattr(item, 'name') else item.task_id
        return f"""/*
{header.replace('#', '//')}
*/

const {{ describe, test, expect }} = require('@jest/globals');

describe('{test_name}', () => {{
  test('basic functionality', () => {{
    // TODO: Implement test cases
    expect(true).toBe(true); // Placeholder
  }});
  
  test('error handling', () => {{
    // TODO: Implement error case tests
    expect(true).toBe(true); // Placeholder
  }});
  
  test('edge cases', () => {{
    // TODO: Implement edge case tests
    expect(true).toBe(true); // Placeholder
  }});
}});
"""
    
    def generate_requirements_traceability_matrix(self,
                                                requirements: Dict[str, str],
                                                generated_files: List[Tuple[str, str]]) -> str:
        """Generate a traceability matrix document."""
        matrix = []
        matrix.append("# Requirements Traceability Matrix")
        matrix.append(f"Generated: {datetime.now().isoformat()}")
        matrix.append("")
        matrix.append("| Requirement ID | Description | Implementing Files | Test Coverage |")
        matrix.append("|----------------|-------------|-------------------|---------------|")
        
        for req_id, req_desc in requirements.items():
            implementing_files = []
            test_files = []
            
            for file_path, content in generated_files:
                if req_id in content:
                    if 'test' in file_path.lower():
                        test_files.append(file_path)
                    else:
                        implementing_files.append(file_path)
            
            impl_str = ', '.join(implementing_files) if implementing_files else "**NOT IMPLEMENTED**"
            test_str = ', '.join(test_files) if test_files else "**NO TESTS**"
            
            matrix.append(f"| {req_id} | {req_desc[:50]}... | {impl_str} | {test_str} |")
        
        return '\n'.join(matrix)
    
    def write_generated_files(self, generated_files: List[Tuple[str, str]], dry_run: bool = True) -> List[str]:
        """Write generated files to filesystem."""
        written_files = []
        
        for file_path, content in generated_files:
            full_path = self.repo_path / file_path
            
            if dry_run:
                print(f"Would create: {file_path}")
                continue
            
            # Create directory if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(full_path, 'w') as f:
                f.write(content)
            
            written_files.append(file_path)
        
        return written_files


def create_codegen_engine(repo_path: str) -> CodeGenEngine:
    """Factory function to create code generation engine."""
    return CodeGenEngine(repo_path)