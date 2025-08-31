"""
Tests for paradigm engine service.

VERIFIES: R-PRD-016 (paradigm framework selection)
VALIDATES: YC, McKinsey, Lean Startup, Design Thinking frameworks
TEST_TYPE: Unit + Integration
LAST_SYNC: 2025-08-30
"""

import pytest
from unittest.mock import Mock, patch
import yaml
import json

from src.llm_council.services.paradigm_engine import ParadigmEngine
from src.llm_council.models.se_models import ParadigmFramework, ParadigmQuestion


class TestParadigmEngine:
    """Test paradigm engine framework selection and question generation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.engine = ParadigmEngine()

    def test_supported_frameworks_available(self):
        """
        VERIFIES: R-PRD-016 (framework selection support)
        SCENARIO: System provides multiple paradigm framework options
        """
        frameworks = self.engine.get_supported_frameworks()
        
        assert len(frameworks) >= 4
        framework_names = [f.framework_id for f in frameworks]
        
        # Verify core frameworks are supported
        assert "yc_startup" in framework_names
        assert "mckinsey_problem_solving" in framework_names 
        assert "lean_startup" in framework_names
        assert "design_thinking" in framework_names
        
        # Verify framework metadata
        yc_framework = next(f for f in frameworks if f.framework_id == "yc_startup")
        assert yc_framework.name == "YC Startup Framework"
        assert "market" in yc_framework.description.lower()
        assert len(yc_framework.focus_areas) >= 3

    def test_yc_framework_question_generation(self):
        """
        VERIFIES: YC startup framework question set
        SCENARIO: YC framework generates market-first questions
        """
        questions = self.engine.get_framework_questions("yc_startup")
        
        assert len(questions) >= 8
        question_texts = [q.text.lower() for q in questions]
        
        # Verify YC-specific questions are present
        assert any("market" in text for text in question_texts)
        assert any("problem" in text for text in question_texts)
        assert any("solution" in text for text in question_texts)
        assert any("customer" in text for text in question_texts)
        assert any("competition" in text for text in question_texts)
        assert any("business model" in text for text in question_texts)
        
        # Verify question structure
        market_question = next(q for q in questions if "market" in q.text.lower())
        assert market_question.question_type in ["strategic", "market_analysis"]
        assert market_question.weight >= 1.5  # High importance for YC
        assert market_question.human_input_required == True

    def test_mckinsey_framework_question_generation(self):
        """
        VERIFIES: McKinsey problem-solving framework questions
        SCENARIO: McKinsey framework generates structured problem-solving questions
        """
        questions = self.engine.get_framework_questions("mckinsey_problem_solving")
        
        assert len(questions) >= 6
        question_texts = [q.text.lower() for q in questions]
        
        # Verify McKinsey MECE and hypothesis-driven questions
        assert any("problem definition" in text for text in question_texts)
        assert any("hypothesis" in text for text in question_texts)
        assert any("structure" in text for text in question_texts)
        assert any("data" in text or "evidence" in text for text in question_texts)
        assert any("recommendation" in text for text in question_texts)
        
        # Verify McKinsey-specific characteristics
        hypothesis_question = next(q for q in questions if "hypothesis" in q.text.lower())
        assert hypothesis_question.requires_evidence == True
        assert hypothesis_question.human_input_required == True

    def test_lean_startup_framework_question_generation(self):
        """
        VERIFIES: Lean Startup framework question set
        SCENARIO: Lean framework generates hypothesis-driven validation questions
        """
        questions = self.engine.get_framework_questions("lean_startup")
        
        assert len(questions) >= 7
        question_texts = [q.text.lower() for q in questions]
        
        # Verify Lean Startup Build-Measure-Learn questions
        assert any("hypothesis" in text for text in question_texts)
        assert any("experiment" in text for text in question_texts)
        assert any("metric" in text for text in question_texts)
        assert any("mvp" in text for text in question_texts)
        assert any("learn" in text or "validate" in text for text in question_texts)
        
        # Verify Lean-specific validation approach
        experiment_question = next(q for q in questions if "experiment" in q.text.lower())
        assert experiment_question.validation_method in ["experiment", "user_test", "a_b_test"]

    def test_design_thinking_framework_question_generation(self):
        """
        VERIFIES: Design Thinking framework question set
        SCENARIO: Design Thinking framework generates user-centered questions
        """
        questions = self.engine.get_framework_questions("design_thinking")
        
        assert len(questions) >= 6
        question_texts = [q.text.lower() for q in questions]
        
        # Verify Design Thinking user-centered questions
        assert any("user" in text for text in question_texts)
        assert any("empathy" in text or "understand" in text for text in question_texts)
        assert any("prototype" in text for text in question_texts)
        assert any("test" in text for text in question_texts)
        assert any("iterate" in text for text in question_texts)
        
        # Verify Design Thinking process focus
        empathy_question = next(q for q in questions if "user" in q.text.lower())
        assert empathy_question.stage in ["empathize", "define", "ideate"]

    def test_framework_question_customization(self):
        """
        VERIFIES: Framework question customization based on project context
        SCENARIO: Questions adapt based on project type and context
        """
        # Test with different project contexts
        software_context = {
            "project_type": "software_product",
            "team_size": "small",
            "market_maturity": "emerging"
        }
        
        hardware_context = {
            "project_type": "hardware_product", 
            "team_size": "large",
            "market_maturity": "established"
        }
        
        # Get customized questions for different contexts
        yc_software_questions = self.engine.get_framework_questions("yc_startup", software_context)
        yc_hardware_questions = self.engine.get_framework_questions("yc_startup", hardware_context)
        
        # Verify customization occurred
        assert len(yc_software_questions) != len(yc_hardware_questions)
        
        software_texts = [q.text.lower() for q in yc_software_questions]
        hardware_texts = [q.text.lower() for q in yc_hardware_questions]
        
        # Software context should emphasize different aspects than hardware
        assert any("software" in text or "app" in text for text in software_texts)
        assert any("manufacturing" in text or "supply chain" in text for text in hardware_texts)

    def test_paradigm_answer_validation(self):
        """
        VERIFIES: Paradigm answer validation and quality checking
        SCENARIO: Validate user answers meet framework requirements
        """
        framework_id = "yc_startup"
        questions = self.engine.get_framework_questions(framework_id)
        
        # Create valid answers
        valid_answers = {
            "market_size": "Health app market $4.2B, growing 15% annually",
            "target_customer": "Health-conscious professionals aged 25-45",
            "problem_validation": "67% of users struggle with hydration tracking (survey of 500 users)",
            "unique_solution": "Automated tracking with ML-powered reminder optimization",
            "mvp_scope": "Water logging + smart reminders + basic analytics"
        }
        
        # Create incomplete answers
        incomplete_answers = {
            "market_size": "Big market",  # Too vague
            "target_customer": "",        # Empty
            # Missing other required answers
        }
        
        # Test validation
        valid_result = self.engine.validate_paradigm_answers(framework_id, valid_answers)
        invalid_result = self.engine.validate_paradigm_answers(framework_id, incomplete_answers)
        
        assert valid_result.is_valid == True
        assert len(valid_result.validation_errors) == 0
        assert valid_result.completeness_score >= 0.8
        
        assert invalid_result.is_valid == False
        assert len(invalid_result.validation_errors) >= 2
        assert invalid_result.completeness_score < 0.5

    def test_framework_switching_and_migration(self):
        """
        VERIFIES: Framework switching capability
        SCENARIO: User switches from one framework to another mid-process
        """
        # Step 1: Start with YC framework and partial answers
        initial_framework = "yc_startup"
        yc_answers = {
            "market_size": "Health app market $4.2B",
            "target_customer": "Health-conscious professionals"
        }
        
        # Step 2: Switch to Lean Startup framework
        new_framework = "lean_startup"
        
        # Test migration of applicable answers
        migrated_answers = self.engine.migrate_answers_between_frameworks(
            initial_framework, new_framework, yc_answers
        )
        
        assert len(migrated_answers) <= len(yc_answers)  # Some answers may not transfer
        
        # Verify common concepts transferred
        if "target_customer" in yc_answers:
            assert "target_segment" in migrated_answers or "user_persona" in migrated_answers
        
        # Step 3: Get new questions for Lean framework
        lean_questions = self.engine.get_framework_questions(new_framework)
        lean_question_ids = [q.question_id for q in lean_questions]
        
        # Verify framework-specific questions
        assert any("hypothesis" in qid for qid in lean_question_ids)
        assert any("experiment" in qid for qid in lean_question_ids)

    def test_llm_assisted_answer_generation(self):
        """
        VERIFIES: LLM assistance for paradigm question answering
        SCENARIO: LLM provides suggested answers, human refines
        """
        framework_id = "yc_startup"
        user_idea = "Water tracking app for health-conscious professionals"
        
        question = ParadigmQuestion(
            question_id="market_size_analysis",
            text="What is the total addressable market (TAM) for your solution?",
            question_type="market_analysis",
            weight=2.0,
            human_input_required=True
        )
        
        # Mock LLM response for market analysis
        with patch.object(self.engine, '_get_llm_suggestion') as mock_llm:
            mock_llm.return_value = {
                "suggested_answer": "Global health app market estimated at $4.2B (2024), growing 15% CAGR",
                "confidence": 0.7,
                "supporting_evidence": [
                    "WHO health technology report 2024",
                    "App Annie health app market analysis"
                ],
                "follow_up_questions": [
                    "What specific geographic markets will you target first?",
                    "How will you differentiate from existing health apps?"
                ]
            }
            
            suggestion = self.engine.get_llm_answer_suggestion(question, user_idea)
        
        assert suggestion is not None
        assert "4.2B" in suggestion["suggested_answer"]
        assert suggestion["confidence"] >= 0.5
        assert len(suggestion["supporting_evidence"]) >= 2
        assert len(suggestion["follow_up_questions"]) >= 1

    def test_paradigm_framework_validation(self):
        """
        VERIFIES: Paradigm framework configuration validation
        SCENARIO: Validate framework configs are properly structured
        """
        # Test each supported framework has valid configuration
        frameworks = self.engine.get_supported_frameworks()
        
        for framework in frameworks:
            # Verify required fields
            assert framework.framework_id is not None
            assert framework.name is not None
            assert framework.description is not None
            assert len(framework.focus_areas) >= 2
            
            # Get questions for framework
            questions = self.engine.get_framework_questions(framework.framework_id)
            assert len(questions) >= 5
            
            # Verify question quality
            for question in questions:
                assert question.question_id is not None
                assert question.text is not None
                assert question.weight > 0
                assert question.question_type in [
                    "strategic", "market_analysis", "problem_validation",
                    "solution_design", "resource_planning", "risk_assessment"
                ]


class TestParadigmIntegration:
    """Test paradigm engine integration with other pipeline components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.engine = ParadigmEngine()

    def test_paradigm_to_entity_extraction_integration(self):
        """
        VERIFIES: Integration between paradigm answers and entity extraction
        SCENARIO: Paradigm answers enhance entity extraction quality
        """
        paradigm_answers = {
            "target_customer": "Health-conscious professionals aged 25-45",
            "problem_validation": "67% struggle with hydration tracking",
            "unique_solution": "Automated water tracking with smart notifications"
        }
        
        # Test that paradigm context enhances entity extraction
        enhanced_context = self.engine.enhance_entity_extraction_context(paradigm_answers)
        
        assert "target_customer" in enhanced_context
        assert "professionals" in enhanced_context["target_customer"]
        assert "problem_validation" in enhanced_context
        assert "67%" in enhanced_context["problem_validation"]

    def test_paradigm_to_research_expansion_integration(self):
        """
        VERIFIES: Integration between paradigm selection and research expansion  
        SCENARIO: Framework choice influences research focus areas
        """
        # YC framework should focus on market research
        yc_research_focus = self.engine.get_research_focus_areas("yc_startup")
        assert "market_size" in yc_research_focus
        assert "competition_analysis" in yc_research_focus
        assert "customer_acquisition" in yc_research_focus
        
        # McKinsey framework should focus on problem structure
        mckinsey_research_focus = self.engine.get_research_focus_areas("mckinsey_problem_solving")
        assert "problem_decomposition" in mckinsey_research_focus
        assert "data_analysis" in mckinsey_research_focus
        assert "solution_evaluation" in mckinsey_research_focus
        
        # Design Thinking should focus on user research
        dt_research_focus = self.engine.get_research_focus_areas("design_thinking")
        assert "user_research" in dt_research_focus
        assert "empathy_mapping" in dt_research_focus
        assert "prototype_testing" in dt_research_focus

    def test_paradigm_answer_to_document_generation(self):
        """
        VERIFIES: Paradigm answers flow into document generation
        SCENARIO: Framework answers populate vision and PRD documents
        """
        framework_id = "yc_startup"
        paradigm_answers = {
            "market_size": "Health app market $4.2B, growing 15% annually",
            "target_customer": "Health-conscious professionals aged 25-45",
            "problem_validation": "67% of users struggle with hydration tracking",
            "unique_solution": "Automated tracking with smart notifications",
            "mvp_scope": "Water logging + reminders + progress tracking",
            "business_model": "Freemium with premium analytics"
        }
        
        # Generate document templates from paradigm answers
        vision_template = self.engine.generate_vision_template(framework_id, paradigm_answers)
        prd_template = self.engine.generate_prd_template(framework_id, paradigm_answers)
        
        # Verify vision template incorporates answers
        assert "Health app market $4.2B" in vision_template
        assert "Health-conscious professionals" in vision_template
        assert "hydration tracking" in vision_template
        
        # Verify PRD template incorporates technical scope
        assert "Water logging" in prd_template
        assert "reminders" in prd_template
        assert "progress tracking" in prd_template


