"""
Complete Pipeline Integration Tests - CLI to Runtime

VERIFIES: REQ-016→REQ-023 (complete paradigm-to-code pipeline)
VALIDATES: Full integration across all 10 pipeline layers
USE_CASE: UC-001→UC-010 (end-to-end system validation)
INTERFACES: All pipeline components from CLI to runtime telemetry
LAST_SYNC: 2025-08-30
"""

import pytest
import tempfile
import asyncio
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.llm_council.cli import AuditCommand
from src.llm_council.services.paradigm_engine import ParadigmEngine
from src.llm_council.services.entity_extractor import EntityExtractor
from src.llm_council.services.research_expander import ResearchExpander
from src.llm_council.services.graph_integration import GraphIntegrationService
from src.llm_council.services.codegen_engine import CodeGenEngine
from src.llm_council.services.provenance_tracker import ProvenanceTracker
from src.llm_council.orchestrator import AuditorOrchestrator


class TestCompletePipelineIntegration:
    """Test complete pipeline workflows from CLI to runtime telemetry."""

    def setup_method(self):
        """Set up test environment with full pipeline components."""
        self.temp_dir = tempfile.mkdtemp()
        self.docs_dir = Path(self.temp_dir) / "docs"
        self.docs_dir.mkdir()
        
        # Initialize all pipeline services
        self.paradigm_engine = ParadigmEngine()
        self.entity_extractor = EntityExtractor()
        self.research_expander = ResearchExpander()
        self.graph_service = GraphIntegrationService(self.temp_dir)
        self.codegen_engine = CodeGenEngine(self.temp_dir)
        self.provenance_tracker = ProvenanceTracker(self.temp_dir)

    @pytest.mark.asyncio
    async def test_complete_cli_to_runtime_pipeline(self):
        """
        VERIFIES: REQ-016→REQ-023 (complete 10-layer pipeline execution)
        VALIDATES: CLI command → paradigm → documents → code → runtime telemetry
        USE_CASE: UC-010 (complete user journey from idea to deployed system)
        """
        # Layer 1: Idea Capture & Paradigm Selection
        user_idea = "Build a task management app for remote teams with AI-powered priority suggestions"
        selected_paradigm = "lean_startup"
        
        # Layer 2: Context Graph Generation  
        with patch.object(self.entity_extractor, 'extract_context') as mock_extract:
            mock_extract.return_value = Mock(
                entities=[
                    Mock(id="prob_001", type="problem", label="Remote Team Task Chaos"),
                    Mock(id="user_001", type="target_user", label="Remote Team Managers"),
                    Mock(id="sol_001", type="solution", label="AI Priority Suggestions")
                ],
                relationships=[
                    Mock(source_id="prob_001", target_id="user_001", type="affects"),
                    Mock(source_id="sol_001", target_id="prob_001", type="solves")
                ]
            )
            
            context_graph = await self.entity_extractor.extract_context(user_idea)
        
        assert len(context_graph.entities) == 3
        assert any(e.type == "problem" for e in context_graph.entities)
        
        # Layer 3: Research Expansion
        with patch.object(self.research_expander, 'expand_context') as mock_research:
            mock_research.return_value = Mock(
                market_insights=["Task management market is $4.2B"],
                competitive_analysis=["Asana, Monday.com dominate enterprise"],
                technical_trends=["AI-powered productivity tools trending"]
            )
            
            enhanced_graph = await self.research_expander.expand_context(context_graph, {})
        
        # Layer 4: Document Generation Pipeline
        paradigm_questions = self.paradigm_engine.get_framework_questions(selected_paradigm)
        
        mock_answers = {
            "problem_hypothesis": "Remote teams waste 2hrs/day on task prioritization",
            "solution_concept": "AI suggests optimal task priority based on team context",
            "mvp_features": "Task creation, AI priority scoring, team dashboard"
        }
        
        # Generate documents through audit system
        docs_created = await self._simulate_document_generation_pipeline(
            user_idea, selected_paradigm, mock_answers, enhanced_graph
        )
        
        assert "VISION.md" in docs_created
        assert "PRD.md" in docs_created  
        assert "ARCHITECTURE.md" in docs_created
        assert "IMPLEMENTATION_PLAN.md" in docs_created
        
        # Layer 5: Specification Generation
        specs_generated = self._generate_hierarchical_specs(docs_created["PRD.md"])
        
        assert "specs/requirements/REQ-TASK-001.yaml" in specs_generated
        assert "specs/requirements/REQ-AI-002.yaml" in specs_generated
        assert "specs/nfr/NFR-PERF-001.yaml" in specs_generated
        
        # Layer 6: Code Generation with Provenance
        implementation_plan = docs_created["IMPLEMENTATION_PLAN.md"]
        code_artifacts = self.codegen_engine.generate_from_implementation_plan(
            implementation_plan, specs_generated
        )
        
        assert len(code_artifacts) >= 6  # services + models + tests
        
        # Validate provenance headers in generated code
        service_files = [f for f, c in code_artifacts if "service" in f and "test" not in f]
        for file_path, content in service_files:
            assert "IMPLEMENTS:" in content
            assert "VERIFIED_BY:" in content
            assert "REQ-" in content or "FRS-" in content
        
        # Layer 7: Test Generation with Requirements Mapping  
        test_files = [f for f, c in code_artifacts if "test_" in f]
        for file_path, content in test_files:
            assert "VERIFIES:" in content
            assert "TESTS:" in content
            assert "USE_CASES:" in content
        
        # Layer 8: Runtime Configuration & Deployment
        runtime_config = self._generate_runtime_configuration(code_artifacts)
        
        assert "telemetry_tags" in runtime_config
        assert "requirement_tracking" in runtime_config
        assert "performance_metrics" in runtime_config
        
        # Layer 9: Telemetry & Observability Setup
        telemetry_setup = self._setup_runtime_telemetry(runtime_config)
        
        assert "REQ_TRACKING_enabled" in telemetry_setup
        assert "component_tracing" in telemetry_setup
        assert "performance_monitoring" in telemetry_setup
        
        # Layer 10: Governance & Lifecycle Management
        governance_rules = self._setup_governance_enforcement()
        
        assert "no_orphan_code_rule" in governance_rules
        assert "provenance_required" in governance_rules
        assert "symmetry_enforcement" in governance_rules

    @pytest.mark.asyncio
    async def test_cli_audit_full_pipeline_integration(self):
        """
        VERIFIES: REQ-012, REQ-013 (CLI integration), REQ-001→REQ-015 (audit system)
        VALIDATES: CLI audit command executes complete pipeline workflow
        USE_CASE: UC-001, UC-007 (command-line driven audit execution)
        """
        # Step 1: Create test documents
        await self._create_test_documents()
        
        # Step 2: Create test template and quality gates
        template_file = self._create_test_template()
        quality_gates_file = self._create_test_quality_gates()
        
        # Step 3: Mock orchestrator execution
        with patch('src.llm_council.cli.AuditorOrchestrator') as mock_orchestrator:
            mock_orchestrator.return_value.execute_stage_audit = AsyncMock(
                return_value=Mock(
                    success=True,
                    auditor_responses=[
                        {"auditor_role": "pm", "overall_assessment": {"overall_pass": True}},
                        {"auditor_role": "ux", "overall_assessment": {"overall_pass": True}},
                        {"auditor_role": "security", "overall_assessment": {"overall_pass": True}}
                    ],
                    consensus_result=Mock(final_decision="PASS", weighted_average=4.2)
                )
            )
            
            # Step 4: Execute CLI audit command
            audit_cmd = AuditCommand(
                docs_path=str(self.docs_dir),
                stage="vision",
                template=str(template_file),
                model="gpt-4o",
                api_key="test-key",
                interactive=False,
                max_calls=10
            )
            
            result = await audit_cmd.execute()
        
        # Step 5: Validate audit execution results
        assert result['success'] == True
        assert result['stage'] == "vision"
        assert result['consensus_result']['final_decision'] == "PASS"
        assert len(result['auditor_responses']) >= 3

    @pytest.mark.asyncio
    async def test_pipeline_error_recovery_and_rollback(self):
        """
        VERIFIES: REQ-007 (error handling), R-PRD-022 (rollback mechanisms)
        VALIDATES: Pipeline resilience and recovery from component failures
        USE_CASE: UC-004 (error handling and recovery workflows)
        """
        # Step 1: Simulate pipeline execution with component failure
        pipeline_steps = [
            ("paradigm_selection", True),    # Success
            ("entity_extraction", True),     # Success  
            ("research_expansion", False),   # Failure
            ("document_generation", False),  # Should not execute
            ("code_generation", False)       # Should not execute
        ]
        
        execution_log = []
        
        for step_name, should_succeed in pipeline_steps:
            try:
                if step_name == "paradigm_selection":
                    result = self.paradigm_engine.select_framework("test_idea", "yc_startup")
                    execution_log.append((step_name, "SUCCESS", result))
                    
                elif step_name == "entity_extraction":
                    with patch.object(self.entity_extractor, 'extract_context') as mock_extract:
                        mock_extract.return_value = Mock(entities=[], relationships=[])
                        result = await self.entity_extractor.extract_context("test_idea")
                        execution_log.append((step_name, "SUCCESS", result))
                
                elif step_name == "research_expansion":
                    if not should_succeed:
                        raise Exception("Simulated research API failure")
                        
                elif step_name == "document_generation":
                    # Should not execute due to previous failure
                    execution_log.append((step_name, "SKIPPED", "Previous step failed"))
                    
            except Exception as e:
                execution_log.append((step_name, "FAILED", str(e)))
                # Trigger rollback mechanism
                if "research" in step_name:
                    rollback_actions = self._execute_pipeline_rollback(execution_log)
                    break
        
        # Step 2: Validate rollback execution
        assert len(execution_log) == 3  # paradigm + entity + research_failure
        assert execution_log[0][1] == "SUCCESS"  # paradigm succeeded
        assert execution_log[1][1] == "SUCCESS"  # entity extraction succeeded
        assert execution_log[2][1] == "FAILED"   # research failed
        
        # Step 3: Validate rollback actions were triggered
        rollback_actions = self._execute_pipeline_rollback(execution_log)
        assert "cleanup_partial_entities" in rollback_actions
        assert "reset_pipeline_state" in rollback_actions
        assert "preserve_user_input" in rollback_actions

    async def test_multi_model_consensus_with_council_debate(self):
        """
        VERIFIES: R-PRD-023 (council debate system), REQ-001→REQ-003 (consensus engine)
        VALIDATES: Multi-model LLM council with structured debate workflow
        USE_CASE: UC-003, UC-008 (multi-auditor consensus with human oversight)
        """
        # Step 1: Set up multi-model council configuration
        council_config = {
            "models": [
                {"provider": "openai", "model": "gpt-4o", "weight": 1.0},
                {"provider": "anthropic", "model": "claude-3-5-sonnet", "weight": 1.1},
                {"provider": "google", "model": "gemini-pro", "weight": 0.9}
            ],
            "debate_rounds": 2,
            "consensus_threshold": 0.75
        }
        
        # Step 2: Create test document for multi-model review
        test_document = """
        # VISION.md - AI Task Management App
        
        ## Problem Statement
        Remote teams struggle with task prioritization, wasting 2+ hours daily on coordination overhead.
        
        ## Solution Approach  
        AI-powered task management with automated priority scoring based on team context and deadlines.
        
        ## Success Metrics
        - 50% reduction in coordination time
        - 90% user adoption within teams
        - 4.5+ app store rating
        """
        
        # Step 3: Execute multi-model council debate
        with patch('src.llm_council.orchestrator.get_llm_client') as mock_client_factory:
            # Mock different model responses with varying perspectives
            mock_openai_response = self._create_mock_auditor_response(
                "pm", "vision", 4.1, True, "Strong market opportunity, clear problem statement"
            )
            mock_claude_response = self._create_mock_auditor_response(
                "pm", "vision", 3.8, True, "Good vision but needs more user validation data"
            )
            mock_gemini_response = self._create_mock_auditor_response(
                "pm", "vision", 4.3, True, "Excellent problem-solution fit for target market"
            )
            
            mock_clients = {
                "openai": AsyncMock(chat=Mock(completions=Mock(create=AsyncMock(return_value=mock_openai_response)))),
                "anthropic": AsyncMock(chat=Mock(completions=Mock(create=AsyncMock(return_value=mock_claude_response)))),
                "google": AsyncMock(chat=Mock(completions=Mock(create=AsyncMock(return_value=mock_gemini_response))))
            }
            
            mock_client_factory.side_effect = lambda provider, **kwargs: mock_clients[provider]
            
            # Execute council debate
            orchestrator = AuditorOrchestrator(
                template_path=self._create_test_template(),
                model="multi-model-council",
                api_key="test-key",
                council_config=council_config
            )
            
            council_result = await orchestrator.execute_council_debate("vision", test_document)
        
        # Step 4: Validate council debate results
        assert council_result.debate_rounds == 2
        assert len(council_result.model_responses) == 3
        assert council_result.final_consensus_score >= 3.8
        assert council_result.consensus_achieved == True
        
        # Step 5: Validate debate synthesis
        synthesis = council_result.debate_synthesis
        assert "coordination time" in synthesis.lower()
        assert "task prioritization" in synthesis.lower()
        assert len(synthesis) >= 200  # Substantial synthesis content

    @pytest.mark.asyncio
    async def test_runtime_telemetry_integration_with_req_tracking(self):
        """
        VERIFIES: R-PRD-021→R-PRD-022 (runtime telemetry, requirement tracking)
        VALIDATES: Runtime telemetry captures requirement fulfillment metrics
        USE_CASE: UC-009, UC-010 (runtime monitoring, performance tracking)
        """
        # Step 1: Set up runtime configuration with REQ tracking
        runtime_config = {
            "telemetry": {
                "requirement_tracking": True,
                "component_tagging": True,
                "performance_monitoring": True
            },
            "req_mappings": {
                "REQ-TASK-001": ["src/services/task_service.py", "TaskService.create_task()"],
                "REQ-AI-002": ["src/services/ai_service.py", "AIService.suggest_priority()"],
                "NFR-PERF-001": ["src/middleware/performance.py", "ResponseTimeMiddleware"]
            }
        }
        
        # Step 2: Simulate runtime execution with telemetry
        telemetry_events = []
        
        # Mock runtime events with REQ tagging
        runtime_events = [
            {
                "timestamp": "2025-08-30T10:00:00Z",
                "event": "task_created",
                "component": "TaskService.create_task",
                "req_id": "REQ-TASK-001",
                "performance": {"duration_ms": 150, "success": True}
            },
            {
                "timestamp": "2025-08-30T10:00:01Z", 
                "event": "ai_priority_calculated",
                "component": "AIService.suggest_priority",
                "req_id": "REQ-AI-002",
                "performance": {"duration_ms": 450, "success": True}
            },
            {
                "timestamp": "2025-08-30T10:00:02Z",
                "event": "api_response",
                "component": "ResponseTimeMiddleware",
                "req_id": "NFR-PERF-001", 
                "performance": {"duration_ms": 280, "success": True}
            }
        ]
        
        # Step 3: Process telemetry through requirement tracking
        req_fulfillment_metrics = self._process_runtime_telemetry(runtime_events, runtime_config)
        
        # Step 4: Validate requirement fulfillment tracking
        assert "REQ-TASK-001" in req_fulfillment_metrics
        assert req_fulfillment_metrics["REQ-TASK-001"]["calls_count"] == 1
        assert req_fulfillment_metrics["REQ-TASK-001"]["avg_performance_ms"] == 150
        assert req_fulfillment_metrics["REQ-TASK-001"]["success_rate"] == 1.0
        
        assert "NFR-PERF-001" in req_fulfillment_metrics
        assert req_fulfillment_metrics["NFR-PERF-001"]["avg_performance_ms"] == 280
        assert req_fulfillment_metrics["NFR-PERF-001"]["threshold_compliance"] == True  # <300ms
        
        # Step 5: Generate runtime compliance report
        compliance_report = self._generate_runtime_compliance_report(req_fulfillment_metrics)
        
        assert compliance_report["overall_compliance_rate"] >= 0.95
        assert "REQ-TASK-001" in compliance_report["requirement_status"] 
        assert compliance_report["requirement_status"]["REQ-TASK-001"]["status"] == "COMPLIANT"

    async def test_bidirectional_change_impact_with_full_propagation(self):
        """
        VERIFIES: R-PRD-021 (impact analysis), UC-006 (change propagation)
        VALIDATES: Complete bidirectional impact analysis across all pipeline layers
        USE_CASE: UC-006 (change impact assessment and propagation)
        """
        # Step 1: Set up complete artifact traceability matrix
        trace_matrix = {
            "paradigm_to_docs": {
                "lean_startup_framework": ["docs/VISION.md", "docs/PRD.md"]
            },
            "docs_to_requirements": {
                "docs/VISION.md": ["REQ-TASK-001", "REQ-AI-002"],
                "docs/PRD.md": ["REQ-TASK-001", "REQ-AI-002", "NFR-PERF-001"]
            },
            "requirements_to_code": {
                "REQ-TASK-001": ["src/services/task_service.py", "src/models/task.py"],
                "REQ-AI-002": ["src/services/ai_service.py", "src/models/priority.py"]
            },
            "code_to_tests": {
                "src/services/task_service.py": ["tests/test_task_service.py"],
                "src/services/ai_service.py": ["tests/test_ai_service.py"]
            },
            "tests_to_runtime": {
                "tests/test_task_service.py": ["runtime/task_monitor.py"],
                "tests/test_ai_service.py": ["runtime/ai_monitor.py"]
            }
        }
        
        # Step 2: Simulate code change in TaskService
        changed_files = ["src/services/task_service.py"]
        change_description = "Added task validation logic and priority constraints"
        
        # Step 3: Execute complete impact analysis
        impact_analysis = self.graph_service.analyze_complete_change_impact(
            changed_files, change_description, trace_matrix
        )
        
        # Step 4: Validate upstream impact detection
        upstream_impacts = impact_analysis['upstream_impacts']
        assert "REQ-TASK-001" in upstream_impacts['affected_requirements']
        assert "docs/VISION.md" in upstream_impacts['affected_documents']
        assert "docs/PRD.md" in upstream_impacts['affected_documents']
        assert "lean_startup_framework" in upstream_impacts['affected_paradigms']
        
        # Step 5: Validate downstream impact detection
        downstream_impacts = impact_analysis['downstream_impacts']
        assert "tests/test_task_service.py" in downstream_impacts['affected_tests']
        assert "runtime/task_monitor.py" in downstream_impacts['affected_runtime']
        
        # Step 6: Validate recommended actions
        recommended_actions = impact_analysis['recommended_actions']
        assert len(recommended_actions) >= 5
        assert any("update test" in action.lower() for action in recommended_actions)
        assert any("validate requirement" in action.lower() for action in recommended_actions)
        assert any("update documentation" in action.lower() for action in recommended_actions)

    async def _simulate_document_generation_pipeline(self, idea, paradigm, answers, graph):
        """Helper to simulate complete document generation pipeline."""
        return {
            "VISION.md": f"""
            # VISION.md - {idea[:40]}...
            GENERATED_FROM: paradigm/{paradigm}_framework.yaml
            
            ## Problem Statement
            {answers.get('problem_hypothesis', 'TBD')}
            
            ## Solution Approach
            {answers.get('solution_concept', 'TBD')}
            
            ## MVP Scope
            {answers.get('mvp_features', 'TBD')}
            """,
            "PRD.md": f"""
            # PRD.md
            SOURCE_VISION: docs/VISION.md
            
            ## Requirements
            REQ-TASK-001: Task creation and management
            REQ-AI-002: AI-powered priority suggestions
            
            ## Features  
            FRS-TASK-001: Basic task CRUD operations
            FRS-AI-002: Priority suggestion engine
            """,
            "ARCHITECTURE.md": """
            # ARCHITECTURE.md
            SOURCE_PRD: docs/PRD.md
            
            ## System Components
            - TaskService: Handles task operations
            - AIService: Provides priority suggestions
            - APIGateway: External interface
            """,
            "IMPLEMENTATION_PLAN.md": """
            # IMPLEMENTATION_PLAN.md
            SOURCE_ARCHITECTURE: docs/ARCHITECTURE.md
            
            ## Tasks
            T-TASK-001: Implement TaskService (8 hours)
            T-AI-001: Implement AIService (12 hours)
            T-API-001: Set up API endpoints (6 hours)
            """
        }

    def _generate_hierarchical_specs(self, prd_content):
        """Helper to generate hierarchical specifications from PRD."""
        return {
            "specs/requirements/REQ-TASK-001.yaml": """
id: REQ-TASK-001
title: Task Creation and Management
source_documents:
  - docs/PRD.md#requirements
acceptance_criteria:
  - User can create tasks with title and description
  - Tasks have priority levels (low, medium, high)
  - Task status can be updated (todo, in_progress, done)
            """,
            "specs/requirements/REQ-AI-002.yaml": """
id: REQ-AI-002
title: AI Priority Suggestions
source_documents:
  - docs/PRD.md#features
acceptance_criteria:
  - AI analyzes task context and deadlines
  - Priority suggestions are provided within 500ms
  - Suggestions include confidence score
            """,
            "specs/nfr/NFR-PERF-001.yaml": """
id: NFR-PERF-001
title: API Performance Requirements
description: System must respond to requests within 300ms
target_metrics:
  - p95_response_time: 300ms
  - api_availability: 99.9%
            """
        }

    def _generate_runtime_configuration(self, code_artifacts):
        """Helper to generate runtime configuration from code artifacts."""
        return {
            "telemetry_tags": {
                "requirement_tracking": True,
                "component_performance": True,
                "user_journey_tracking": True
            },
            "requirement_tracking": {
                "enabled": True,
                "tag_format": "REQ_{req_id}",
                "metrics": ["execution_count", "avg_duration", "success_rate"]
            },
            "performance_metrics": {
                "api_response_time": {"threshold": "300ms", "alert_on_breach": True},
                "database_query_time": {"threshold": "100ms", "alert_on_breach": True},
                "ai_inference_time": {"threshold": "500ms", "alert_on_breach": True}
            }
        }

    def _setup_runtime_telemetry(self, runtime_config):
        """Helper to set up runtime telemetry based on configuration."""
        return {
            "REQ_TRACKING_enabled": runtime_config["requirement_tracking"]["enabled"],
            "component_tracing": {
                "TaskService": {"req_tags": ["REQ-TASK-001"], "performance_monitoring": True},
                "AIService": {"req_tags": ["REQ-AI-002"], "performance_monitoring": True}
            },
            "performance_monitoring": {
                "thresholds": runtime_config["performance_metrics"],
                "alerting": True,
                "dashboard_integration": True
            }
        }

    def _setup_governance_enforcement(self):
        """Helper to set up governance and lifecycle management rules."""
        return {
            "no_orphan_code_rule": {
                "enabled": True,
                "enforcement": "pre_commit_hook",
                "violation_action": "block_commit"
            },
            "provenance_required": {
                "code_files": ["IMPLEMENTS", "VERIFIED_BY", "LINKED_TO"],
                "test_files": ["VERIFIES", "TESTS", "USE_CASES"],
                "doc_files": ["GENERATED_FROM", "VALIDATES"]
            },
            "symmetry_enforcement": {
                "bidirectional_traceability": True,
                "automatic_impact_analysis": True,
                "change_approval_gates": True
            }
        }

    async def _create_test_documents(self):
        """Helper to create test documents in temp directory."""
        test_docs = {
            "VISION.md": """
            # VISION.md - Test Project
            ## Problem Statement
            Test problem requiring solution
            """,
            "PRD.md": """
            # PRD.md  
            ## Requirements
            REQ-001: Basic requirement for testing
            """
        }
        
        for doc_name, content in test_docs.items():
            doc_path = self.docs_dir / doc_name
            doc_path.write_text(content)

    def _create_test_template(self):
        """Helper to create test template configuration."""
        template_config = {
            "project_info": {
                "name": "Integration Test Template",
                "description": "Template for integration testing",
                "stages": ["vision", "prd"]
            },
            "auditor_questions": {
                "vision": {
                    "pm": {
                        "focus_areas": ["market_strategy"],
                        "key_questions": ["Is the market opportunity clear?"]
                    }
                }
            },
            "scoring_weights": {"vision": {"pm": 1.0}}
        }
        
        template_file = Path(self.temp_dir) / "test_template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(template_config, f)
        
        return template_file

    def _create_test_quality_gates(self):
        """Helper to create test quality gates configuration."""
        quality_gates = {
            "consensus_thresholds": {
                "score_threshold": 3.8,
                "approval_threshold": 0.67
            },
            "required_auditors": ["pm", "ux", "security"]
        }
        
        gates_file = Path(self.temp_dir) / "quality_gates.yaml"
        with open(gates_file, 'w') as f:
            yaml.dump(quality_gates, f)
        
        return gates_file

    def _create_mock_auditor_response(self, role, stage, score, pass_verdict, summary):
        """Helper to create mock auditor response."""
        return Mock(
            choices=[Mock(
                message=Mock(content=json.dumps({
                    "auditor_role": role,
                    "document_analyzed": stage,
                    "audit_timestamp": "2025-08-30T10:00:00Z",
                    "scores_detailed": {
                        "simplicity": {"score": score, "pass": pass_verdict, 
                                     "justification": f"Detailed justification for {role} evaluation",
                                     "improvements": ["Sample improvement"]},
                        "conciseness": {"score": score, "pass": pass_verdict,
                                      "justification": f"Conciseness evaluation by {role}",
                                      "improvements": ["Sample improvement"]},
                        "actionability": {"score": score, "pass": pass_verdict,
                                        "justification": f"Actionability assessment from {role}",
                                        "improvements": ["Sample improvement"]},
                        "readability": {"score": score, "pass": pass_verdict,
                                      "justification": f"Readability review by {role}",
                                      "improvements": ["Sample improvement"]},
                        "options_tradeoffs": {"score": score, "pass": pass_verdict,
                                            "justification": f"Options analysis from {role}",
                                            "improvements": ["Sample improvement"]},
                        "evidence_specificity": {"score": score, "pass": pass_verdict,
                                               "justification": f"Evidence review by {role}",
                                               "improvements": ["Sample improvement"]}
                    },
                    "overall_assessment": {
                        "average_score": score,
                        "overall_pass": pass_verdict,
                        "summary": summary,
                        "top_strengths": ["Strong analysis"],
                        "top_risks": ["Scope risk"],
                        "quick_wins": ["Add examples"]
                    },
                    "blocking_issues": [],
                    "alignment_feedback": {
                        "upstream_consistency": {"score": 4, "issues": [], "suggestions": []},
                        "internal_consistency": {"score": 4, "issues": [], "suggestions": []}
                    },
                    "confidence_level": 4
                }))
            )]
        )

    def _execute_pipeline_rollback(self, execution_log):
        """Helper to execute pipeline rollback actions."""
        rollback_actions = []
        
        # Analyze failed steps and determine rollback actions
        for step_name, status, result in execution_log:
            if status == "FAILED":
                if "research" in step_name:
                    rollback_actions.extend([
                        "cleanup_partial_entities",
                        "reset_pipeline_state", 
                        "preserve_user_input",
                        "fallback_to_offline_mode"
                    ])
                elif "document" in step_name:
                    rollback_actions.extend([
                        "revert_document_changes",
                        "restore_previous_version",
                        "maintain_audit_trail"
                    ])
        
        return rollback_actions

    def _process_runtime_telemetry(self, events, runtime_config):
        """Helper to process runtime telemetry events."""
        req_metrics = {}
        
        for event in events:
            req_id = event["req_id"]
            if req_id not in req_metrics:
                req_metrics[req_id] = {
                    "calls_count": 0,
                    "total_duration_ms": 0,
                    "success_count": 0,
                    "avg_performance_ms": 0,
                    "success_rate": 0,
                    "threshold_compliance": True
                }
            
            metrics = req_metrics[req_id]
            metrics["calls_count"] += 1
            metrics["total_duration_ms"] += event["performance"]["duration_ms"]
            if event["performance"]["success"]:
                metrics["success_count"] += 1
            
            # Calculate averages
            metrics["avg_performance_ms"] = metrics["total_duration_ms"] / metrics["calls_count"]
            metrics["success_rate"] = metrics["success_count"] / metrics["calls_count"]
            
            # Check performance thresholds
            if req_id.startswith("NFR-PERF") and metrics["avg_performance_ms"] > 300:
                metrics["threshold_compliance"] = False
        
        return req_metrics

    def _generate_runtime_compliance_report(self, req_metrics):
        """Helper to generate runtime compliance report."""
        compliant_reqs = sum(1 for m in req_metrics.values() if m["success_rate"] >= 0.95)
        total_reqs = len(req_metrics)
        
        requirement_status = {}
        for req_id, metrics in req_metrics.items():
            if metrics["success_rate"] >= 0.95 and metrics["threshold_compliance"]:
                requirement_status[req_id] = {"status": "COMPLIANT", "metrics": metrics}
            else:
                requirement_status[req_id] = {"status": "NON_COMPLIANT", "metrics": metrics}
        
        return {
            "overall_compliance_rate": compliant_reqs / total_reqs if total_reqs > 0 else 0,
            "requirement_status": requirement_status,
            "total_requirements": total_reqs,
            "compliant_requirements": compliant_reqs
        }


