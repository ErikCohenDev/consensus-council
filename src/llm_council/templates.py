"""Template engine for LLM council configuration management."""
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass


@dataclass
class AuditorConfig:
    """Configuration for a specific auditor role and stage."""
    role: str
    stage: str
    focus_areas: List[str]
    key_questions: List[str]
    scoring_weight: float = 1.0


class TemplateConfig:
    """Template configuration with validation and accessors."""
    
    def __init__(self, **config_data):
        self._validate_required_fields(config_data)
        
        self.project_info = config_data["project_info"]
        self.auditor_questions = config_data.get("auditor_questions", {})
        self.scoring_weights = config_data.get("scoring_weights", {})
        self.human_review_policy = config_data.get("human_review_policy", {})
    
    def _validate_required_fields(self, config_data: Dict[str, Any]) -> None:
        """Validate that required fields are present."""
        if "project_info" not in config_data:
            raise ValueError("Template config missing required 'project_info' section")
        
        project_info = config_data["project_info"]
        required_project_fields = ["name", "description", "stages"]
        
        for field in required_project_fields:
            if field not in project_info:
                raise ValueError(f"project_info missing required field: {field}")
    
    def get_auditor_config(self, stage: str, role: str) -> Optional[AuditorConfig]:
        """Get auditor configuration for specific stage and role."""
        if stage not in self.auditor_questions:
            return None
        
        stage_questions = self.auditor_questions[stage]
        if role not in stage_questions:
            return None
        
        auditor_data = stage_questions[role]
        
        # Get scoring weight (default to 1.0)
        scoring_weight = 1.0
        if stage in self.scoring_weights and role in self.scoring_weights[stage]:
            scoring_weight = self.scoring_weights[stage][role]
        
        return AuditorConfig(
            role=role,
            stage=stage,
            focus_areas=auditor_data.get("focus_areas", []),
            key_questions=auditor_data.get("key_questions", []),
            scoring_weight=scoring_weight
        )


def load_template_config(template_path: Path) -> TemplateConfig:
    """Load template configuration from YAML file."""
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    try:
        with open(template_path, 'r') as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML in {template_path}: {e}")
    
    try:
        return TemplateConfig(**config_data)
    except (ValueError, KeyError) as e:
        raise ValueError(f"Invalid template config structure in {template_path}: {e}")


def validate_template_config(config_data: Dict[str, Any]) -> List[str]:
    """Validate template configuration and return list of errors."""
    errors = []
    
    # Check that all declared stages have auditor questions
    if "project_info" in config_data and "stages" in config_data["project_info"]:
        declared_stages = config_data["project_info"]["stages"]
        auditor_questions = config_data.get("auditor_questions", {})
        
        for stage in declared_stages:
            if stage not in auditor_questions:
                errors.append(f"Stage '{stage}' declared but no auditor questions defined")
            else:
                # Check that auditors have key questions
                for role, role_config in auditor_questions[stage].items():
                    key_questions = role_config.get("key_questions", [])
                    if not key_questions:
                        errors.append(f"Auditor '{role}' in stage '{stage}' has no key_questions")
    
    # Check that scoring weights only reference defined auditors
    scoring_weights = config_data.get("scoring_weights", {})
    auditor_questions = config_data.get("auditor_questions", {})
    
    for stage, weights in scoring_weights.items():
        if stage in auditor_questions:
            defined_roles = set(auditor_questions[stage].keys())
            weighted_roles = set(weights.keys())
            
            unknown_roles = weighted_roles - defined_roles
            for role in unknown_roles:
                errors.append(f"Scoring weight defined for unknown role '{role}' in stage '{stage}'")
    
    return errors


class TemplateEngine:
    """Template engine for managing auditor configurations and prompts."""
    
    def __init__(self, template_path: Path):
        self.template_path = template_path
        self.config = load_template_config(template_path)
    
    def get_stage_auditors(self, stage: str) -> List[str]:
        """Get list of auditor roles configured for a stage."""
        if stage not in self.config.auditor_questions:
            return []
        
        return list(self.config.auditor_questions[stage].keys())
    
    def get_auditor_prompt(self, stage: str, role: str, document_content: str) -> str:
        """Generate prompt for specific auditor role and stage."""
        auditor_config = self.config.get_auditor_config(stage, role)
        
        if auditor_config is None:
            # Fallback prompt for missing configuration
            return self._generate_fallback_prompt(stage, role, document_content)
        
        # Build structured prompt
        prompt_parts = [
            f"You are a {role.upper()} auditor reviewing a {stage.upper()} document.",
            "",
            f"Focus Areas: {', '.join(auditor_config.focus_areas)}",
            "",
            "Key Questions to Address:",
        ]
        
        for i, question in enumerate(auditor_config.key_questions, 1):
            prompt_parts.append(f"{i}. {question}")
        
        prompt_parts.extend([
            "",
            "Document to Review:",
            "=" * 50,
            document_content,
            "=" * 50,
            "",
            "Please provide your assessment following the standard auditor response schema."
        ])
        
        return "\n".join(prompt_parts)
    
    def _generate_fallback_prompt(self, stage: str, role: str, document_content: str) -> str:
        """Generate basic fallback prompt when configuration is missing."""
        return f"""You are a {role.upper()} auditor reviewing a {stage.upper()} document.

Please evaluate this document from your {role} perspective and provide feedback on:
- Overall quality and completeness
- Areas of concern from your expertise
- Specific improvements needed

Document to Review:
{'=' * 50}
{document_content}
{'=' * 50}

Please provide your assessment following the standard auditor response schema."""
    
    def get_scoring_weights(self, stage: str) -> Dict[str, float]:
        """Get scoring weights for all auditors in a stage."""
        if stage not in self.config.scoring_weights:
            # Return default weights (1.0) for all auditors in this stage
            auditors = self.get_stage_auditors(stage)
            return {auditor: 1.0 for auditor in auditors}
        
        stage_weights = self.config.scoring_weights[stage].copy()
        
        # Fill in default weights for auditors without explicit weights
        auditors = self.get_stage_auditors(stage)
        for auditor in auditors:
            if auditor not in stage_weights:
                stage_weights[auditor] = 1.0
        
        return stage_weights
    
    def validate_auditor_coverage(self, stage: str, required_auditors: List[str]) -> List[str]:
        """Validate that all required auditors have questions defined for stage."""
        configured_auditors = set(self.get_stage_auditors(stage))
        required_auditors_set = set(required_auditors)
        
        missing_auditors = required_auditors_set - configured_auditors
        return list(missing_auditors)
    
    def get_human_review_policy(self, stage: str) -> Dict[str, Any]:
        """Get human review policy for stage."""
        return self.config.human_review_policy.get(stage, {
            "required": True,
            "rationale": "Default human review policy",
            "key_decisions": []
        })
    
    def get_template_content(self) -> str:
        """Get template file content as string for cache key generation."""
        try:
            return self.template_path.read_text(encoding="utf-8")
        except Exception:
            return ""