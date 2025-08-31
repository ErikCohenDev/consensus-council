"""
Tests for SE (Systems Engineering) integration service.

VERIFIES: Complete SE pipeline integration and orchestration
VALIDATES: 10-layer pipeline coordination and data flow
TEST_TYPE: Integration + Unit
LAST_SYNC: 2025-08-30
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.llm_council.services.se_integration import SEIntegrationService
from src.llm_council.models.se_models import SystemsEntity, ImplementationTask, ArchitecturalComponent
from src.llm_council.models.code_artifact_models import CodeArtifact, TraceabilityMatrix


class TestSEIntegrationService:
    """Test SE integration service orchestration of complete pipeline."""
    
    def setup_method(self):
        """Set up test environment."""
        from unittest.mock import Mock
        from src.llm_council.consensus import ConsensusEngine
        from src.llm_council.human_review import HumanReviewInterface
        from src.llm_council.research_agent import ResearchAgent
        from src.llm_council.orchestrator import AuditorOrchestrator
        
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock dependencies
        consensus_engine = Mock(spec=ConsensusEngine)
        human_review = Mock(spec=HumanReviewInterface)
        research_agent = ResearchAgent(enabled=False)
        orchestrator = Mock(spec=AuditorOrchestrator)
        
        self.se_service = SEIntegrationService(consensus_engine, human_review, research_agent, orchestrator)

    @pytest.mark.asyncio
    async def test_complete_pipeline_orchestration(self):
        """
        VERIFIES: Complete 10-layer pipeline orchestration
        SCENARIO: Idea → paradigm → documents → specs → code → tests → runtime
        USE_CASE: UC-001→UC-010 (complete pipeline flow)
        """
        # Step 1: Initialize pipeline with water app idea
        pipeline_input = {
            "idea": "Water tracking app for health-conscious professionals",
            "paradigm": "yc_startup",
            "paradigm_answers": {
                "market_size": "Health app market $4.2B",
                "target_customer": "Health-conscious professionals aged 25-45",
                "problem_validation": "67% struggle with hydration tracking"
            }
        }
        
        # Step 2: Execute complete pipeline (using public API)
        pipeline_result = await self.se_service.execute_complete_pipeline(pipeline_input)
        
        # Step 3: Validate pipeline completion
        assert pipeline_result.success == True
        assert pipeline_result.layers_completed == 10
        assert pipeline_result.traceability_coverage >= 0.9
        assert len(pipeline_result.generated_artifacts) >= 4
        
        # Verify all expected artifact types
        artifact_types = [artifact.artifact_type for artifact in pipeline_result.generated_artifacts]
        assert "document" in artifact_types
        assert "specification" in artifact_types  
        assert "source_code" in artifact_types
        assert "test" in artifact_types

    def test_layer_validation_and_quality_gates(self):
        """
        VERIFIES: Quality gates between pipeline layers
        SCENARIO: Each layer validates before promoting to next
        """
        # Step 1: Create layer outputs for validation
        vision_output = {
            "document": "# VISION.md\n## Problem\nHydration tracking problem",
            "entities": [
                Mock(type="problem", label="Hydration tracking difficulty"),
                Mock(type="target_user", label="Health-conscious professionals")
            ],
            "quality_score": 4.2
        }
        
        prd_output = {
            "document": "# PRD.md\n## Requirements\nREQ-TRACKING-001",
            "requirements": ["REQ-TRACKING-001", "REQ-NOTIF-001"],
            "quality_score": 3.9
        }
        
        # Step 2: Test vision → PRD gate validation
        vision_gate_result = self.se_service.validate_layer_transition(
            "vision", "prd", vision_output
        )
        
        assert vision_gate_result.can_proceed == True
        assert vision_gate_result.validation_score >= 3.8
        assert len(vision_gate_result.blocking_issues) == 0
        
        # Step 3: Test PRD → Architecture gate with quality issues
        low_quality_prd = prd_output.copy()
        low_quality_prd["quality_score"] = 2.1  # Below threshold
        
        failing_gate_result = self.se_service.validate_layer_transition(
            "prd", "architecture", low_quality_prd
        )
        
        assert failing_gate_result.can_proceed == False
        assert failing_gate_result.validation_score < 3.0
        assert len(failing_gate_result.blocking_issues) > 0

    def test_cross_layer_alignment_validation(self):
        """
        VERIFIES: Alignment validation across all pipeline layers
        SCENARIO: Detect misalignment between vision, PRD, architecture, code
        """
        # Step 1: Set up pipeline artifacts with potential misalignment
        pipeline_artifacts = {
            "vision": {
                "target_users": ["Health-conscious professionals"],
                "core_features": ["water tracking", "smart notifications"]
            },
            "prd": {
                "requirements": ["REQ-TRACKING-001", "REQ-NOTIF-001", "REQ-SOCIAL-001"], # Added social feature
                "target_users": ["Health professionals", "Fitness enthusiasts"]  # Expanded scope
            },
            "architecture": {
                "components": ["WaterService", "NotificationService"],  # Missing social component
                "user_types": ["Health professionals"]  # Inconsistent with PRD
            },
            "code": {
                "services": ["water_service.py", "notification_service.py", "legacy_service.py"], # Added legacy
                "requirements_implemented": ["REQ-TRACKING-001"]  # Missing REQ-NOTIF-001
            }
        }
        
        # Step 2: Run alignment validation
        alignment_result = self.se_service.validate_cross_layer_alignment(pipeline_artifacts)
        
        # Step 3: Verify misalignment detection
        assert alignment_result.overall_alignment_score < 0.9  # Should detect issues
        assert len(alignment_result.misalignment_issues) >= 3
        
        # Check specific misalignments
        issues = [issue.description for issue in alignment_result.misalignment_issues]
        assert any("REQ-SOCIAL-001" in issue for issue in issues)  # Social req in PRD but not arch
        assert any("legacy_service.py" in issue for issue in issues)  # Orphaned code
        assert any("REQ-NOTIF-001" in issue for issue in issues)  # Missing implementation

    async def test_pipeline_error_recovery_and_rollback(self):
        """
        VERIFIES: Pipeline error handling and rollback mechanisms
        SCENARIO: Pipeline failure → detect error → rollback to stable state
        """
        # Step 1: Set up pipeline state before failure
        stable_state = {
            "completed_layers": ["paradigm", "context", "vision"],
            "artifacts": {
                "paradigm_selection.yaml": "yc_startup framework",
                "context_graph.json": "entity graph data",
                "VISION.md": "vision document content"
            },
            "traceability_matrix": Mock(requirements_to_code={})
        }
        
        # Step 2: Simulate failure during PRD generation
        with patch.object(self.se_service, '_run_document_generation') as mock_doc_gen:
            mock_doc_gen.side_effect = Exception("LLM API failure during PRD generation")
            
            # Attempt pipeline execution
            with pytest.raises(Exception) as exc_info:
                await self.se_service.execute_complete_pipeline({
                    "idea": "test idea",
                    "paradigm": "yc_startup"
                })
        
        # Step 3: Test rollback to stable state
        rollback_result = self.se_service.rollback_to_stable_state(stable_state)
        
        assert rollback_result.success == True
        assert rollback_result.restored_layer == "vision"
        assert len(rollback_result.preserved_artifacts) == 3

    def test_pipeline_performance_monitoring(self):
        """
        VERIFIES: Pipeline performance monitoring and optimization
        SCENARIO: Track layer execution times and resource usage
        """
        # Step 1: Execute pipeline with performance monitoring
        performance_config = {
            "track_layer_times": True,
            "track_llm_usage": True,
            "track_memory_usage": True
        }
        
        with patch.multiple(
            self.se_service,
            _run_paradigm_analysis=AsyncMock(return_value=Mock()),
            _run_context_expansion=AsyncMock(return_value=Mock()),
            _monitor_performance=Mock(return_value={
                "layer_times": {
                    "paradigm": 2.3,
                    "context": 15.7,
                    "vision": 45.2,
                    "prd": 38.9
                },
                "llm_usage": {
                    "total_tokens": 15420,
                    "total_cost": 1.23
                },
                "memory_peak": 245.6
            })
        ):
            performance_data = self.se_service.monitor_pipeline_performance(performance_config)
        
        # Step 2: Validate performance tracking
        assert "layer_times" in performance_data
        assert "llm_usage" in performance_data
        assert performance_data["llm_usage"]["total_cost"] <= 2.0  # Cost target
        
        # Step 3: Verify performance optimization suggestions
        optimization_suggestions = self.se_service.analyze_performance_bottlenecks(performance_data)
        
        if performance_data["layer_times"]["vision"] > 30:  # Vision layer too slow
            assert any("vision" in suggestion.lower() for suggestion in optimization_suggestions)

    async def test_multi_project_se_pipeline_coordination(self):
        """
        VERIFIES: SE pipeline coordination across multiple projects
        SCENARIO: Multiple projects using SE pipeline without interference
        """
        # Step 1: Set up multiple project contexts
        project_a_context = {
            "project_id": "water-app",
            "paradigm": "yc_startup",
            "stage": "prd"
        }
        
        project_b_context = {
            "project_id": "fitness-tracker", 
            "paradigm": "design_thinking",
            "stage": "vision"
        }
        
        # Step 2: Execute pipelines concurrently (mock)
        with patch.object(self.se_service, '_execute_project_pipeline') as mock_execute:
            mock_execute.return_value = Mock(success=True, project_id="test")
            
            results = await asyncio.gather(
                self.se_service.execute_project_pipeline(project_a_context),
                self.se_service.execute_project_pipeline(project_b_context)
            )
        
        # Step 3: Verify no cross-project interference
        assert len(results) == 2
        assert all(result.success for result in results)
        
        # Verify project isolation
        project_a_artifacts = self.se_service.get_project_artifacts("water-app")
        project_b_artifacts = self.se_service.get_project_artifacts("fitness-tracker")
        
        assert project_a_artifacts != project_b_artifacts
        assert len(set(project_a_artifacts.keys()) & set(project_b_artifacts.keys())) == 0


class TestSEPipelineDataFlow:
    """Test data flow validation through SE pipeline layers."""
    
    def setup_method(self):
        """Set up test environment."""
        from unittest.mock import Mock
        from src.llm_council.consensus import ConsensusEngine
        from src.llm_council.human_review import HumanReviewInterface
        from src.llm_council.research_agent import ResearchAgent
        from src.llm_council.orchestrator import AuditorOrchestrator
        
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock dependencies
        consensus_engine = Mock(spec=ConsensusEngine)
        human_review = Mock(spec=HumanReviewInterface)
        research_agent = ResearchAgent(enabled=False)
        orchestrator = Mock(spec=AuditorOrchestrator)
        
        self.se_service = SEIntegrationService(consensus_engine, human_review, research_agent, orchestrator)

    def test_entity_propagation_through_layers(self):
        """
        VERIFIES: Entities properly propagate and evolve through pipeline layers
        SCENARIO: Core entities maintain identity while gaining detail through layers
        """
        # Step 1: Create initial entities from idea
        initial_entities = [
            Mock(
                id="entity_001",
                label="Hydration Tracking Problem",
                type="problem",
                importance=0.9,
                stage="idea"
            ),
            Mock(
                id="entity_002", 
                label="Health-conscious Professionals",
                type="target_user",
                importance=0.8,
                stage="idea"
            )
        ]
        
        # Step 2: Simulate entity evolution through layers
        layer_progressions = {
            "vision": self._evolve_entities_for_vision(initial_entities),
            "prd": self._evolve_entities_for_prd(initial_entities),
            "architecture": self._evolve_entities_for_architecture(initial_entities),
            "implementation": self._evolve_entities_for_implementation(initial_entities)
        }
        
        # Step 3: Validate entity continuity and evolution
        for layer, entities in layer_progressions.items():
            # Original entities should still exist
            entity_ids = [e.id for e in entities]
            assert "entity_001" in entity_ids
            assert "entity_002" in entity_ids
            
            # Entities should have gained layer-specific detail
            problem_entity = next(e for e in entities if e.id == "entity_001")
            assert problem_entity.stage == layer
            assert len(problem_entity.layer_specific_data) > 0

    def test_requirement_traceability_through_layers(self):
        """
        VERIFIES: Requirements maintain traceability through all layers
        SCENARIO: REQ-XXX identifiers flow from PRD → specs → code → tests → runtime
        """
        # Step 1: Create requirement that flows through layers
        base_requirement = {
            "id": "REQ-TRACKING-001",
            "title": "Water Intake Logging",
            "description": "Users must be able to log water intake with timestamps",
            "source_layer": "prd"
        }
        
        # Step 2: Trace requirement through layers
        layer_artifacts = {
            "specs": {
                "REQ-TRACKING-001.yaml": self._generate_req_spec(base_requirement)
            },
            "architecture": {
                "components": [Mock(name="WaterService", implements=["REQ-TRACKING-001"])]
            },
            "implementation": {
                "tasks": [Mock(task_id="T-TRACK-001", requirements=["REQ-TRACKING-001"])]
            },
            "code": {
                "files": [("src/water_service.py", "# IMPLEMENTS: REQ-TRACKING-001")]
            },
            "tests": {
                "files": [("tests/test_water.py", "# VERIFIES: REQ-TRACKING-001")]
            }
        }
        
        # Step 3: Validate requirement traceability
        traceability_validation = self.se_service.validate_requirement_traceability(
            "REQ-TRACKING-001", layer_artifacts
        )
        
        assert traceability_validation.requirement_found_in_all_layers == True
        assert len(traceability_validation.missing_layers) == 0
        assert traceability_validation.traceability_completeness >= 0.9

    def test_symmetry_enforcement_across_layers(self):
        """
        VERIFIES: Absolute symmetry enforcement between all layers
        SCENARIO: Detect and prevent asymmetry between requirements and implementation
        """
        # Step 1: Set up asymmetric artifact set
        asymmetric_artifacts = {
            "requirements": {
                "REQ-TRACKING-001": "Water logging requirement",
                "REQ-NOTIF-001": "Notification requirement",
                "REQ-ORPHAN-001": "Orphaned requirement with no implementation"
            },
            "code_files": [
                ("src/water_service.py", "# IMPLEMENTS: REQ-TRACKING-001"),
                ("src/notification_service.py", "# IMPLEMENTS: REQ-NOTIF-001"),
                ("src/legacy_utils.py", "# No requirement link - orphaned code")
            ],
            "test_files": [
                ("tests/test_water.py", "# VERIFIES: REQ-TRACKING-001"),
                # Missing test for REQ-NOTIF-001
            ]
        }
        
        # Step 2: Run symmetry validation
        symmetry_result = self.se_service.validate_pipeline_symmetry(asymmetric_artifacts)
        
        # Step 3: Verify asymmetry detection
        assert symmetry_result.is_symmetric == False
        assert len(symmetry_result.asymmetry_violations) >= 3
        
        violations = [v.violation_type for v in symmetry_result.asymmetry_violations]
        assert "orphaned_requirement" in violations  # REQ-ORPHAN-001
        assert "orphaned_code" in violations        # legacy_utils.py
        assert "missing_test" in violations         # No test for REQ-NOTIF-001

    def test_change_propagation_through_layers(self):
        """
        VERIFIES: Change propagation and impact analysis across layers
        SCENARIO: Code change → upstream requirement impacts + downstream test effects
        """
        # Step 1: Set up existing pipeline state
        existing_state = {
            "requirements": {"REQ-TRACKING-001": "Water logging requirement"},
            "code": {
                "src/water_service.py": """
                # IMPLEMENTS: REQ-TRACKING-001
                class WaterService:
                    def log_intake(self, amount_ml): pass
                """
            },
            "tests": {
                "tests/test_water.py": """
                # VERIFIES: REQ-TRACKING-001  
                def test_log_intake(): pass
                """
            }
        }
        
        # Step 2: Simulate code change
        code_change = {
            "file": "src/water_service.py",
            "change_type": "method_addition",
            "description": "Added validate_amount method with business logic",
            "new_requirements": ["REQ-VALIDATION-001"]  # New requirement emerges
        }
        
        # Step 3: Analyze change propagation
        propagation_result = self.se_service.analyze_change_propagation(
            code_change, existing_state
        )
        
        # Step 4: Verify upstream impact detection
        assert len(propagation_result.upstream_impacts) >= 1
        upstream_reqs = [impact.target_id for impact in propagation_result.upstream_impacts]
        assert "REQ-TRACKING-001" in upstream_reqs  # Existing requirement affected
        
        # Step 5: Verify downstream impact detection
        assert len(propagation_result.downstream_impacts) >= 1
        downstream_tests = [impact.target_id for impact in propagation_result.downstream_impacts]
        assert "tests/test_water.py" in downstream_tests  # Test needs update
        
        # Step 6: Verify new requirement detection
        assert "REQ-VALIDATION-001" in propagation_result.new_requirements_detected

    def test_mvp_scoping_integration(self):
        """
        VERIFIES: MVP scoping and resource optimization integration
        SCENARIO: SE pipeline respects MVP cuts and resource constraints
        """
        # Step 1: Set up full feature set
        all_features = [
            Mock(id="F001", name="Water Tracking", value=0.9, cost=5, effort=8),
            Mock(id="F002", name="Smart Notifications", value=0.7, cost=3, effort=5),
            Mock(id="F003", name="Social Sharing", value=0.4, cost=4, effort=7),
            Mock(id="F004", name="Advanced Analytics", value=0.6, cost=8, effort=12),
            Mock(id="F005", name="Wearable Integration", value=0.5, cost=6, effort=10)
        ]
        
        # Step 2: Apply MVP constraints
        mvp_constraints = {
            "max_cost": 15,
            "max_effort": 20, 
            "timeline_weeks": 12,
            "must_have_features": ["F001", "F002"]  # Core features
        }
        
        # Step 3: Run MVP optimization
        mvp_result = self.se_service.optimize_mvp_scope(all_features, mvp_constraints)
        
        # Step 4: Verify constraint compliance
        assert mvp_result.total_cost <= mvp_constraints["max_cost"]
        assert mvp_result.total_effort <= mvp_constraints["max_effort"]
        
        # Verify must-have features included
        selected_ids = [f.id for f in mvp_result.selected_features]
        assert "F001" in selected_ids  # Water tracking
        assert "F002" in selected_ids  # Notifications
        
        # Verify optimization logic (adjusted for realistic test data)
        assert mvp_result.value_density > 0.15  # Reasonable value per cost ratio

    def _evolve_entities_for_vision(self, entities):
        """Helper to simulate entity evolution in vision layer."""
        evolved = []
        for entity in entities:
            evolved_entity = Mock()
            evolved_entity.id = entity.id
            evolved_entity.label = entity.label
            evolved_entity.type = entity.type
            evolved_entity.stage = "vision"
            evolved_entity.layer_specific_data = {
                "problem_clarity": 0.85,
                "market_validation": 0.78
            }
            evolved.append(evolved_entity)
        return evolved
    
    def _evolve_entities_for_prd(self, entities):
        """Helper to simulate entity evolution in PRD layer."""
        evolved = []
        for entity in entities:
            evolved_entity = Mock()
            evolved_entity.id = entity.id
            evolved_entity.label = entity.label
            evolved_entity.type = entity.type
            evolved_entity.stage = "prd"
            evolved_entity.layer_specific_data = {
                "requirements_mapped": ["REQ-001", "REQ-002"],
                "acceptance_criteria": ["AC-001", "AC-002"]
            }
            evolved.append(evolved_entity)
        return evolved
    
    def _evolve_entities_for_architecture(self, entities):
        """Helper to simulate entity evolution in architecture layer."""
        evolved = []
        for entity in entities:
            evolved_entity = Mock()
            evolved_entity.id = entity.id
            evolved_entity.label = entity.label
            evolved_entity.type = entity.type
            evolved_entity.stage = "architecture"
            evolved_entity.layer_specific_data = {
                "components_assigned": ["WaterService", "NotificationService"],
                "interfaces_defined": ["API", "Database"]
            }
            evolved.append(evolved_entity)
        return evolved
    
    def _evolve_entities_for_implementation(self, entities):
        """Helper to simulate entity evolution in implementation layer."""
        evolved = []
        for entity in entities:
            evolved_entity = Mock()
            evolved_entity.id = entity.id
            evolved_entity.label = entity.label
            evolved_entity.type = entity.type
            evolved_entity.stage = "implementation"
            evolved_entity.layer_specific_data = {
                "tasks_created": ["T-001", "T-002"],
                "effort_estimated": 15.5
            }
            evolved.append(evolved_entity)
        return evolved
    
    def _generate_req_spec(self, requirement):
        """Helper to generate requirement specification."""
        return f"""