class TestParadigmQuestionTypes:
    """Test different paradigm question types and their behaviors."""
    
    def setup_method(self):
        """Set up test environment."""
        self.engine = ParadigmEngine()

    def test_strategic_questions_require_human_input(self):
        """
        VERIFIES: Strategic questions require human input
        SCENARIO: High-weight strategic questions cannot be auto-answered
        """
        strategic_questions = self.engine.get_questions_by_type("strategic")
        
        for question in strategic_questions:
            assert question.human_input_required == True
            assert question.weight >= 1.8  # Strategic questions have high weight
            assert question.can_be_auto_answered == False

    def test_market_analysis_questions_support_research(self):
        """
        VERIFIES: Market analysis questions can leverage research data
        SCENARIO: Market questions can be enhanced with research insights
        """
        market_questions = self.engine.get_questions_by_type("market_analysis")
        
        for question in market_questions:
            assert question.supports_research_enhancement == True
            assert "market" in question.text.lower() or "competition" in question.text.lower()

    def test_technical_questions_leverage_llm_knowledge(self):
        """
        VERIFIES: Technical questions can be primarily LLM-answered
        SCENARIO: Technical implementation questions use LLM expertise
        """
        technical_questions = self.engine.get_questions_by_type("technical_planning")
        
        for question in technical_questions:
            assert question.can_be_auto_answered == True
            assert question.human_input_required == False or question.human_input_preferred == True

    def test_question_dependency_resolution(self):
        """
        VERIFIES: Question dependencies are properly resolved
        SCENARIO: Some questions depend on answers to previous questions
        """
        framework_id = "yc_startup"
        questions = self.engine.get_framework_questions(framework_id)
        
        # Find questions with dependencies
        dependent_questions = [q for q in questions if q.depends_on]
        
        if dependent_questions:
            dep_question = dependent_questions[0]
            
            # Verify dependency resolution
            dependency_tree = self.engine.resolve_question_dependencies(framework_id)
            
            assert dep_question.question_id in dependency_tree
            assert len(dependency_tree[dep_question.question_id]) > 0

    def test_paradigm_config_loading_and_validation(self):
        """
        VERIFIES: Paradigm configurations are properly loaded and validated
        SCENARIO: Framework configs load from YAML with proper validation
        """
        # Test loading YC framework config
        yc_config = self.engine._load_framework_config("yc_startup")
        
        assert yc_config is not None
        assert "questions" in yc_config
        assert "focus_areas" in yc_config
        assert "validation_rules" in yc_config
        
        # Verify question structure in config
        questions_config = yc_config["questions"]
        assert len(questions_config) >= 5
        
        for question_config in questions_config:
            assert "question_id" in question_config
            assert "text" in question_config
            assert "weight" in question_config
            assert question_config["weight"] > 0