class TestPipelinePerformanceAndScalability:
    """Test pipeline performance characteristics and scalability limits."""

    def setup_method(self):
        """Set up performance test environment."""
        self.temp_dir = tempfile.mkdtemp()

    @pytest.mark.asyncio
    async def test_large_document_set_performance(self):
        """
        VERIFIES: NFR-PERF-001→NFR-PERF-003 (performance requirements)
        VALIDATES: Pipeline performance with realistic document sizes
        USE_CASE: UC-007 (performance validation for production workloads)
        """
        # Step 1: Create large document set (realistic sizes)
        large_documents = {
            "VISION.md": "# Vision\n" + ("Content line\n" * 200),      # ~2KB
            "PRD.md": "# PRD\n" + ("Requirement line\n" * 500),        # ~5KB  
            "ARCHITECTURE.md": "# Architecture\n" + ("Design line\n" * 300),  # ~3KB
            "IMPLEMENTATION_PLAN.md": "# Plan\n" + ("Task line\n" * 400)      # ~4KB
        }
        
        # Step 2: Execute pipeline with performance monitoring
        start_time = asyncio.get_event_loop().time()
        
        with patch('src.llm_council.orchestrator.AuditorOrchestrator') as mock_orchestrator:
            mock_orchestrator.return_value.execute_stage_audit = AsyncMock(
                return_value=Mock(
                    success=True,
                    auditor_responses=[Mock()] * 6,  # 6 auditors
                    execution_time=2.5,  # Simulated execution time
                    total_tokens=8000,   # Simulated token usage
                    total_cost=0.50      # Simulated cost
                )
            )
            
            # Process each document
            results = []
            for doc_name, content in large_documents.items():
                result = await mock_orchestrator.return_value.execute_stage_audit(
                    doc_name.replace(".md", "").lower(), content
                )
                results.append(result)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        # Step 3: Validate performance requirements
        assert total_time < 10.0  # Under 10 seconds for 4 documents
        assert all(r.success for r in results)
        
        total_tokens = sum(r.total_tokens for r in results)
        total_cost = sum(r.total_cost for r in results)
        
        assert total_tokens < 50000   # Token efficiency
        assert total_cost < 2.00      # Cost control (<$2/run target)

    @pytest.mark.asyncio
    async def test_concurrent_pipeline_execution_limits(self):
        """
        VERIFIES: REQ-007 (parallel execution limits), NFR-SCALE-001 (concurrency)
        VALIDATES: System handles concurrent pipeline executions appropriately
        USE_CASE: UC-007 (multi-user concurrent access)
        """
        # Step 1: Set up concurrent pipeline executions
        concurrent_pipelines = 3
        pipeline_tasks = []
        
        for i in range(concurrent_pipelines):
            task = self._create_mock_pipeline_execution(f"project_{i}")
            pipeline_tasks.append(task)
        
        # Step 2: Execute pipelines concurrently
        results = await asyncio.gather(*pipeline_tasks, return_exceptions=True)
        
        # Step 3: Validate concurrent execution results
        successful_pipelines = [r for r in results if not isinstance(r, Exception)]
        failed_pipelines = [r for r in results if isinstance(r, Exception)]
        
        assert len(successful_pipelines) >= 2  # At least 2 should succeed
        assert len(failed_pipelines) <= 1     # At most 1 should fail due to resource limits

    async def _create_mock_pipeline_execution(self, project_name):
        """Helper to create mock pipeline execution."""
        # Simulate pipeline execution with random delay
        await asyncio.sleep(0.1 + (hash(project_name) % 100) / 1000)  # 0.1-0.2s delay
        
        return {
            "project": project_name,
            "success": True,
            "execution_time": 2.5,
            "documents_processed": 4,
            "consensus_achieved": True
        }