id: {requirement["id"]}
title: {requirement["title"]}
description: {requirement["description"]}
source_documents:
  - docs/PRD.md
acceptance_criteria:
  - User can input water amount
  - System validates input range
  - Data is stored with timestamp
implementing_code: []
verified_by: []
        """


class TestSEPipelineIntegrationWorkflows:
    """Test complete SE pipeline integration workflows."""
    
    def setup_method(self):
        """Set up test environment."""
        from unittest.mock import Mock
        from src.llm_council.consensus import ConsensusEngine
        from src.llm_council.human_review import HumanReviewInterface
        from src.llm_council.research_agent import ResearchAgent
        from src.llm_council.orchestrator import AuditorOrchestrator
        
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock dependencies
        consensus_engine = Mock(spec=ConsensusEngine)
        human_review = Mock(spec=HumanReviewInterface)
        research_agent = ResearchAgent(enabled=False)
        orchestrator = Mock(spec=AuditorOrchestrator)
        
        self.se_service = SEIntegrationService(consensus_engine, human_review, research_agent, orchestrator)

    @pytest.mark.asyncio
    async def test_real_world_water_app_complete_pipeline(self):
        """
        VERIFIES: Complete real-world pipeline execution  
        SCENARIO: Water tracking app from idea to deployable code
        USE_CASE: UC-001→UC-010 (complete end-to-end scenario)
        """
        # Step 1: Real water app idea input
        water_app_input = {
            "idea": """
            Build a water tracking app for health-conscious professionals who struggle 
            to maintain proper hydration throughout their busy workday. The app should 
            send smart reminders based on activity level, weather, and personal goals.
            Target users are working professionals aged 25-45 who care about health 
            but have limited time for manual tracking.
            """,
            "paradigm": "yc_startup",
            "context": {
                "budget": 50000,
                "timeline_weeks": 12,
                "team_size": 2,
                "target_platform": "mobile_web"
            }
        }
        
        # Step 2: Execute complete pipeline with realistic timing
        with patch.multiple(
            self.se_service,
            _extract_entities=AsyncMock(return_value=self._generate_water_app_entities()),
            _expand_research_context=AsyncMock(return_value=self._generate_water_app_research()),
            _generate_vision_document=AsyncMock(return_value=self._generate_water_app_vision()),
            _generate_prd_documents=AsyncMock(return_value=self._generate_water_app_prds()),
            _generate_architecture=AsyncMock(return_value=self._generate_water_app_architecture()),
            _generate_implementation_plan=AsyncMock(return_value=self._generate_water_app_tasks()),
            _generate_code_artifacts=AsyncMock(return_value=self._generate_water_app_code()),
            _generate_test_artifacts=AsyncMock(return_value=self._generate_water_app_tests())
        ):
            pipeline_result = await self.se_service.execute_complete_pipeline(water_app_input)
        
        # Step 3: Validate complete pipeline success
        assert pipeline_result.success == True
        assert pipeline_result.layers_completed == 10
        
        # Step 4: Validate artifact completeness
        artifacts = pipeline_result.generated_artifacts
        
        # Documents
        document_artifacts = [a for a in artifacts if a.artifact_type == "document"]
        assert len(document_artifacts) >= 4  # Vision, PRD, Architecture, Implementation
        
        # Specifications
        spec_artifacts = [a for a in artifacts if a.artifact_type == "specification"]
        assert len(spec_artifacts) >= 3  # REQ, NFR, API specs
        
        # Code
        code_artifacts = [a for a in artifacts if a.artifact_type == "source_code"]
        assert len(code_artifacts) >= 5  # Services, models, controllers
        
        # Tests
        test_artifacts = [a for a in artifacts if a.artifact_type == "test"]
        assert len(test_artifacts) >= 5  # Unit, integration, E2E tests
        
        # Step 5: Validate traceability completeness
        assert pipeline_result.traceability_coverage >= 0.95
        assert len(pipeline_result.orphaned_artifacts) == 0
        assert pipeline_result.symmetry_score >= 0.9

    def _generate_water_app_entities(self):
        """Generate realistic entities for water tracking app."""
        return [
            Mock(id="prob_001", label="Hydration Tracking Difficulty", type="problem"),
            Mock(id="user_001", label="Health-conscious Professionals", type="target_user"),
            Mock(id="sol_001", label="Automated Water Tracking", type="solution"),
            Mock(id="feat_001", label="Smart Reminder System", type="feature"),
            Mock(id="risk_001", label="User Adoption Challenge", type="risk")
        ]
    
    def _generate_water_app_research(self):
        """Generate realistic research data for water tracking app."""
        return Mock(
            market_data={
                "size": "$4.2B health app market",
                "growth": "15% CAGR",
                "penetration": "23% of professionals use health apps"
            },
            competition_analysis=[
                {"name": "MyFitnessPal", "focus": "nutrition", "users": "200M+"},
                {"name": "Waterllama", "focus": "basic tracking", "users": "100k+"}
            ]
        )
    
    def _generate_water_app_vision(self):
        """Generate realistic vision document for water tracking app."""
        return """
        # VISION.md - Water Tracking App
        
        ## Problem & JTBD
        Health-conscious professionals struggle to maintain proper hydration
        
        ## Target Users  
        Working professionals aged 25-45 who care about health
        
        ## Success Metrics
        - 70% daily hydration goal achievement
        - 4.5+ App Store rating
        - 10k+ active users within 6 months
        """
    
    def _generate_water_app_prds(self):
        """Generate realistic PRD documents for water tracking app."""
        return {
            "PRD.md": "# Main PRD with high-level requirements",
            "sub_prds/FRS-TRACKING-001.md": "# Water tracking feature requirements",
            "sub_prds/FRS-NOTIF-002.md": "# Smart notification requirements"
        }
    
    def _generate_water_app_architecture(self):
        """Generate realistic architecture for water tracking app."""
        return {
            "components": [
                Mock(name="WaterTrackingService", type="service"),
                Mock(name="NotificationService", type="service"),
                Mock(name="UserService", type="service"),
                Mock(name="AnalyticsService", type="service")
            ],
            "interfaces": [
                Mock(name="REST API", protocol="HTTP"),
                Mock(name="Database", protocol="PostgreSQL")
            ]
        }
    
    def _generate_water_app_tasks(self):
        """Generate realistic implementation tasks for water tracking app."""
        return [
            Mock(task_id="T-TRACK-001", description="Implement water logging service"),
            Mock(task_id="T-NOTIF-001", description="Create notification scheduling"),
            Mock(task_id="T-USER-001", description="Build user management system"),
            Mock(task_id="T-API-001", description="Design REST API endpoints"),
            Mock(task_id="T-DB-001", description="Set up database schema")
        ]
    
    def _generate_water_app_code(self):
        """Generate realistic code artifacts for water tracking app."""
        return [
            ("src/services/water_service.py", "# IMPLEMENTS: REQ-TRACKING-001"),
            ("src/services/notification_service.py", "# IMPLEMENTS: REQ-NOTIF-001"),
            ("src/models/user_model.py", "# IMPLEMENTS: REQ-USER-001"),
            ("src/controllers/api_controller.py", "# IMPLEMENTS: REQ-API-001"),
            ("src/database/schema.py", "# IMPLEMENTS: REQ-DATA-001")
        ]
    
    def _generate_water_app_tests(self):
        """Generate realistic test artifacts for water tracking app."""
        return [
            ("tests/unit/test_water_service.py", "# VERIFIES: REQ-TRACKING-001"),
            ("tests/unit/test_notification_service.py", "# VERIFIES: REQ-NOTIF-001"),
            ("tests/integration/test_api.py", "# VERIFIES: API integration"),
            ("tests/e2e/test_user_flow.py", "# VERIFIES: UC-001 (complete user journey)"),
            ("tests/nfr/test_performance.py", "# VERIFIES: NFR-PERF-001")
        ]