class TestParadigmMetrics:
    """Test paradigm framework effectiveness metrics."""
    
    def setup_method(self):
        """Set up test environment."""
        self.engine = ParadigmEngine()

    def test_framework_effectiveness_scoring(self):
        """
        VERIFIES: Framework effectiveness can be measured and scored
        SCENARIO: Track which frameworks produce better outcomes
        """
        framework_usage = {
            "yc_startup": {
                "projects_completed": 15,
                "avg_consensus_score": 4.2,
                "avg_success_metrics": 0.78
            },
            "lean_startup": {
                "projects_completed": 8,
                "avg_consensus_score": 3.9,
                "avg_success_metrics": 0.71
            }
        }
        
        effectiveness_scores = self.engine.calculate_framework_effectiveness(framework_usage)
        
        assert "yc_startup" in effectiveness_scores
        assert "lean_startup" in effectiveness_scores
        assert effectiveness_scores["yc_startup"] > effectiveness_scores["lean_startup"]

    def test_paradigm_question_quality_metrics(self):
        """
        VERIFIES: Question quality can be measured and improved
        SCENARIO: Track question effectiveness and user satisfaction
        """
        question_metrics = {
            "market_size_analysis": {
                "completion_rate": 0.95,
                "human_satisfaction": 4.3,
                "answer_quality_score": 0.82
            },
            "problem_validation": {
                "completion_rate": 0.87,
                "human_satisfaction": 4.1,
                "answer_quality_score": 0.79
            }
        }
        
        quality_analysis = self.engine.analyze_question_quality(question_metrics)
        
        assert quality_analysis["top_performing_questions"] is not None
        assert quality_analysis["questions_needing_improvement"] is not None
        assert "market_size_analysis" in quality_analysis["top_performing_questions"]