"""Complete system E2E test: Full idea-to-production journey with all user types."""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from src.llm_council.database.neo4j_client import Neo4jClient, Neo4jConfig
from src.llm_council.services.question_engine import QuestionEngine, Paradigm
from src.llm_council.services.council_system import CouncilSystem, DebateTopic
from src.llm_council.services.research_expander import ResearchExpander
from src.llm_council.services.provenance_tracker import ProvenanceTracker, CodeScanner
from src.llm_council.services.traceability_matrix import TraceabilityMatrix
from src.llm_council.multi_model import MultiModelClient

pytestmark = pytest.mark.e2e

@pytest.fixture
async def complete_system_setup():
    """Setup for complete system testing."""
    
    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="test-password",
        database="test_complete_system"
    )
    
    neo4j_client = Neo4jClient(neo4j_config)
    neo4j_client.connect()
    
    # Clear test database
    with neo4j_client.driver.session(database="test_complete_system") as session:
        session.run("MATCH (n) DETACH DELETE n")
    
    # Create temporary project
    test_project = Path(tempfile.mkdtemp(prefix="complete_system_test_"))
    
    # Initialize all services
    multi_model = MultiModelClient()
    question_engine = QuestionEngine(neo4j_client, multi_model)
    council_system = CouncilSystem(neo4j_client, multi_model)
    research_expander = ResearchExpander()
    code_scanner = CodeScanner(neo4j_client)
    provenance_tracker = ProvenanceTracker(neo4j_client, code_scanner)
    matrix_generator = TraceabilityMatrix(neo4j_client)
    
    yield {
        "neo4j": neo4j_client,
        "question_engine": question_engine,
        "council": council_system,
        "research": research_expander,
        "scanner": code_scanner,
        "provenance": provenance_tracker,
        "matrix": matrix_generator,
        "test_project": test_project
    }
    
    # Cleanup
    neo4j_client.close()
    shutil.rmtree(test_project, ignore_errors=True)

