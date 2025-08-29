"""Tests for template engine configuration loading."""
import pytest
import yaml
from pathlib import Path
from llm_council.templates import (
    TemplateEngine,
    TemplateConfig,
    AuditorConfig,
    load_template_config,
    validate_template_config
)


class TestTemplateConfig:
    """Test template configuration data structure."""
    
    def test_valid_template_config(self, sample_template_config):
        """Test that valid template configs are accepted."""
        config = TemplateConfig(**sample_template_config)
        
        assert config.project_info["name"] == "Test Template"
        assert "vision" in config.auditor_questions
        assert "pm" in config.auditor_questions["vision"]
        assert len(config.auditor_questions["vision"]["pm"]["key_questions"]) >= 1

    def test_template_config_with_scoring_weights(self, sample_template_config):
        """Test template config with scoring weight adjustments."""
        config = TemplateConfig(**sample_template_config)
        
        assert "vision" in config.scoring_weights
        assert config.scoring_weights["vision"]["pm"] == 1.2
        assert config.scoring_weights["vision"]["ux"] == 1.1

    def test_template_config_missing_required_fields_fails(self):
        """Test that template configs missing required fields fail validation."""
        incomplete_config = {
            "project_info": {
                "name": "Test"
                # Missing description and stages
            }
        }
        
        with pytest.raises(ValueError):
            TemplateConfig(**incomplete_config)


class TestAuditorConfig:
    """Test auditor configuration extraction."""
    
    def test_auditor_config_extraction(self, sample_template_config):
        """Test extracting auditor config for specific stage and role."""
        config = TemplateConfig(**sample_template_config)
        
        auditor_config = config.get_auditor_config("vision", "pm")
        
        assert auditor_config.role == "pm"
        assert auditor_config.stage == "vision"
        assert "product_strategy" in auditor_config.focus_areas
        assert "Is the value proposition clear?" in auditor_config.key_questions
        assert auditor_config.scoring_weight == 1.2

    def test_auditor_config_missing_stage_returns_none(self, sample_template_config):
        """Test that missing stage returns None."""
        config = TemplateConfig(**sample_template_config)
        
        auditor_config = config.get_auditor_config("nonexistent_stage", "pm")
        
        assert auditor_config is None

    def test_auditor_config_missing_role_returns_none(self, sample_template_config):
        """Test that missing role returns None."""
        config = TemplateConfig(**sample_template_config)
        
        auditor_config = config.get_auditor_config("vision", "nonexistent_role")
        
        assert auditor_config is None

    def test_auditor_config_default_weight(self, sample_template_config):
        """Test that auditors without explicit weights get default weight of 1.0."""
        # Add an auditor without weight to test data
        sample_template_config["auditor_questions"]["vision"]["security"] = {
            "focus_areas": ["security_risks"],
            "key_questions": ["Are security risks addressed?"]
        }
        
        config = TemplateConfig(**sample_template_config)
        auditor_config = config.get_auditor_config("vision", "security")
        
        assert auditor_config.scoring_weight == 1.0


