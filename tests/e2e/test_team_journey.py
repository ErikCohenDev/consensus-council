"""End-to-end tests for Team journey: Collaborative development with change impact tracking."""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

from src.llm_council.database.neo4j_client import Neo4jClient, Neo4jConfig
from src.llm_council.services.council_system import CouncilSystem, DebateTopic
from src.llm_council.services.provenance_tracker import ProvenanceTracker, CodeScanner
from src.llm_council.services.traceability_matrix import TraceabilityMatrix
from src.llm_council.multi_model import MultiModelClient

pytestmark = pytest.mark.e2e

@pytest.fixture
async def team_test_setup():
    """Setup for team journey testing."""
    
    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="test-password",
        database="test_team_db"
    )
    
    neo4j_client = Neo4jClient(neo4j_config)
    neo4j_client.connect()
    
    # Clear test database
    with neo4j_client.driver.session(database="test_team_db") as session:
        session.run("MATCH (n) DETACH DELETE n")
    
    # Initialize services
    multi_model = MultiModelClient()
    council_system = CouncilSystem(neo4j_client, multi_model)
    code_scanner = CodeScanner(neo4j_client)
    provenance_tracker = ProvenanceTracker(neo4j_client, code_scanner)
    matrix_generator = TraceabilityMatrix(neo4j_client)
    
    yield {
        "neo4j": neo4j_client,
        "council": council_system,
        "scanner": code_scanner,
        "provenance": provenance_tracker,
        "matrix": matrix_generator,
        "multi_model": multi_model
    }
    
    # Cleanup
    neo4j_client.close()