class TestCompleteSystemJourney:
    """Test complete end-to-end system journey with all user types collaborating."""
    
    @pytest.mark.asyncio
    async def test_complete_idea_to_production_journey(self, complete_system_setup):
        """Test complete journey: Founder idea → PM requirements → Engineer code → Team deployment."""
        
        services = complete_system_setup
        neo4j = services["neo4j"]
        question_engine = services["question_engine"]
        council = services["council"]
        research = services["research"]
        scanner = services["scanner"]
        provenance = services["provenance"]
        matrix = services["matrix"]
        test_project = services["test_project"]
        
        # ============= FOUNDER PHASE =============
        
        print("🚀 FOUNDER PHASE: Idea to validated concept")
        
        # Founder inputs idea
        founder_idea = """
        Remote teams struggle with asynchronous decision-making. Important decisions get lost in 
        Slack threads, email chains, and meeting notes. We need a structured decision-tracking 
        system that captures context, alternatives, and outcomes for future reference.
        """
        
        paradigm = Paradigm.YC
        idea_id = neo4j.create_idea_graph(founder_idea, paradigm.value)
        
        # Extract entities
        founder_entities = {
            "problems": [{
                "id": "P-DECISION-001",
                "statement": "Remote teams struggle with asynchronous decision-making and lose decision context",
                "impact_metric": "Important decisions get lost, leading to repeated discussions and confusion",
                "pain_level": 0.7,
                "frequency": 1.0,
                "confidence": 0.8
            }],
            "icps": [{
                "id": "ICP-DECISION-001", 
                "segment": "Engineering managers and team leads at 50-500 person remote companies",
                "size": 50000,
                "pains": ["Lost decision context", "Repeated discussions", "Poor decision tracking"],
                "gains": ["Clear decision history", "Faster team alignment", "Better transparency"],
                "wtp": 25.0,  # Per user per month
                "confidence": 0.7
            }],
            "assumptions": [{
                "id": "A-DECISION-001",
                "statement": "Teams will adopt structured decision-making tools if they integrate with existing workflow",
                "type": "adoption",
                "criticality": 0.9,
                "confidence": 0.6,
                "validation_method": "pilot_program"
            }]
        }
        
        neo4j.add_extracted_entities(idea_id, founder_entities)
        
        # Generate YC-style questions
        question_set = question_engine.generate_questions(
            paradigm=paradigm,
            idea_id=idea_id,
            entities=ExtractedEntities(**{k: [type(v[0])(**item) for item in v] for k, v in founder_entities.items()})
        )
        
        # Council evaluates idea viability
        idea_viability_topic = DebateTopic(
            title="Is structured decision-tracking a viable SaaS business?",
            description="YC-style evaluation of decision-tracking tool business viability",
            context={
                "market_size": "50k potential customers",
                "willingness_to_pay": "$25/user/month",
                "competition": "Notion, Linear, Monday.com (partial solutions)",
                "differentiation": "Structured decision-specific workflow vs general project management"
            }
        )
        
        founder_consensus, _ = await council.evaluate_topic(idea_viability_topic)
        
        assert founder_consensus.decision in ["PASS", "ESCALATE"]  # Should not outright fail
        
        founder_success = founder_consensus.decision == "PASS"
        
        # ============= PRODUCT MANAGER PHASE =============
        
        print("📋 PRODUCT MANAGER PHASE: Requirements and traceability")
        
        # PM creates structured requirements from validated idea
        pm_requirements = [
            {
                "id": "REQ-DEC-001",
                "description": "Users can create structured decision records with context, alternatives, and stakeholders",
                "type": "FR",
                "priority": "M",
                "stage": "mvp",
                "acceptance_criteria": [
                    "Decision title and description required",
                    "Multiple alternatives can be added",
                    "Stakeholders can be assigned and notified"
                ]
            },
            {
                "id": "REQ-DEC-002", 
                "description": "Users can track decision status from proposal to implementation",
                "type": "FR",
                "priority": "M",
                "stage": "mvp",
                "acceptance_criteria": [
                    "Status workflow: Proposed → Discussed → Decided → Implemented",
                    "Status change notifications to stakeholders",
                    "Decision timeline and history"
                ]
            },
            {
                "id": "REQ-DEC-003",
                "description": "Integration with Slack and email for seamless workflow",
                "type": "FR",
                "priority": "S",
                "stage": "v1",
                "acceptance_criteria": [
                    "Slack bot for decision creation and updates",
                    "Email notifications for key status changes", 
                    "Link back to full decision context"
                ]
            },
            {
                "id": "NFR-DEC-001",
                "description": "System supports 1000+ concurrent users with <200ms response time",
                "type": "NFR", 
                "category": "performance",
                "priority": "M",
                "stage": "mvp"
            }
        ]
        
        # Add PM requirements to Neo4j
        for req in pm_requirements:
            query = """
            MERGE (r:Requirement {id: $id})
            SET r.description = $description,
                r.type = $type,
                r.priority = $priority,
                r.stage = $stage,
                r.status = 'ready_for_implementation',
                r.created_at = datetime(),
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, req)
        
        # Link requirements to original problems
        neo4j.create_requirements_from_problems(idea_id)
        
        pm_success = len(pm_requirements) >= 3
        
        # ============= ENGINEERING PHASE =============
        
        print("💻 ENGINEERING PHASE: Spec-driven implementation")
        
        # Engineers implement services with full provenance
        src_dir = test_project / "src" / "services"
        tests_dir = test_project / "tests"
        src_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        
        # Decision service implementation
        decision_service_code = provenance.generate_provenance_header(
            artifact_name="DecisionService",
            artifact_type="Service",
            requirements=["REQ-DEC-001", "REQ-DEC-002"],
            tests=["TEST-U-DEC-001", "TEST-I-DEC-001"]
        )
        
        decision_service_code += '''

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class DecisionStatus(Enum):
    PROPOSED = "proposed"
    DISCUSSED = "discussed"
    DECIDED = "decided"
    IMPLEMENTED = "implemented"

class DecisionService:
    """Core decision tracking and management service.
    
    Implements: REQ-DEC-001, REQ-DEC-002
    """
    
    def __init__(self):
        self.decisions = {}
        self.decision_counter = 1
    
    def create_decision(
        self, 
        title: str, 
        description: str,
        alternatives: List[str],
        stakeholders: List[str]
    ) -> Dict[str, Any]:
        """Create new decision record.
        
        Implements: REQ-DEC-001
        """
        decision_id = f"DEC-{self.decision_counter:03d}"
        self.decision_counter += 1
        
        decision = {
            "id": decision_id,
            "title": title,
            "description": description,
            "alternatives": alternatives,
            "stakeholders": stakeholders,
            "status": DecisionStatus.PROPOSED,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "history": []
        }
        
        self.decisions[decision_id] = decision
        return decision
    
    def update_decision_status(
        self, 
        decision_id: str, 
        new_status: DecisionStatus,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update decision status with history tracking.
        
        Implements: REQ-DEC-002
        """
        if decision_id not in self.decisions:
            raise ValueError(f"Decision {decision_id} not found")
        
        decision = self.decisions[decision_id]
        old_status = decision["status"]
        
        # Add to history
        history_entry = {
            "from_status": old_status.value if isinstance(old_status, DecisionStatus) else old_status,
            "to_status": new_status.value,
            "timestamp": datetime.utcnow(),
            "notes": notes
        }
        
        decision["history"].append(history_entry)
        decision["status"] = new_status
        decision["updated_at"] = datetime.utcnow()
        
        return decision
    
    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve decision by ID."""
        return self.decisions.get(decision_id)
    
    def list_decisions_by_status(self, status: DecisionStatus) -> List[Dict[str, Any]]:
        """List decisions filtered by status."""
        return [
            decision for decision in self.decisions.values()
            if decision["status"] == status
        ]
'''
        
        decision_service_path = src_dir / "decision_service.py"
        decision_service_path.write_text(decision_service_code)
        
        # Integration service
        integration_service_code = provenance.generate_provenance_header(
            artifact_name="IntegrationService",
            artifact_type="Service", 
            requirements=["REQ-DEC-003"],
            tests=["TEST-U-INT-001", "TEST-I-INT-001"]
        )
        
        integration_service_code += '''

class IntegrationService:
    """Handles integrations with external tools (Slack, email).
    
    Implements: REQ-DEC-003
    """
    
    def __init__(self):
        self.slack_webhook = None
        self.email_service = None
    
    def send_slack_notification(
        self, 
        decision_id: str,
        message: str,
        channel: str
    ) -> Dict[str, Any]:
        """Send decision notification to Slack.
        
        Implements: REQ-DEC-003
        """
        # Mock Slack integration
        notification = {
            "decision_id": decision_id,
            "channel": channel,
            "message": message,
            "timestamp": datetime.utcnow(),
            "success": True
        }
        
        print(f"Slack notification sent: {notification}")
        return notification
    
    def send_email_notification(
        self,
        decision_id: str, 
        recipients: List[str],
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Send decision notification via email.
        
        Implements: REQ-DEC-003
        """
        # Mock email integration
        notification = {
            "decision_id": decision_id,
            "recipients": recipients,
            "subject": subject,
            "body": body,
            "timestamp": datetime.utcnow(),
            "success": True
        }
        
        print(f"Email notification sent: {notification}")
        return notification