class TestTemplateLoading:
    """Test template loading from files."""
    
    def test_load_template_from_file(self, temp_dir, sample_template_config):
        """Test loading template config from YAML file."""
        template_file = temp_dir / "test_template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)
        
        config = load_template_config(template_file)
        
        assert config.project_info["name"] == "Test Template"
        assert "vision" in config.auditor_questions

    def test_load_template_file_not_found(self, temp_dir):
        """Test loading non-existent template file raises error."""
        nonexistent_file = temp_dir / "nonexistent.yaml"
        
        with pytest.raises(FileNotFoundError):
            load_template_config(nonexistent_file)

    def test_load_template_invalid_yaml(self, temp_dir):
        """Test loading invalid YAML raises error."""
        invalid_file = temp_dir / "invalid.yaml"
        with open(invalid_file, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        with pytest.raises(yaml.YAMLError):
            load_template_config(invalid_file)

    def test_load_template_invalid_config_structure(self, temp_dir):
        """Test loading YAML with invalid config structure."""
        invalid_config = {"not_project_info": "invalid"}
        invalid_file = temp_dir / "invalid_config.yaml"
        with open(invalid_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        with pytest.raises(ValueError):
            load_template_config(invalid_file)


class TestTemplateValidation:
    """Test template configuration validation."""
    
    def test_validate_complete_template(self, sample_template_config):
        """Test validation of complete template passes."""
        errors = validate_template_config(sample_template_config)
        assert len(errors) == 0

    def test_validate_missing_stages_in_questions(self):
        """Test validation catches missing stages in auditor questions."""
        config = {
            "project_info": {
                "name": "Test",
                "description": "Test template",
                "stages": ["vision", "prd"]  # Two stages declared
            },
            "auditor_questions": {
                "vision": {"pm": {"focus_areas": [], "key_questions": []}}
                # Missing prd stage
            },
            "scoring_weights": {}
        }
        
        errors = validate_template_config(config)
        assert len(errors) > 0
        assert any("prd" in error for error in errors)

    def test_validate_missing_key_questions(self):
        """Test validation catches auditors without key questions."""
        config = {
            "project_info": {
                "name": "Test",
                "description": "Test template", 
                "stages": ["vision"]
            },
            "auditor_questions": {
                "vision": {
                    "pm": {
                        "focus_areas": ["strategy"],
                        "key_questions": []  # Empty questions
                    }
                }
            },
            "scoring_weights": {}
        }
        
        errors = validate_template_config(config)
        assert len(errors) > 0
        assert any("key_questions" in error for error in errors)

    def test_validate_unknown_roles_in_weights(self, sample_template_config):
        """Test validation catches unknown roles in scoring weights."""
        sample_template_config["scoring_weights"]["vision"]["unknown_role"] = 1.5
        
        errors = validate_template_config(sample_template_config)
        assert len(errors) > 0
        assert any("unknown_role" in error for error in errors)


class TestTemplateEngine:
    """Test template engine orchestration."""
    
    def test_template_engine_initialization(self, temp_dir, sample_template_config):
        """Test template engine initializes correctly."""
        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)
        
        engine = TemplateEngine(template_file)
        
        assert engine.config is not None
        assert engine.config.project_info["name"] == "Test Template"

    def test_get_stage_auditors(self, temp_dir, sample_template_config):
        """Test getting auditors required for a specific stage."""
        template_file = temp_dir / "template.yaml"  
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)
        
        engine = TemplateEngine(template_file)
        auditors = engine.get_stage_auditors("vision")
        
        assert "pm" in auditors
        assert len(auditors) >= 1

    def test_get_auditor_prompt(self, temp_dir, sample_template_config):
        """Test generating prompts for specific auditor."""
        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)
        
        engine = TemplateEngine(template_file)
        prompt = engine.get_auditor_prompt("vision", "pm", "Sample document content")
        
        assert "pm" in prompt.lower() or "product" in prompt.lower()
        assert "vision" in prompt.lower()
        assert "Is the value proposition clear?" in prompt
        assert "Sample document content" in prompt

    def test_get_scoring_weights(self, temp_dir, sample_template_config):
        """Test getting scoring weights for stage."""
        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)
        
        engine = TemplateEngine(template_file)
        weights = engine.get_scoring_weights("vision")
        
        assert weights["pm"] == 1.2
        assert weights["ux"] == 1.1

    def test_fallback_for_missing_auditor_questions(self, temp_dir):
        """Test that engine handles missing auditor questions gracefully."""
        minimal_config = {
            "project_info": {
                "name": "Minimal Template",
                "description": "Basic template",
                "stages": ["vision"]
            },
            "auditor_questions": {},  # Empty questions
            "scoring_weights": {}
        }
        
        template_file = temp_dir / "minimal.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(minimal_config, f)
        
        engine = TemplateEngine(template_file)
        
        # Should not crash and should return empty lists/defaults
        auditors = engine.get_stage_auditors("vision")
        assert auditors == []
        
        prompt = engine.get_auditor_prompt("vision", "pm", "content")
        # Should return a basic fallback prompt
        assert "pm" in prompt.lower()
        assert "vision" in prompt.lower()

    def test_validate_required_auditors_coverage(self, temp_dir, sample_quality_gates):
        """Test validation that all required auditors have questions defined."""
        # Create template missing required auditors from quality gates
        incomplete_config = {
            "project_info": {
                "name": "Incomplete Template",
                "description": "Missing required auditors",
                "stages": ["vision"]
            },
            "auditor_questions": {
                "vision": {
                    "pm": {"focus_areas": [], "key_questions": ["Q1"]}
                    # Missing ux and cost auditors required by quality gates
                }
            },
            "scoring_weights": {}
        }
        
        template_file = temp_dir / "incomplete.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(incomplete_config, f)
        
        engine = TemplateEngine(template_file)
        
        # Should identify missing required auditors
        required_auditors = ["pm", "ux", "cost"]  # From quality gates fixture
        missing = engine.validate_auditor_coverage("vision", required_auditors)
        
        assert "ux" in missing
        assert "cost" in missing
        assert "pm" not in missing