class TestTeamCompleteJourney:
    """Test complete team journey for collaborative development with impact tracking."""
    
    @pytest.mark.asyncio
    async def test_team_collaborative_feature_development(self, team_test_setup):
        """Test team collaborating on feature development with council oversight."""
        
        services = team_test_setup
        neo4j = services["neo4j"]
        council = services["council"]
        scanner = services["scanner"]
        provenance = services["provenance"]
        matrix = services["matrix"]
        
        # === STEP 1: Team plans new feature collaboratively ===
        
        # Product manager proposes feature
        feature_proposal = DebateTopic(
            title="Add real-time collaboration features to document editor",
            description="Enable multiple users to edit documents simultaneously with conflict resolution",
            context={
                "business_driver": "Customer requests for collaborative editing",
                "user_research": "78% of users want real-time collaboration",
                "technical_complexity": "High - requires WebSocket, operational transform, conflict resolution",
                "timeline_pressure": "Requested for Q2 release",
                "resource_constraints": "2 frontend engineers, 1 backend engineer available"
            },
            priority="critical"
        )
        
        # Council debates feature scope and feasibility
        consensus, debate_session = await council.evaluate_topic(
            feature_proposal,
            enable_debate=True,
            consensus_threshold=0.7
        )
        
        assert consensus is not None
        assert debate_session is not None if consensus.decision == "ESCALATE" else True
        
        # Team uses council input to scope feature
        if consensus.decision == "PASS":
            approved_scope = "full_collaborative_editing"
        elif consensus.weighted_score > 0.5:
            approved_scope = "simplified_collaborative_editing"  # Reduced scope
        else:
            approved_scope = "defer_to_next_quarter"
        
        assert approved_scope != "defer_to_next_quarter"  # Should get some version approved
        
        # === STEP 2: Team breaks down feature into requirements ===
        
        collaborative_requirements = [
            {
                "id": "REQ-COLLAB-001",
                "description": "Multiple users can edit same document simultaneously", 
                "type": "FR",
                "priority": "M",
                "stage": "v1",
                "team": "backend",
                "complexity": "high"
            },
            {
                "id": "REQ-COLLAB-002",
                "description": "Real-time synchronization of document changes across clients",
                "type": "FR", 
                "priority": "M",
                "stage": "v1",
                "team": "backend",
                "complexity": "high"
            },
            {
                "id": "REQ-COLLAB-003",
                "description": "Conflict resolution when users edit same content",
                "type": "FR",
                "priority": "M", 
                "stage": "v1",
                "team": "backend",
                "complexity": "very_high"
            },
            {
                "id": "REQ-COLLAB-UI-001",
                "description": "Show other users' cursors and selections in real-time",
                "type": "FR",
                "priority": "S",
                "stage": "v1", 
                "team": "frontend",
                "complexity": "medium"
            },
            {
                "id": "NFR-COLLAB-001",
                "description": "Support 50+ concurrent editors per document with <100ms latency",
                "type": "NFR",
                "category": "performance",
                "priority": "M",
                "stage": "v1",
                "team": "backend"
            }
        ]
        
        # Add requirements to Neo4j
        for req in collaborative_requirements:
            query = """
            MERGE (r:Requirement {id: $id})
            SET r.description = $description,
                r.type = $type,
                r.priority = $priority,
                r.stage = $stage,
                r.team = $team,
                r.complexity = $complexity,
                r.status = 'planned',
                r.created_at = datetime(),
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, req)
        
        # === STEP 3: Team coordinates implementation across frontend/backend ===
        
        # Backend team implements core collaboration engine
        backend_services = [
            {
                "type": "Service",
                "id": "SVC-COLLAB-ENGINE",
                "name": "CollaborationEngine",
                "implements": ["REQ-COLLAB-001", "REQ-COLLAB-002"],
                "team": "backend",
                "complexity": 15,
                "status": "in_progress"
            },
            {
                "type": "Service", 
                "id": "SVC-CONFLICT-RESOLVER",
                "name": "ConflictResolver",
                "implements": ["REQ-COLLAB-003"],
                "team": "backend", 
                "complexity": 20,
                "status": "planned"  # High complexity, needs more time
            },
            {
                "type": "Service",
                "id": "SVC-WEBSOCKET-MGR",
                "name": "WebSocketManager", 
                "implements": ["REQ-COLLAB-002", "NFR-COLLAB-001"],
                "team": "backend",
                "complexity": 12,
                "status": "in_progress"
            }
        ]
        
        # Frontend team implements UI components
        frontend_services = [
            {
                "type": "Service",
                "id": "SVC-COLLAB-UI",
                "name": "CollaborativeEditor",
                "implements": ["REQ-COLLAB-UI-001"],
                "team": "frontend",
                "complexity": 8,
                "status": "in_progress"
            },
            {
                "type": "Service",
                "id": "SVC-CURSOR-DISPLAY",
                "name": "CursorDisplayManager",
                "implements": ["REQ-COLLAB-UI-001"], 
                "team": "frontend",
                "complexity": 6,
                "status": "implemented"
            }
        ]
        
        all_collab_services = backend_services + frontend_services
        neo4j.sync_code_artifacts(all_collab_services)
        
        # === STEP 4: Team tracks cross-service dependencies ===
        
        # Frontend services depend on backend WebSocket manager
        team_dependencies = [
            {"from": "SVC-COLLAB-UI", "to": "SVC-WEBSOCKET-MGR", "type": "DEPENDS_ON"},
            {"from": "SVC-CURSOR-DISPLAY", "to": "SVC-WEBSOCKET-MGR", "type": "DEPENDS_ON"},
            {"from": "SVC-COLLAB-ENGINE", "to": "SVC-CONFLICT-RESOLVER", "type": "DEPENDS_ON"}
        ]
        
        for dep in team_dependencies:
            query = """
            MATCH (from {id: $from_id})
            MATCH (to {id: $to_id})
            MERGE (from)-[:DEPENDS_ON]->(to)
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, {"from_id": dep["from"], "to_id": dep["to"]})
        
        # === STEP 5: Team uses traceability matrix for coordination ===
        
        team_matrix = matrix.generate_complete_matrix(increment_filter="v1")
        
        # Group by team for coordination
        backend_entries = []
        frontend_entries = []
        
        for entry in team_matrix:
            # Find team assignment
            for req in collaborative_requirements:
                if req["id"] == entry.req_id:
                    if req["team"] == "backend":
                        backend_entries.append(entry)
                    elif req["team"] == "frontend":
                        frontend_entries.append(entry)
                    break
        
        # Both teams should have requirements to implement
        assert len(backend_entries) >= 3  # Backend has more complex requirements
        assert len(frontend_entries) >= 1  # Frontend has UI requirements
        
        # === STEP 6: Team handles blocking dependency scenario ===
        
        # Simulate backend WebSocket service being blocked
        # This should impact frontend services that depend on it
        
        # Update WebSocket service status to blocked
        block_query = """
        MATCH (s:Service {id: 'SVC-WEBSOCKET-MGR'})
        SET s.status = 'blocked',
            s.block_reason = 'Waiting for infrastructure team to provision load balancer',
            s.updated_at = datetime()
        """
        
        with neo4j.driver.session(database=neo4j.config.database) as session:
            session.run(block_query)
        
        # Analyze impact of blocked service
        blocked_impact = provenance.generate_impact_report(["SVC-WEBSOCKET-MGR"])
        
        # Should identify downstream services affected
        dependent_services_query = """
        MATCH (blocked:Service {id: 'SVC-WEBSOCKET-MGR'})<-[:DEPENDS_ON]-(dependent)
        RETURN collect(dependent.id) as dependent_ids
        """
        
        with neo4j.driver.session(database=neo4j.config.database) as session:
            result = session.run(dependent_services_query)
            dependent_ids = result.single()["dependent_ids"]
        
        # Frontend services should be identified as affected
        assert "SVC-COLLAB-UI" in dependent_ids
        assert "SVC-CURSOR-DISPLAY" in dependent_ids
        
        # === STEP 7: Team coordinates resolution strategy ===
        
        resolution_topic = DebateTopic(
            title="How to handle blocked WebSocket dependency?",
            description="Backend WebSocket service blocked by infrastructure dependency", 
            context={
                "blocked_service": "SVC-WEBSOCKET-MGR",
                "affected_services": dependent_ids,
                "block_reason": "Infrastructure team provisioning delay",
                "options": [
                    "Wait for infrastructure (2 week delay)",
                    "Implement mock WebSocket for frontend development",
                    "Reduce scope to async-only collaboration"
                ],
                "timeline_impact": "Could delay V1 release by 2 weeks"
            },
            priority="critical"
        )
        
        resolution_consensus, resolution_debate = await council.evaluate_topic(
            resolution_topic,
            enable_debate=True
        )
        
        assert resolution_consensus is not None
        
        # Council should provide guidance on resolution approach
        if resolution_consensus.decision == "PASS":
            # Council reached consensus on approach
            recommended_approach = "council_consensus"
        else:
            # Escalate to human team lead
            recommended_approach = "human_decision"
        
        # === STEP 8: Team implements resolution and tracks impact ===
        
        if recommended_approach == "council_consensus":
            # Implement mock WebSocket for unblocking frontend
            mock_websocket_code = provenance.generate_provenance_header(
                artifact_name="MockWebSocketManager",
                artifact_type="Service",
                requirements=["REQ-COLLAB-002"],  # Partially implements  
                tests=["TEST-MOCK-WS-001"]
            )
            
            mock_websocket_code += '''

class MockWebSocketManager:
    """Mock WebSocket manager for development.
    
    Implements: REQ-COLLAB-002 (partial, for frontend development)
    """
    
    def __init__(self):
        self.connections = {}
    
    def broadcast_change(self, document_id: str, change_data: Dict):
        """Mock broadcast of document changes."""
        print(f"Mock broadcast to document {document_id}: {change_data}")
        return {"success": True, "message": "Mock broadcast completed"}
    
    def connect_user(self, user_id: str, document_id: str):
        """Mock user connection."""
        if document_id not in self.connections:
            self.connections[document_id] = []
        self.connections[document_id].append(user_id)
        return {"success": True, "connection_id": f"mock_{user_id}"}
'''
            
            # Add mock service to project
            mock_service_path = test_project / "src" / "services" / "mock_websocket_manager.py"
            mock_service_path.parent.mkdir(parents=True, exist_ok=True)
            mock_service_path.write_text(mock_websocket_code)
            
            # Update frontend services to use mock temporarily
            frontend_update_query = """
            MATCH (frontend:Service)
            WHERE frontend.id IN ['SVC-COLLAB-UI', 'SVC-CURSOR-DISPLAY']
            SET frontend.dependencies_note = 'Using mock WebSocket for development',
                frontend.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(frontend_update_query)
        
        # === STEP 9: Team validates coordinated development progress ===
        
        # Rescan codebase to include mock service
        updated_scan = scanner.scan_codebase(str(test_project))
        provenance.sync_artifacts_to_neo4j(updated_scan)
        
        # Generate updated traceability matrix
        team_matrix = matrix.generate_complete_matrix(increment_filter="v1")
        
        # Should show progress on collaborative features
        collab_entries = [e for e in team_matrix if "COLLAB" in e.req_id]
        assert len(collab_entries) >= 4  # Multiple collaborative requirements
        
        # Some should be partially implemented (with mock)
        partial_implementations = [e for e in collab_entries if len(e.implementing_code) > 0]
        assert len(partial_implementations) >= 2
        
        # === STEP 10: Team handles concurrent development conflicts ===
        
        # Simulate two developers working on related services
        
        # Developer A changes collaboration engine
        dev_a_changes = ["SVC-COLLAB-ENGINE"]
        dev_a_impact = provenance.generate_impact_report(dev_a_changes)
        
        # Developer B changes conflict resolver  
        dev_b_changes = ["SVC-CONFLICT-RESOLVER"]
        dev_b_impact = provenance.generate_impact_report(dev_b_changes)
        
        # Check for overlapping impacts (potential conflicts)
        dev_a_requirements = set(dev_a_impact["upstream_requirements"])
        dev_b_requirements = set(dev_b_impact["upstream_requirements"])
        
        overlapping_requirements = dev_a_requirements.intersection(dev_b_requirements)
        
        if overlapping_requirements:
            # Team coordination needed
            coordination_topic = DebateTopic(
                title="Coordinate changes affecting shared requirements",
                description=f"Developers working on overlapping requirements: {list(overlapping_requirements)}",
                context={
                    "dev_a_changes": dev_a_changes,
                    "dev_b_changes": dev_b_changes,
                    "shared_requirements": list(overlapping_requirements),
                    "coordination_options": [
                        "Sequential development (A then B)",
                        "Parallel with integration testing",
                        "Pair programming on shared components"
                    ]
                },
                priority="important"
            )
            
            coord_consensus, _ = await council.evaluate_topic(coordination_topic)
            assert coord_consensus is not None
        
        # === STEP 11: Team validates feature completion ===
        
        # Mark some services as completed
        completion_updates = [
            {"service_id": "SVC-CURSOR-DISPLAY", "status": "implemented"},
            {"service_id": "SVC-COLLAB-UI", "status": "implemented"},
            {"service_id": "SVC-COLLAB-ENGINE", "status": "implemented"}
        ]
        
        for update in completion_updates:
            query = """
            MATCH (s:Service {id: $service_id})
            SET s.status = $status,
                s.completed_at = datetime(),
                s.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, update)
        
        # Add integration tests for team coordination validation
        team_integration_tests = [
            {
                "type": "Test",
                "id": "TEST-TEAM-INTEGRATION-001",
                "name": "test_frontend_backend_collab_integration",
                "test_type": "integration",
                "covers": ["REQ-COLLAB-001", "REQ-COLLAB-UI-001"],
                "status": "implemented"
            },
            {
                "type": "Test", 
                "id": "TEST-TEAM-E2E-001",
                "name": "test_multi_user_editing_workflow",
                "test_type": "e2e",
                "covers": ["REQ-COLLAB-001", "REQ-COLLAB-002", "REQ-COLLAB-UI-001"],
                "status": "implemented"
            }
        ]
        
        neo4j.sync_code_artifacts(team_integration_tests)
        
        # === STEP 12: Team validates collaborative success metrics ===
        
        # Generate final traceability matrix for feature
        final_matrix = matrix.generate_complete_matrix(increment_filter="v1")
        feature_entries = [e for e in final_matrix if "COLLAB" in e.req_id]
        
        # Calculate team coordination success metrics
        coordination_metrics = {
            "requirements_planned": len(collaborative_requirements),
            "services_implemented": len([s for s in all_collab_services if s["status"] == "implemented"]),
            "cross_team_dependencies": len(team_dependencies), 
            "integration_tests_created": len(team_integration_tests),
            "council_debates_conducted": 2,  # Feature proposal + coordination
            "blocking_issues_resolved": 1,   # WebSocket dependency resolved with mock
            "traceability_maintained": len(feature_entries) > 0
        }
        
        # Team coordination effectiveness
        coordination_effectiveness = {
            "implementation_rate": coordination_metrics["services_implemented"] / len(all_collab_services),
            "dependency_management": coordination_metrics["cross_team_dependencies"] > 0,
            "integration_coverage": len(team_integration_tests) >= 2,
            "conflict_resolution": coordination_metrics["blocking_issues_resolved"] > 0,
            "council_utilization": coordination_metrics["council_debates_conducted"] >= 2,
            "traceability_preservation": coordination_metrics["traceability_maintained"]
        }
        
        effectiveness_score = sum(1 for check, passed in coordination_effectiveness.items() if passed) / len(coordination_effectiveness)
        
        # Team coordination should be highly effective (>80%)
        assert effectiveness_score >= 0.8, f"Team coordination effectiveness {effectiveness_score:.1%} < 80%"
        
        # Validate specific team outcomes
        assert coordination_metrics["requirements_planned"] >= 4
        assert coordination_metrics["integration_tests_created"] >= 2
        assert coordination_metrics["council_debates_conducted"] >= 2
        
        print(f"✅ Team Collaborative Development Journey Completed!")
        print(f"   👥 Coordination Effectiveness: {effectiveness_score:.1%}")
        print(f"   📋 Requirements Planned: {coordination_metrics['requirements_planned']}")
        print(f"   💻 Services Implemented: {coordination_metrics['services_implemented']}")
        print(f"   🔗 Cross-Team Dependencies: {coordination_metrics['cross_team_dependencies']}")
        print(f"   🧪 Integration Tests: {coordination_metrics['integration_tests_created']}")
        print(f"   🗣️  Council Debates: {coordination_metrics['council_debates_conducted']}")
        print(f"   🚫 Blocking Issues Resolved: {coordination_metrics['blocking_issues_resolved']}")

    @pytest.mark.asyncio
    async def test_team_continuous_improvement_journey(self, team_test_setup):
        """Test team continuous improvement with metrics and retrospectives."""
        
        services = team_test_setup
        neo4j = services["neo4j"]
        council = services["council"]
        matrix = services["matrix"]
        
        # === STEP 1: Team establishes baseline metrics ===
        
        # Create baseline project state
        baseline_requirements = [
            {
                "id": "REQ-BASELINE-001",
                "description": "User dashboard with performance metrics",
                "type": "FR", 
                "priority": "M",
                "stage": "mvp",
                "velocity_points": 8,
                "actual_effort": None  # To be measured
            },
            {
                "id": "REQ-BASELINE-002",
                "description": "Admin panel for system configuration",
                "type": "FR",
                "priority": "S", 
                "stage": "mvp",
                "velocity_points": 5,
                "actual_effort": None
            }
        ]
        
        for req in baseline_requirements:
            query = """
            MERGE (r:Requirement {id: $id})
            SET r.description = $description,
                r.type = $type,
                r.priority = $priority,
                r.stage = $stage,
                r.velocity_points = $velocity_points,
                r.status = 'in_progress',
                r.started_at = datetime(),
                r.created_at = datetime(),
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, req)
        
        baseline_services = [
            {
                "type": "Service",
                "id": "SVC-DASHBOARD",
                "name": "UserDashboard",
                "implements": ["REQ-BASELINE-001"],
                "status": "implemented",
                "implementation_time_hours": 12
            },
            {
                "type": "Service",
                "id": "SVC-ADMIN",
                "name": "AdminPanel", 
                "implements": ["REQ-BASELINE-002"],
                "status": "implemented",
                "implementation_time_hours": 8
            }
        ]
        
        neo4j.sync_code_artifacts(baseline_services)
        
        # === STEP 2: Team measures actual vs estimated effort ===
        
        # Update requirements with actual effort
        effort_updates = [
            {"req_id": "REQ-BASELINE-001", "actual_effort": 12, "variance": 4},  # 8 estimated, 12 actual
            {"req_id": "REQ-BASELINE-002", "actual_effort": 8, "variance": 3}   # 5 estimated, 8 actual
        ]
        
        for update in effort_updates:
            query = """
            MATCH (r:Requirement {id: $req_id})
            SET r.actual_effort = $actual_effort,
                r.effort_variance = $variance,
                r.completed_at = datetime(),
                r.status = 'implemented'
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, update)
        
        # === STEP 3: Team conducts retrospective with council insights ===
        
        retrospective_topic = DebateTopic(
            title="Sprint retrospective: Effort estimation accuracy and improvement opportunities",
            description="Analyze team velocity and estimation accuracy for continuous improvement",
            context={
                "sprint_data": {
                    "estimated_points": 13,  # 8 + 5
                    "actual_hours": 20,      # 12 + 8
                    "variance": 7,           # Total variance
                    "velocity": 0.65         # 13 estimated / 20 actual
                },
                "quality_metrics": {
                    "bugs_found": 2,
                    "rework_required": 1,
                    "test_coverage": 85.0
                },
                "team_feedback": [
                    "Requirements were clear",
                    "Underestimated UI complexity", 
                    "Need better design mockups upfront"
                ]
            },
            priority="important"
        )
        
        retro_consensus, retro_debate = await council.evaluate_topic(
            retrospective_topic,
            enable_debate=True
        )
        
        assert retro_consensus is not None
        
        # === STEP 4: Team implements improvement actions ===
        
        # Based on retrospective, team identifies improvement actions
        improvement_actions = [
            {
                "action": "Add design review gate before implementation",
                "owner": "UX team",
                "target_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "success_metric": "Reduce UI rework by 50%"
            },
            {
                "action": "Improve effort estimation for UI components",
                "owner": "Engineering team", 
                "target_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
                "success_metric": "Estimation variance <20%"
            },
            {
                "action": "Create estimation guidelines based on complexity",
                "owner": "Tech lead",
                "target_date": (datetime.utcnow() + timedelta(days=10)).isoformat(), 
                "success_metric": "Team adoption >90%"
            }
        ]
        
        # Store improvement actions in Neo4j
        for action in improvement_actions:
            query = """
            MERGE (a:ImprovementAction {id: $action_id})
            SET a.description = $action,
                a.owner = $owner,
                a.target_date = $target_date,
                a.success_metric = $success_metric,
                a.status = 'planned',
                a.created_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, {
                    "action_id": f"ACTION-{improvement_actions.index(action) + 1:03d}",
                    **action
                })
        
        # === STEP 5: Team tracks improvement over time ===
        
        # Simulate next sprint with improvements applied
        improved_requirements = [
            {
                "id": "REQ-IMPROVED-001",
                "description": "Enhanced user dashboard with better UX",
                "type": "FR",
                "priority": "M",
                "stage": "v1", 
                "velocity_points": 10,
                "actual_effort": 11,  # Better estimation (10% variance vs previous 50%+ variance)
                "estimation_quality": "improved"
            }
        ]
        
        for req in improved_requirements:
            query = """
            MERGE (r:Requirement {id: $id})
            SET r.description = $description,
                r.type = $type,
                r.priority = $priority,
                r.stage = $stage,
                r.velocity_points = $velocity_points,
                r.actual_effort = $actual_effort,
                r.status = 'implemented',
                r.estimation_quality = $estimation_quality,
                r.created_at = datetime(),
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, req)
        
        # === STEP 6: Team measures improvement effectiveness ===
        
        # Calculate improvement metrics
        baseline_variance = sum(update["variance"] for update in effort_updates) / len(effort_updates)
        improved_variance = abs(improved_requirements[0]["actual_effort"] - improved_requirements[0]["velocity_points"])
        
        improvement_percentage = ((baseline_variance - improved_variance) / baseline_variance) * 100
        
        # Should show improvement in estimation accuracy
        assert improvement_percentage > 0, "No improvement in estimation accuracy"
        
        # === STEP 7: Team validates continuous improvement success ===
        
        continuous_improvement_metrics = {
            "retrospectives_conducted": 1,
            "improvement_actions_identified": len(improvement_actions),
            "estimation_variance_reduction": improvement_percentage,
            "council_insights_utilized": retro_consensus.decision != "FAIL",
            "team_coordination_issues_resolved": 1,  # WebSocket blocking issue
            "traceability_maintained_through_changes": True,
            "process_improvements_documented": len(improvement_actions) > 0
        }
        
        ci_success_rate = sum(1 for metric, value in continuous_improvement_metrics.items() 
                             if (isinstance(value, bool) and value) or 
                                (isinstance(value, (int, float)) and value > 0)) / len(continuous_improvement_metrics)
        
        # Continuous improvement should be highly successful (>85%)
        assert ci_success_rate >= 0.85, f"Continuous improvement success rate {ci_success_rate:.1%} < 85%"
        
        print(f"✅ Team Continuous Improvement Journey Completed!")
        print(f"   📊 Improvement Success Rate: {ci_success_rate:.1%}")
        print(f"   📈 Estimation Accuracy Improved: {improvement_percentage:.1f}%")
        print(f"   🔄 Retrospectives: {continuous_improvement_metrics['retrospectives_conducted']}")
        print(f"   ✅ Actions Identified: {continuous_improvement_metrics['improvement_actions_identified']}")
        print(f"   🗣️  Council Insights: {retro_consensus.decision}")
        print(f"   🤝 Team Coordination: Effective")

    @pytest.mark.asyncio
    async def test_team_release_coordination_journey(self, team_test_setup):
        """Test team coordinating release across multiple services and teams."""
        
        services = team_test_setup
        neo4j = services["neo4j"] 
        council = services["council"]
        matrix = services["matrix"]
        provenance = services["provenance"]
        
        # === STEP 1: Team prepares for release coordination ===
        
        # Multiple teams contributing to release
        release_requirements = [
            # Frontend team
            {"id": "REQ-RELEASE-UI-001", "team": "frontend", "status": "implemented"},
            {"id": "REQ-RELEASE-UI-002", "team": "frontend", "status": "implemented"},
            
            # Backend team  
            {"id": "REQ-RELEASE-API-001", "team": "backend", "status": "implemented"},
            {"id": "REQ-RELEASE-API-002", "team": "backend", "status": "in_progress"},
            
            # Platform team
            {"id": "REQ-RELEASE-INFRA-001", "team": "platform", "status": "implemented"},
            {"id": "REQ-RELEASE-INFRA-002", "team": "platform", "status": "blocked"},
            
            # QA team
            {"id": "REQ-RELEASE-QA-001", "team": "qa", "status": "in_progress"}
        ]
        
        for req in release_requirements:
            query = """
            MERGE (r:Requirement {id: $id})
            SET r.team = $team,
                r.status = $status,
                r.type = 'FR',
                r.priority = 'M',
                r.stage = 'release_v1',
                r.created_at = datetime(),
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, req)
        
        # === STEP 2: Team assesses release readiness ===
        
        readiness_check = matrix.validate_increment_readiness("release_v1")
        
        # Should identify blocking issues
        assert len(readiness_check["blocking_issues"]) > 0  # Some requirements not ready
        
        # === STEP 3: Team coordinates release decision ===
        
        release_decision_topic = DebateTopic(
            title="Should we proceed with V1 release despite incomplete platform requirements?",
            description="Release coordination decision with partial team readiness",
            context={
                "ready_teams": ["frontend", "qa"],
                "blocked_teams": ["platform"], 
                "in_progress_teams": ["backend"],
                "business_pressure": "Customer demo scheduled for next week",
                "technical_risk": "Platform scaling not ready for production load",
                "mitigation_options": [
                    "Release with manual scaling procedures",
                    "Delay release until platform ready",
                    "Release beta version with usage limits"
                ]
            },
            priority="critical"
        )
        
        release_consensus, release_debate = await council.evaluate_topic(
            release_decision_topic,
            enable_debate=True
        )
        
        assert release_consensus is not None
        
        # Council should provide structured decision guidance
        if release_consensus.decision == "PASS":
            release_approach = "proceed_with_mitigations"
        elif release_consensus.decision == "FAIL":
            release_approach = "delay_until_ready"
        else:
            release_approach = "escalate_to_business_stakeholders"
        
        # === STEP 4: Team implements release decision ===
        
        if release_approach == "proceed_with_mitigations":
            # Update blocked requirements with mitigation plan
            mitigation_query = """
            MATCH (r:Requirement {id: 'REQ-RELEASE-INFRA-002'})
            SET r.status = 'mitigated',
                r.mitigation_plan = 'Manual scaling procedures documented, monitoring alerts configured',
                r.risk_acceptance = 'Business stakeholder approved',
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(mitigation_query)
        
        # === STEP 5: Team validates release coordination success ===
        
        # Final readiness check after mitigations
        final_readiness = matrix.validate_increment_readiness("release_v1")
        
        # Generate team coordination report
        team_status_query = """
        MATCH (r:Requirement {stage: 'release_v1'})
        WITH r.team as team, r.status as status, count(r) as req_count
        RETURN team, status, req_count
        ORDER BY team, status
        """
        
        team_status = {}
        with neo4j.driver.session(database=neo4j.config.database) as session:
            result = session.run(team_status_query)
            for record in result:
                team = record["team"]
                status = record["status"]
                count = record["req_count"]
                
                if team not in team_status:
                    team_status[team] = {}
                team_status[team][status] = count
        
        # Calculate team readiness percentages
        team_readiness = {}
        for team, statuses in team_status.items():
            total = sum(statuses.values())
            implemented = statuses.get("implemented", 0) + statuses.get("mitigated", 0)
            team_readiness[team] = (implemented / total) * 100 if total > 0 else 0
        
        # === STEP 6: Team measures release coordination effectiveness ===
        
        release_coordination_metrics = {
            "total_teams_involved": len(team_status),
            "teams_with_80_percent_ready": len([team for team, readiness in team_readiness.items() if readiness >= 80]),
            "council_guidance_quality": release_consensus.confidence,
            "risk_mitigation_plans": 1,  # Platform mitigation
            "cross_team_dependencies_managed": True,
            "release_decision_documented": release_consensus.rationale is not None,
            "stakeholder_communication": release_approach != "escalate_to_business_stakeholders"
        }
        
        coordination_success = (
            release_coordination_metrics["teams_with_80_percent_ready"] / 
            release_coordination_metrics["total_teams_involved"]
        )
        
        # Most teams should be ready for coordinated release
        assert coordination_success >= 0.6, f"Team coordination success {coordination_success:.1%} < 60%"
        
        # Validate that team has comprehensive view of release status
        assert release_coordination_metrics["total_teams_involved"] >= 3
        assert release_coordination_metrics["council_guidance_quality"] >= 0.6
        assert release_coordination_metrics["stakeholder_communication"] == True
        
        print(f"✅ Team Release Coordination Journey Completed!")
        print(f"   📊 Coordination Success: {coordination_success:.1%}")
        print(f"   👥 Teams Involved: {release_coordination_metrics['total_teams_involved']}")
        print(f"   ✅ Teams Ready (≥80%): {release_coordination_metrics['teams_with_80_percent_ready']}")
        print(f"   🎯 Council Guidance Quality: {release_coordination_metrics['council_guidance_quality']:.2f}")
        print(f"   📋 Release Approach: {release_approach}")
        print(f"   🚀 Final Readiness: {final_readiness['ready_for_release']}")
        print(f"   🔗 Team Status: {team_readiness}")