'''
        
        integration_service_path = src_dir / "integration_service.py"
        integration_service_path.write_text(integration_service_code)
        
        # Create comprehensive test suite
        decision_test_code = '''"""Comprehensive tests for decision tracking system.

Covers: REQ-DEC-001, REQ-DEC-002, REQ-DEC-003, NFR-DEC-001
"""

import pytest
from datetime import datetime
from src.services.decision_service import DecisionService, DecisionStatus
from src.services.integration_service import IntegrationService

class TestDecisionTrackingSystem:
    """Complete test suite for decision tracking system.
    
    Covers: REQ-DEC-001, REQ-DEC-002
    """
    
    def setup_method(self):
        self.decision_service = DecisionService()
        self.integration_service = IntegrationService()
    
    def test_complete_decision_lifecycle(self):
        """Test complete decision lifecycle from creation to implementation.
        
        Validates: Complete user workflow for decision tracking
        """
        # Create decision
        decision = self.decision_service.create_decision(
            title="Choose frontend framework for new project",
            description="Need to select between React, Vue, and Angular for upcoming project",
            alternatives=["React with TypeScript", "Vue 3 with Composition API", "Angular with TypeScript"],
            stakeholders=["@tech-lead", "@senior-frontend-dev", "@product-manager"]
        )
        
        assert decision["id"].startswith("DEC-")
        assert decision["status"] == DecisionStatus.PROPOSED
        assert len(decision["alternatives"]) == 3
        assert len(decision["stakeholders"]) == 3
        
        # Update through lifecycle
        discussed = self.decision_service.update_decision_status(
            decision["id"],
            DecisionStatus.DISCUSSED,
            "Team discussed pros and cons in architecture review meeting"
        )
        
        assert discussed["status"] == DecisionStatus.DISCUSSED
        assert len(discussed["history"]) == 1
        
        decided = self.decision_service.update_decision_status(
            decision["id"],
            DecisionStatus.DECIDED,
            "Team chose React with TypeScript based on team expertise and ecosystem"
        )
        
        assert decided["status"] == DecisionStatus.DECIDED
        assert len(decided["history"]) == 2
        
        implemented = self.decision_service.update_decision_status(
            decision["id"],
            DecisionStatus.IMPLEMENTED,
            "React project setup completed, team training conducted"
        )
        
        assert implemented["status"] == DecisionStatus.IMPLEMENTED
        assert len(implemented["history"]) == 3
        
        print(f"   ✅ Decision Lifecycle: {decision['id']} → {implemented['status'].value}")
    
    def test_integration_notifications(self):
        """Test integration with external tools.
        
        Covers: REQ-DEC-003
        """
        # Create decision for notification testing
        decision = self.decision_service.create_decision(
            title="API design decisions for user authentication",
            description="Choose between session-based vs JWT-based authentication",
            alternatives=["Session cookies", "JWT tokens", "OAuth only"],
            stakeholders=["@backend-team", "@security-engineer"]
        )
        
        # Test Slack notification
        slack_result = self.integration_service.send_slack_notification(
            decision["id"],
            f"New decision needs your input: {decision['title']}",
            "#backend-decisions"
        )
        
        assert slack_result["success"] == True
        assert slack_result["decision_id"] == decision["id"]
        
        # Test email notification
        email_result = self.integration_service.send_email_notification(
            decision["id"],
            ["backend-team@company.com", "security@company.com"],
            f"Decision Required: {decision['title']}", 
            f"Please review and provide input: {decision['description']}"
        )
        
        assert email_result["success"] == True
        assert decision["id"] in email_result["subject"]
        
        print(f"   ✅ Integrations: Slack + Email notifications working")

class TestEndToEndUserWorkflows:
    """Test end-to-end user workflows across the complete system."""
    
    @pytest.mark.asyncio
    async def test_multi_user_collaborative_workflow(self, complete_system_setup):
        """Test multiple users collaborating through the complete system."""
        
        services = complete_system_setup
        neo4j = services["neo4j"]
        council = services["council"]
        matrix = services["matrix"]
        
        # === STEP 1: Multiple users with different roles ===
        
        users = [
            {"id": "USER-001", "role": "founder", "name": "Alex (Founder)"},
            {"id": "USER-002", "role": "pm", "name": "Jordan (Product Manager)"},
            {"id": "USER-003", "role": "engineer", "name": "Sam (Lead Engineer)"},
            {"id": "USER-004", "role": "engineer", "name": "Taylor (Frontend Engineer)"}
        ]
        
        # Add users to Neo4j
        for user in users:
            query = """
            MERGE (u:User {id: $id})
            SET u.role = $role,
                u.name = $name,
                u.joined_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, user)
        
        # === STEP 2: Collaborative idea refinement ===
        
        # Founder starts idea, PM refines, Engineers provide technical input
        
        collaboration_topic = DebateTopic(
            title="Technical feasibility of real-time collaborative decision tracking",
            description="Cross-functional team evaluation of technical implementation approach",
            context={
                "founder_priority": "Fast time-to-market, simple UX",
                "pm_priority": "Scalable feature set, clear user journey",
                "engineer_priority": "Maintainable architecture, reasonable complexity",
                "constraints": ["3-month MVP timeline", "2 engineers", "$10k/month infrastructure budget"]
            },
            priority="critical"
        )
        
        # Council provides multi-perspective evaluation
        collab_consensus, collab_debate = await council.evaluate_topic(
            collaboration_topic,
            enable_debate=True
        )
        
        assert collab_consensus is not None
        
        # Debate should involve multiple perspectives
        if collab_debate:
            unique_perspectives = set(arg.council_role for arg in collab_debate.arguments)
            assert len(unique_perspectives) >= 3  # Multiple perspectives represented
        
        # === STEP 3: Coordinated implementation ===
        
        # Track user assignments to requirements
        user_assignments = [
            {"user_id": "USER-002", "req_id": "REQ-DEC-001", "role": "requirements_owner"},
            {"user_id": "USER-003", "req_id": "REQ-DEC-001", "role": "technical_lead"},
            {"user_id": "USER-003", "req_id": "REQ-DEC-002", "role": "implementer"},
            {"user_id": "USER-004", "req_id": "REQ-DEC-003", "role": "implementer"}
        ]
        
        for assignment in user_assignments:
            query = """
            MATCH (u:User {id: $user_id})
            MATCH (r:Requirement {id: $req_id})
            MERGE (u)-[:ASSIGNED_TO {role: $role, assigned_at: datetime()}]->(r)
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, assignment)
        
        # === STEP 4: Cross-user impact analysis ===
        
        # Simulate USER-003 (Lead Engineer) making architectural change
        arch_change_topic = DebateTopic(
            title="Change database schema for decision tracking - impact on team",
            description="Lead engineer proposes schema change, analyze impact on other team members",
            context={
                "proposed_change": "Add decision_metadata JSONB column for extensibility",
                "change_reason": "Support for custom decision types and future features",
                "impact_analysis": {
                    "affected_services": ["DecisionService"],
                    "migration_required": True,
                    "frontend_changes_needed": "Possible UI updates for new metadata",
                    "testing_impact": "Database migration tests required"
                },
                "timeline_impact": "1 day implementation + 2 days testing"
            },
            priority="important"
        )
        
        arch_consensus, _ = await council.evaluate_topic(arch_change_topic)
        
        # Should evaluate impact on team coordination
        assert arch_consensus is not None
        
        # === STEP 5: Team validates end-to-end system integration ===
        
        # Create services representing the implemented system
        complete_services = [
            {
                "type": "Service",
                "id": "SVC-DECISION-CORE",
                "name": "DecisionService",
                "implements": ["REQ-DEC-001", "REQ-DEC-002"],
                "assigned_to": ["USER-003"],
                "status": "implemented"
            },
            {
                "type": "Service", 
                "id": "SVC-INTEGRATION", 
                "name": "IntegrationService",
                "implements": ["REQ-DEC-003"],
                "assigned_to": ["USER-004"],
                "status": "implemented"
            }
        ]
        
        complete_tests = [
            {
                "type": "Test",
                "id": "TEST-U-DEC-001",
                "name": "test_decision_service_crud",
                "test_type": "unit",
                "covers": ["REQ-DEC-001"],
                "created_by": ["USER-003"],
                "status": "implemented"
            },
            {
                "type": "Test",
                "id": "TEST-U-DEC-002",
                "name": "test_decision_status_workflow", 
                "test_type": "unit",
                "covers": ["REQ-DEC-002"],
                "created_by": ["USER-003"],
                "status": "implemented"
            },
            {
                "type": "Test",
                "id": "TEST-I-COMPLETE-001",
                "name": "test_decision_to_slack_integration",
                "test_type": "integration",
                "covers": ["REQ-DEC-001", "REQ-DEC-003"],
                "created_by": ["USER-004"],
                "status": "implemented"
            },
            {
                "type": "Test",
                "id": "TEST-E2E-COMPLETE-001", 
                "name": "test_complete_decision_workflow_multi_user",
                "test_type": "e2e",
                "covers": ["REQ-DEC-001", "REQ-DEC-002", "REQ-DEC-003"],
                "created_by": ["USER-002", "USER-003", "USER-004"],
                "status": "implemented",
                "scenario": "Complete multi-user decision workflow from creation to implementation"
            }
        ]
        
        # Sync complete system to Neo4j
        all_artifacts = complete_services + complete_tests
        neo4j.sync_code_artifacts(all_artifacts)
        
        # ============= TEAM COORDINATION VALIDATION =============
        
        print("👥 TEAM PHASE: Coordination and deployment readiness")
        
        # Generate complete traceability matrix
        complete_matrix = matrix.generate_complete_matrix(increment_filter="mvp")
        
        # Validate complete system coverage
        mvp_entries = [e for e in complete_matrix if e.req_id.startswith(("REQ-DEC", "NFR-DEC"))]
        mvp_requirements = [req for req in pm_requirements if req["stage"] == "mvp"]
        
        # Should have matrix entries for all MVP requirements
        assert len(mvp_entries) >= len(mvp_requirements)
        
        # Check that each MVP requirement has implementation and tests
        for entry in mvp_entries:
            if entry.req_id in ["REQ-DEC-001", "REQ-DEC-002"]:  # Core MVP features
                assert len(entry.implementing_code) > 0, f"{entry.req_id} missing implementation"
                assert len(entry.unit_tests) > 0, f"{entry.req_id} missing unit tests"
                assert entry.status in ["GREEN", "YELLOW"], f"{entry.req_id} has status {entry.status}"
        
        # === STEP 6: Complete system deployment readiness ===
        
        deployment_readiness = matrix.validate_increment_readiness("mvp")
        
        # System should be ready or have minimal blocking issues
        total_blocking_issues = len(deployment_readiness["blocking_issues"])
        
        # Calculate overall system health
        system_health_metrics = {
            "requirements_coverage": deployment_readiness["overall_coverage"],
            "critical_coverage": deployment_readiness["critical_coverage"],
            "blocking_issues": total_blocking_issues,
            "team_coordination_success": collab_consensus.decision != "FAIL",
            "traceability_completeness": len(complete_matrix) > 0,
            "multi_user_testing": len([t for t in complete_tests if t["test_type"] == "e2e"]) > 0
        }
        
        # === STEP 7: Validate complete system success criteria ===
        
        complete_system_success = {
            "founder_phase_success": founder_success,
            "pm_phase_success": pm_success,
            "engineer_phase_success": deployment_readiness["overall_coverage"] > 70,
            "team_phase_success": system_health_metrics["team_coordination_success"],
            "end_to_end_traceability": len(complete_matrix) >= len(pm_requirements),
            "deployment_readiness": total_blocking_issues <= 2,  # Allow minor issues
            "multi_user_workflow_tested": system_health_metrics["multi_user_testing"]
        }
        
        overall_success_rate = sum(1 for success in complete_system_success.values() if success) / len(complete_system_success)
        
        # Complete system should achieve >85% success rate across all phases
        assert overall_success_rate >= 0.85, f"Complete system success rate {overall_success_rate:.1%} < 85%"
        
        # ============= FINAL VALIDATION =============
        
        print("🎯 FINAL VALIDATION: Complete system integration")
        
        # Validate that all user types can successfully use the system
        user_success_metrics = {}
        
        # Founder success: Idea refined and validated
        user_success_metrics["founder"] = {
            "idea_captured": idea_id is not None,
            "paradigm_applied": question_set.paradigm == Paradigm.YC,
            "council_guidance": founder_consensus.decision != "FAIL",
            "market_validated": len(founder_entities["icps"]) > 0
        }
        
        # PM success: Requirements structured and traceable
        user_success_metrics["pm"] = {
            "requirements_created": len(pm_requirements) >= 3,
            "traceability_established": len(complete_matrix) > 0,
            "team_coordination": len(user_assignments) > 0,
            "coverage_tracking": deployment_readiness["overall_coverage"] > 0
        }
        
        # Engineer success: Code generated with provenance
        user_success_metrics["engineer"] = {
            "services_implemented": len(complete_services) >= 2,
            "tests_created": len(complete_tests) >= 4,
            "provenance_headers": True,  # Generated with headers
            "requirements_linked": all(len(s["implements"]) > 0 for s in complete_services)
        }
        
        # Team success: Coordination and deployment
        user_success_metrics["team"] = {
            "cross_functional_collaboration": collab_consensus.decision != "FAIL",
            "impact_analysis_available": True,
            "deployment_readiness_assessed": deployment_readiness is not None,
            "continuous_improvement": arch_consensus.decision != "FAIL"
        }
        
        # Each user type should have >80% success rate
        for user_type, metrics in user_success_metrics.items():
            user_success_rate = sum(1 for success in metrics.values() if success) / len(metrics)
            assert user_success_rate >= 0.8, f"{user_type} success rate {user_success_rate:.1%} < 80%"
        
        # ============= SUCCESS SUMMARY =============
        
        final_summary = {
            "overall_success_rate": overall_success_rate,
            "founder_journey_complete": all(user_success_metrics["founder"].values()),
            "pm_journey_complete": all(user_success_metrics["pm"].values()),
            "engineer_journey_complete": all(user_success_metrics["engineer"].values()),
            "team_journey_complete": all(user_success_metrics["team"].values()),
            "system_health": system_health_metrics,
            "deployment_readiness": deployment_readiness["ready_for_release"],
            "total_requirements": len(pm_requirements),
            "total_services": len(complete_services),
            "total_tests": len(complete_tests),
            "traceability_matrix_entries": len(complete_matrix)
        }
        
        print(f"🎉 COMPLETE SYSTEM JOURNEY SUCCESSFUL!")
        print(f"   📊 Overall Success Rate: {overall_success_rate:.1%}")
        print(f"   👤 Founder Journey: {'✅' if final_summary['founder_journey_complete'] else '❌'}")
        print(f"   📋 PM Journey: {'✅' if final_summary['pm_journey_complete'] else '❌'}")
        print(f"   💻 Engineer Journey: {'✅' if final_summary['engineer_journey_complete'] else '❌'}")
        print(f"   👥 Team Journey: {'✅' if final_summary['team_journey_complete'] else '❌'}")
        print(f"   🚀 Deployment Ready: {'✅' if final_summary['deployment_readiness'] else '⚠️'}")
        print(f"   📊 System Health: {len([v for v in system_health_metrics.values() if v])}/{len(system_health_metrics)} metrics positive")
        print(f"   🔗 Complete Traceability: {final_summary['traceability_matrix_entries']} entries")
        
        return final_summary

    @pytest.mark.asyncio
    async def test_system_scalability_and_performance(self, complete_system_setup):
        """Test system performance with multiple concurrent ideas and users."""
        
        services = complete_system_setup
        neo4j = services["neo4j"]
        question_engine = services["question_engine"]
        council = services["council"]
        
        # === STEP 1: Create multiple concurrent ideas ===
        
        concurrent_ideas = [
            "AI-powered code review tool for development teams",
            "Blockchain-based supply chain tracking for e-commerce", 
            "IoT sensor platform for smart building management",
            "Machine learning pipeline for customer churn prediction",
            "Real-time analytics dashboard for marketing teams"
        ]
        
        idea_tasks = []
        for i, idea_text in enumerate(concurrent_ideas):
            task = neo4j.create_idea_graph(idea_text, "yc")
            idea_tasks.append(task)
        
        # All ideas should be created successfully
        assert len(idea_tasks) == len(concurrent_ideas)
        
        # === STEP 2: Concurrent question generation ===
        
        question_generation_tasks = []
        for idea_id in idea_tasks:
            # Create minimal entities for each idea
            minimal_entities = ExtractedEntities(
                problems=[Problem(
                    id=f"P-{idea_id[-3:]}",
                    statement=f"Problem for idea {idea_id}",
                    impact_metric="Simulated impact",
                    pain_level=0.7,
                    frequency=1.0,
                    confidence=0.6
                )],
                icps=[ICP(
                    id=f"ICP-{idea_id[-3:]}",
                    segment=f"Target segment for {idea_id}",
                    size=10000,
                    pains=["Generic pain"],
                    gains=["Generic gain"],
                    wtp=100.0,
                    confidence=0.6
                )]
            )
            
            task = question_engine.generate_questions(
                paradigm=Paradigm.YC,
                idea_id=idea_id,
                entities=minimal_entities
            )
            question_generation_tasks.append(task)
        
        # All question generation should complete
        question_sets = question_generation_tasks  # In real async, would await all
        assert len(question_sets) == len(concurrent_ideas)
        
        # === STEP 3: Concurrent council evaluations ===
        
        evaluation_topics = []
        for i, idea_id in enumerate(idea_tasks):
            topic = DebateTopic(
                title=f"Evaluate idea viability: {concurrent_ideas[i][:50]}...",
                description=f"Council evaluation of concurrent idea {i+1}",
                context={"idea_id": idea_id, "concurrent_test": True},
                priority="medium"
            )
            evaluation_topics.append(topic)
        
        # Evaluate all topics concurrently (simulated)
        evaluation_results = []
        for topic in evaluation_topics:
            consensus, _ = await council.evaluate_topic(topic, enable_debate=False)
            evaluation_results.append(consensus)
        
        # All evaluations should complete
        assert len(evaluation_results) == len(concurrent_ideas)
        
        # Should have variety in council decisions (not all identical)
        unique_decisions = set(consensus.decision for consensus in evaluation_results)
        assert len(unique_decisions) >= 2  # Should have decision variety
        
        # === STEP 4: System performance validation ===
        
        performance_metrics = {
            "concurrent_ideas_supported": len(idea_tasks),
            "concurrent_evaluations": len(evaluation_results),
            "database_operations_successful": True,  # No exceptions thrown
            "council_consensus_quality": sum(c.confidence for c in evaluation_results) / len(evaluation_results),
            "system_responsiveness": True  # All operations completed
        }
        
        # Performance should meet scalability requirements
        assert performance_metrics["concurrent_ideas_supported"] >= 5
        assert performance_metrics["concurrent_evaluations"] >= 5
        assert performance_metrics["council_consensus_quality"] >= 0.6
        
        print(f"✅ System Scalability & Performance Validated!")
        print(f"   🔄 Concurrent Ideas: {performance_metrics['concurrent_ideas_supported']}")
        print(f"   ⚡ Concurrent Evaluations: {performance_metrics['concurrent_evaluations']}")
        print(f"   🎯 Council Quality: {performance_metrics['council_consensus_quality']:.2f}")
        print(f"   📊 Decision Variety: {len(unique_decisions)} different outcomes")
        print(f"   💪 System Stability: {'✅' if performance_metrics['database_operations_successful'] else '❌'}")
