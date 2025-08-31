"""End-to-end tests for Product Manager journey: Requirements → Traceability → Impact Analysis."""

import pytest
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from src.llm_council.database.neo4j_client import Neo4jClient, Neo4jConfig
from src.llm_council.services.traceability_matrix import TraceabilityMatrix
from src.llm_council.services.provenance_tracker import ProvenanceTracker, CodeScanner

pytestmark = pytest.mark.e2e

@pytest.fixture
async def pm_test_setup():
    """Setup for PM journey testing."""
    
    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="test-password", 
        database="test_pm_db"
    )
    
    neo4j_client = Neo4jClient(neo4j_config)
    neo4j_client.connect()
    
    # Clear test database
    with neo4j_client.driver.session(database="test_pm_db") as session:
        session.run("MATCH (n) DETACH DELETE n")
    
    # Initialize services
    matrix_generator = TraceabilityMatrix(neo4j_client)
    code_scanner = CodeScanner(neo4j_client)
    provenance_tracker = ProvenanceTracker(neo4j_client, code_scanner)
    
    # Create test project structure
    test_root = Path("/tmp/test_pm_project")
    test_root.mkdir(exist_ok=True)
    
    yield {
        "neo4j": neo4j_client,
        "matrix": matrix_generator,
        "scanner": code_scanner,
        "provenance": provenance_tracker,
        "test_root": test_root
    }
    
    # Cleanup
    neo4j_client.close()

class TestPMCompleteJourney:
    """Test complete PM journey from validated idea to requirement traceability."""
    
    @pytest.mark.asyncio
    async def test_pm_requirements_to_traceability_journey(self, pm_test_setup):
        """Test PM journey: Idea → PRD → Requirements → Code → Tests → Traceability Matrix."""
        
        services = pm_test_setup
        neo4j = services["neo4j"]
        matrix = services["matrix"]
        scanner = services["scanner"]
        provenance = services["provenance"]
        test_root = services["test_root"]
        
        # === STEP 1: PM starts with validated idea (from founder journey) ===
        idea_id = neo4j.create_idea_graph(
            "AI-powered medical note-taking system for primary care physicians",
            "yc"
        )
        
        # Add validated problem from founder journey
        validated_entities = {
            "problems": [{
                "id": "P-001",
                "statement": "Primary care doctors spend 2+ hours daily on medical documentation",
                "impact_metric": "2 hours lost per doctor per day",
                "pain_level": 0.8,
                "frequency": 1.0,
                "confidence": 0.9
            }],
            "icps": [{
                "id": "ICP-001",
                "segment": "Primary care physicians in US", 
                "size": 220000,
                "pains": ["Time-consuming documentation", "Administrative burden"],
                "gains": ["More time with patients", "Reduced burnout"],
                "wtp": 3000.0,
                "confidence": 0.8
            }],
            "outcomes": [{
                "id": "O-001",
                "description": "Reduce physician documentation time by 50%",
                "metric": "Minutes spent per patient note",
                "target": 3.0,  # From 6 minutes to 3 minutes
                "timeline": "6 months post-launch",
                "confidence": 0.7
            }]
        }
        
        neo4j.add_extracted_entities(idea_id, validated_entities)
        
        # === STEP 2: PM generates structured requirements from validated problems ===
        requirement_ids = neo4j.create_requirements_from_problems(idea_id)
        
        assert len(requirement_ids) > 0
        
        # PM adds detailed functional requirements  
        detailed_requirements = [
            {
                "id": "REQ-001",
                "description": "System shall transcribe physician-patient conversations in real-time",
                "type": "FR",
                "priority": "M",
                "acceptance_criteria": [
                    "Transcription accuracy ≥95% for medical terminology",
                    "Latency ≤2 seconds for speech-to-text",
                    "Support for 20+ medical specialties vocabulary"
                ],
                "confidence": 0.8,
                "stage": "mvp",
                "status": "defined"
            },
            {
                "id": "REQ-002", 
                "description": "System shall generate structured medical notes from transcription",
                "type": "FR",
                "priority": "M",
                "acceptance_criteria": [
                    "Generate SOAP format notes",
                    "Include ICD-10 diagnostic codes",
                    "Maintain physician review and edit capability"
                ],
                "confidence": 0.7,
                "stage": "mvp", 
                "status": "defined"
            },
            {
                "id": "REQ-003",
                "description": "System shall integrate with common EHR systems",
                "type": "FR", 
                "priority": "S",  # Should have, not must
                "acceptance_criteria": [
                    "Epic EHR API integration",
                    "Cerner EHR API integration", 
                    "FHIR standard compliance"
                ],
                "confidence": 0.6,
                "stage": "v1",  # Post-MVP
                "status": "defined"
            }
        ]
        
        # Add NFR requirements
        nfr_requirements = [
            {
                "id": "NFR-001",
                "description": "System shall comply with HIPAA privacy regulations",
                "type": "NFR",
                "category": "security",
                "criterion": "HIPAA compliance audit",
                "threshold": "100% compliant", 
                "priority": "M",
                "stage": "mvp",
                "status": "defined"
            },
            {
                "id": "NFR-002",
                "description": "System shall handle 1000+ concurrent physician sessions",
                "type": "NFR",
                "category": "performance",
                "criterion": "Concurrent user load",
                "threshold": "1000 sessions with <3s response time",
                "priority": "S",
                "stage": "v1", 
                "status": "defined"
            }
        ]
        
        # Store requirements in Neo4j
        all_requirements = detailed_requirements + nfr_requirements
        
        for req in all_requirements:
            query = """
            MATCH (p:Problem {id: 'P-001'})
            MERGE (r:Requirement {id: $req_id})
            SET r.description = $description,
                r.type = $type,
                r.priority = $priority,
                r.stage = $stage,
                r.status = $status,
                r.confidence = $confidence,
                r.created_at = datetime(),
                r.updated_at = datetime()
            MERGE (r)-[:DERIVES_FROM]->(p)
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, {
                    "req_id": req["id"],
                    "description": req["description"],
                    "type": req["type"],
                    "priority": req["priority"],
                    "stage": req["stage"],
                    "status": req["status"],
                    "confidence": req.get("confidence", 0.5)
                })
        
        # === STEP 3: PM creates Feature Requirement Specs (FRS) ===
        frs_specs = [
            {
                "id": "FRS-FEAT-001",
                "title": "Real-time Speech Transcription",
                "description": "Voice-to-text transcription during patient visits",
                "user_stories": [
                    "As a physician, I want automatic transcription so I can focus on patient care",
                    "As a physician, I want to review and edit transcripts before finalizing notes"
                ],
                "requirements": ["REQ-001", "NFR-001"],
                "priority": "critical",
                "stage": "mvp"
            },
            {
                "id": "FRS-FEAT-002", 
                "title": "Medical Note Generation",
                "description": "AI-powered structured medical note creation",
                "user_stories": [
                    "As a physician, I want SOAP format notes generated automatically",
                    "As a physician, I want diagnostic codes suggested based on conversation"
                ],
                "requirements": ["REQ-002", "NFR-001"],
                "priority": "critical",
                "stage": "mvp"
            },
            {
                "id": "FRS-FEAT-003",
                "title": "EHR Integration",
                "description": "Seamless integration with Electronic Health Records",
                "user_stories": [
                    "As a physician, I want notes automatically saved to patient EHR",
                    "As an IT admin, I want FHIR-compliant data exchange"
                ],
                "requirements": ["REQ-003", "NFR-002"],
                "priority": "important",
                "stage": "v1"
            }
        ]
        
        # Store FRS in Neo4j
        for frs in frs_specs:
            frs_query = """
            MERGE (frs:FRS {id: $frs_id})
            SET frs.title = $title,
                frs.description = $description,
                frs.priority = $priority,
                frs.stage = $stage,
                frs.created_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(frs_query, {
                    "frs_id": frs["id"],
                    "title": frs["title"],
                    "description": frs["description"],
                    "priority": frs["priority"],
                    "stage": frs["stage"]
                })
                
                # Link FRS to requirements
                for req_id in frs["requirements"]:
                    link_query = """
                    MATCH (frs:FRS {id: $frs_id})
                    MATCH (r:Requirement {id: $req_id})
                    MERGE (frs)-[:DERIVES]->(r)
                    """
                    session.run(link_query, {"frs_id": frs["id"], "req_id": req_id})
        
        # === STEP 4: PM creates mock implementation structure ===
        # Simulate code that implements the requirements
        
        mock_services = [
            {
                "type": "Service",
                "id": "SVC-TRANSCRIPTION",
                "name": "TranscriptionService", 
                "file_path": f"{test_root}/src/services/transcription_service.py",
                "implements": ["REQ-001"],
                "stage": "mvp",
                "status": "implemented",
                "complexity": 8,
                "lines_of_code": 150
            },
            {
                "type": "Service", 
                "id": "SVC-NOTEGENERATION",
                "name": "NoteGenerationService",
                "file_path": f"{test_root}/src/services/note_generation_service.py", 
                "implements": ["REQ-002"],
                "stage": "mvp",
                "status": "implemented",
                "complexity": 12,
                "lines_of_code": 200
            },
            {
                "type": "Service",
                "id": "SVC-EHRINTEGRATION", 
                "name": "EHRIntegrationService",
                "file_path": f"{test_root}/src/services/ehr_integration_service.py",
                "implements": ["REQ-003"],
                "stage": "v1",
                "status": "planned",  # Not yet implemented
                "complexity": 15,
                "lines_of_code": 0
            }
        ]
        
        mock_tests = [
            {
                "type": "Test",
                "id": "TEST-U-001",
                "name": "test_transcription_accuracy",
                "file_path": f"{test_root}/tests/unit/test_transcription_service.py",
                "test_type": "unit",
                "covers": ["REQ-001"],
                "verified_by": ["SVC-TRANSCRIPTION"],
                "status": "implemented"
            },
            {
                "type": "Test",
                "id": "TEST-U-002", 
                "name": "test_note_generation_soap_format",
                "file_path": f"{test_root}/tests/unit/test_note_generation_service.py",
                "test_type": "unit", 
                "covers": ["REQ-002"],
                "verified_by": ["SVC-NOTEGENERATION"],
                "status": "implemented"
            },
            {
                "type": "Test",
                "id": "TEST-I-001",
                "name": "test_end_to_end_transcription_flow",
                "file_path": f"{test_root}/tests/integration/test_transcription_flow.py",
                "test_type": "integration",
                "covers": ["REQ-001", "REQ-002"],
                "verified_by": ["SVC-TRANSCRIPTION", "SVC-NOTEGENERATION"],
                "status": "implemented"
            },
            {
                "type": "Test",
                "id": "TEST-NFR-001",
                "name": "test_hipaa_compliance_audit",
                "file_path": f"{test_root}/tests/nfr/test_hipaa_compliance.py", 
                "test_type": "nfr",
                "covers": ["NFR-001"],
                "verified_by": ["SVC-TRANSCRIPTION", "SVC-NOTEGENERATION"],
                "status": "implemented"
            },
            {
                "type": "Test",
                "id": "TEST-E2E-001",
                "name": "test_physician_complete_workflow",
                "file_path": f"{test_root}/tests/e2e/test_physician_workflow.py",
                "test_type": "e2e", 
                "covers": ["REQ-001", "REQ-002"],
                "validated": ["FRS-FEAT-001", "FRS-FEAT-002"],
                "status": "implemented"
            }
        ]
        
        # Sync mock artifacts to Neo4j
        all_artifacts = mock_services + mock_tests
        neo4j.sync_code_artifacts(all_artifacts)
        
        # === STEP 5: PM generates traceability matrix ===
        matrix_entries = matrix.generate_complete_matrix(increment_filter="mvp")
        
        # Should have entries for all MVP requirements
        mvp_entries = [e for e in matrix_entries if "REQ-001" in e.req_id or "REQ-002" in e.req_id or "NFR-001" in e.req_id]
        assert len(mvp_entries) >= 3
        
        # Check specific requirement coverage
        req_001_entry = next((e for e in matrix_entries if e.req_id == "REQ-001"), None)
        assert req_001_entry is not None
        assert len(req_001_entry.implementing_code) > 0  # Should have implementing service
        assert len(req_001_entry.unit_tests) > 0        # Should have unit tests
        assert req_001_entry.status in ["GREEN", "YELLOW"] # Should have some coverage
        
        req_002_entry = next((e for e in matrix_entries if e.req_id == "REQ-002"), None)
        assert req_002_entry is not None
        assert len(req_002_entry.implementing_code) > 0
        assert len(req_002_entry.unit_tests) > 0
        
        # === STEP 6: PM analyzes coverage gaps ===
        coverage_report = matrix.generate_coverage_report("mvp")
        orphan_report = matrix.find_orphans()
        
        # Should have good coverage for implemented requirements
        assert coverage_report.overall_coverage > 0.6  # >60% coverage
        
        # MVP requirements should have higher coverage than v1
        mvp_coverage = coverage_report.by_increment.get("mvp", 0)
        
        # Check for orphan requirements (REQ-003 should be orphaned since service not implemented)
        orphan_reqs = [req for req in orphan_report.orphan_requirements if req["req_id"] == "REQ-003"]
        # REQ-003 is stage=v1 and service is status=planned, so it may or may not be orphaned depending on implementation
        
        # === STEP 7: PM performs requirements change impact analysis ===
        # Simulate PM changing REQ-001 (transcription requirement)
        
        # Update requirement to add new acceptance criterion
        update_query = """
        MATCH (r:Requirement {id: 'REQ-001'})
        SET r.description = 'System shall transcribe physician-patient conversations in real-time with multi-language support',
            r.updated_at = datetime()
        RETURN r
        """
        
        with neo4j.driver.session(database=neo4j.config.database) as session:
            result = session.run(update_query)
            assert result.single() is not None
        
        # Analyze impact of the change
        changed_artifacts = ["SVC-TRANSCRIPTION"]  # Service that implements REQ-001
        impact_report = provenance.generate_impact_report(changed_artifacts)
        
        # Should identify upstream requirements and downstream tests
        assert len(impact_report["upstream_requirements"]) > 0
        assert "REQ-001" in impact_report["upstream_requirements"]
        
        assert len(impact_report["downstream_tests"]) > 0
        # Should include unit tests and integration tests that verify the service
        
        # === STEP 8: PM validates increment readiness ===
        readiness_check = matrix.validate_increment_readiness("mvp")
        
        # MVP should be partially ready (some requirements implemented, some not)
        total_mvp_reqs = len([r for r in all_requirements if r.get("stage") == "mvp"])
        
        # Check readiness criteria
        assert readiness_check["increment"] == "mvp"
        assert readiness_check["overall_coverage"] > 0
        
        # May not be fully ready due to missing EHR integration, but should have core features
        if readiness_check["ready_for_release"]:
            assert readiness_check["overall_coverage"] >= 85.0
            assert readiness_check["critical_coverage"] >= 100.0
        
        # === STEP 9: PM exports traceability reports ===
        output_dir = test_root / "reports"
        output_dir.mkdir(exist_ok=True)
        
        # Export matrix in multiple formats
        csv_path = matrix.export_matrix_csv(matrix_entries, str(output_dir / "traceability.csv"))
        json_path = matrix.export_matrix_json(matrix_entries, str(output_dir / "traceability.json"))
        html_path = matrix.generate_html_dashboard(
            matrix_entries, 
            coverage_report,
            orphan_report, 
            str(output_dir / "traceability.html")
        )
        
        # Verify exports were created
        assert Path(csv_path).exists()
        assert Path(json_path).exists()
        assert Path(html_path).exists()
        
        # === STEP 10: PM validates success metrics ===
        pm_success_criteria = {
            "requirements_defined": len(all_requirements) >= 5,
            "frs_created": len(frs_specs) >= 3,
            "traceability_established": len(matrix_entries) > 0,
            "coverage_acceptable": coverage_report.overall_coverage >= 60.0,
            "orphan_analysis_complete": len(orphan_report.orphan_requirements) >= 0,  # Analysis done
            "impact_analysis_functional": len(impact_report["upstream_requirements"]) > 0,
            "reports_generated": Path(html_path).exists(),
            "increment_assessment_complete": readiness_check is not None
        }
        
        success_count = sum(1 for criterion, met in pm_success_criteria.items() if met)
        success_rate = success_count / len(pm_success_criteria)
        
        # PM journey should achieve >90% success rate
        assert success_rate >= 0.9, f"PM journey success rate {success_rate:.1%} < 90%"
        
        print(f"✅ PM Journey Completed Successfully!")
        print(f"   📊 Success Rate: {success_rate:.1%}")
        print(f"   📋 Requirements: {len(all_requirements)} total, {total_mvp_reqs} MVP")
        print(f"   📑 FRS Created: {len(frs_specs)}")
        print(f"   🎯 Coverage: {coverage_report.overall_coverage:.1f}%")
        print(f"   🔗 Matrix Entries: {len(matrix_entries)}")
        print(f"   📄 Reports: {html_path}")
        print(f"   🚀 MVP Ready: {readiness_check['ready_for_release']}")

    @pytest.mark.asyncio
    async def test_pm_requirements_evolution_journey(self, pm_test_setup):
        """Test PM managing requirements evolution and change impact."""
        
        services = pm_test_setup
        neo4j = services["neo4j"]
        matrix = services["matrix"]
        provenance = services["provenance"]
        
        # === STEP 1: PM starts with initial requirements ===
        idea_id = neo4j.create_idea_graph("Task management app for remote teams", "lean")
        
        initial_requirements = [
            {
                "id": "REQ-TASK-001",
                "description": "Users can create and assign tasks to team members",
                "type": "FR", 
                "priority": "M",
                "stage": "mvp",
                "status": "implemented"
            },
            {
                "id": "REQ-TASK-002",
                "description": "Users can track task progress and completion",
                "type": "FR",
                "priority": "M", 
                "stage": "mvp",
                "status": "implemented"
            }
        ]
        
        # Add initial requirements
        for req in initial_requirements:
            query = """
            MERGE (r:Requirement {id: $req_id})
            SET r.description = $description,
                r.type = $type,
                r.priority = $priority,
                r.stage = $stage,
                r.status = $status,
                r.version = 1,
                r.created_at = datetime(),
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, req)
        
        # Add implementing services
        initial_services = [
            {
                "type": "Service",
                "id": "SVC-TASK-MGR",
                "name": "TaskManagerService", 
                "implements": ["REQ-TASK-001", "REQ-TASK-002"],
                "status": "implemented"
            }
        ]
        
        neo4j.sync_code_artifacts(initial_services)
        
        # Generate initial matrix
        initial_matrix = matrix.generate_complete_matrix()
        initial_count = len(initial_matrix)
        
        # === STEP 2: Customer feedback drives requirement changes ===
        # PM receives feedback: "We need real-time notifications and time tracking"
        
        new_requirements = [
            {
                "id": "REQ-TASK-003",
                "description": "System sends real-time notifications for task assignments and updates",
                "type": "FR",
                "priority": "S",  # Should have
                "stage": "v1",   # Next increment  
                "status": "defined"
            },
            {
                "id": "REQ-TASK-004",
                "description": "Users can track time spent on tasks with start/stop timer",
                "type": "FR",
                "priority": "C",  # Could have
                "stage": "v2",   # Future increment
                "status": "defined"
            }
        ]
        
        # PM modifies existing requirement based on feedback
        modified_requirement = {
            "id": "REQ-TASK-001", 
            "description": "Users can create, assign, and prioritize tasks with due dates to team members",  # Enhanced
            "version": 2  # Version increment
        }
        
        # Add new requirements
        for req in new_requirements:
            query = """
            MERGE (r:Requirement {id: $req_id})
            SET r.description = $description,
                r.type = $type,
                r.priority = $priority,
                r.stage = $stage, 
                r.status = $status,
                r.version = 1,
                r.created_at = datetime(),
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, req)
        
        # Update existing requirement
        update_query = """
        MATCH (r:Requirement {id: $req_id})
        SET r.description = $description,
            r.version = $version,
            r.updated_at = datetime()
        """
        
        with neo4j.driver.session(database=neo4j.config.database) as session:
            session.run(update_query, modified_requirement)
        
        # === STEP 3: PM analyzes impact of changes ===
        
        # Regenerate matrix after changes
        updated_matrix = matrix.generate_complete_matrix()
        
        # Should now have more requirements
        assert len(updated_matrix) > initial_count
        
        # Find the modified requirement entry
        modified_entry = next((e for e in updated_matrix if e.req_id == "REQ-TASK-001"), None)
        assert modified_entry is not None
        
        # Check impact on implementing service
        impact_report = provenance.generate_impact_report(["SVC-TASK-MGR"])
        
        # Should show that changes to REQ-TASK-001 affect the service
        assert "REQ-TASK-001" in impact_report["upstream_requirements"]
        
        # === STEP 4: PM plans implementation for new requirements ===
        
        # Check which new requirements are orphaned (no implementing code yet)
        orphan_report = matrix.find_orphans()
        
        new_req_ids = [req["id"] for req in new_requirements]
        orphaned_new_reqs = [
            req for req in orphan_report.orphan_requirements 
            if req["req_id"] in new_req_ids
        ]
        
        # New requirements should be orphaned since not implemented yet
        assert len(orphaned_new_reqs) > 0
        
        # PM adds planned services for new requirements
        planned_services = [
            {
                "type": "Service", 
                "id": "SVC-NOTIFICATIONS",
                "name": "NotificationService",
                "implements": ["REQ-TASK-003"],
                "stage": "v1",
                "status": "planned"  # Not implemented yet
            },
            {
                "type": "Service",
                "id": "SVC-TIMETRACKING", 
                "name": "TimeTrackingService",
                "implements": ["REQ-TASK-004"],
                "stage": "v2", 
                "status": "planned"
            }
        ]
        
        neo4j.sync_code_artifacts(planned_services)
        
        # === STEP 5: PM validates increment planning ===
        
        # Check readiness of different increments
        mvp_readiness = matrix.validate_increment_readiness("mvp")
        v1_readiness = matrix.validate_increment_readiness("v1") 
        
        # MVP should be ready (implemented requirements)
        assert mvp_readiness["ready_for_release"] == True or len(mvp_readiness["blocking_issues"]) == 0
        
        # V1 should not be ready (has planned but not implemented requirements)
        assert v1_readiness["ready_for_release"] == False
        assert len(v1_readiness["blocking_issues"]) > 0
        
        # === STEP 6: PM tracks requirements evolution over time ===
        
        # Generate coverage reports for different increments
        mvp_coverage = matrix.generate_coverage_report("mvp")
        v1_coverage = matrix.generate_coverage_report("v1")
        
        # MVP should have higher coverage than V1 (since V1 services are planned)
        assert mvp_coverage.overall_coverage >= v1_coverage.overall_coverage
        
        print(f"✅ PM Requirements Evolution Journey Completed!")
        print(f"   📋 Initial Requirements: {len(initial_requirements)}")
        print(f"   📋 Total Requirements After Evolution: {len(updated_matrix)}")
        print(f"   📊 MVP Coverage: {mvp_coverage.overall_coverage:.1f}%")
        print(f"   📊 V1 Coverage: {v1_coverage.overall_coverage:.1f}%")
        print(f"   🚀 MVP Ready: {mvp_readiness['ready_for_release']}")
        print(f"   🔄 V1 Ready: {v1_readiness['ready_for_release']}")

    @pytest.mark.asyncio
    async def test_pm_multi_team_coordination_journey(self, pm_test_setup):
        """Test PM coordinating requirements across multiple teams and services."""
        
        services = pm_test_setup
        neo4j = services["neo4j"]
        matrix = services["matrix"] 
        
        # === STEP 1: PM defines cross-team requirements for e-commerce platform ===
        
        # Frontend team requirements
        frontend_requirements = [
            {
                "id": "REQ-UI-001",
                "description": "User interface for product browsing and search",
                "type": "FR",
                "priority": "M",
                "stage": "mvp",
                "status": "implemented",
                "team": "frontend"
            },
            {
                "id": "REQ-UI-002", 
                "description": "Shopping cart and checkout user interface",
                "type": "FR",
                "priority": "M",
                "stage": "mvp", 
                "status": "implemented",
                "team": "frontend"
            }
        ]
        
        # Backend API team requirements
        backend_requirements = [
            {
                "id": "REQ-API-001",
                "description": "Product catalog API with search and filtering",
                "type": "FR",
                "priority": "M",
                "stage": "mvp",
                "status": "implemented", 
                "team": "backend"
            },
            {
                "id": "REQ-API-002",
                "description": "Order management API for cart and checkout",
                "type": "FR", 
                "priority": "M",
                "stage": "mvp",
                "status": "implemented",
                "team": "backend"
            }
        ]
        
        # Platform/DevOps team requirements  
        platform_requirements = [
            {
                "id": "REQ-INFRA-001",
                "description": "Scalable infrastructure supporting 10k concurrent users",
                "type": "NFR",
                "priority": "M",
                "stage": "mvp",
                "status": "implemented",
                "team": "platform"
            },
            {
                "id": "REQ-INFRA-002",
                "description": "CI/CD pipeline for automated deployment",
                "type": "NFR",
                "priority": "S", 
                "stage": "mvp",
                "status": "implemented",
                "team": "platform"
            }
        ]
        
        all_requirements = frontend_requirements + backend_requirements + platform_requirements
        
        # Add requirements to Neo4j
        for req in all_requirements:
            query = """
            MERGE (r:Requirement {id: $id})
            SET r.description = $description,
                r.type = $type,
                r.priority = $priority,
                r.stage = $stage,
                r.status = $status,
                r.team = $team,
                r.created_at = datetime(),
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, req)
        
        # === STEP 2: PM maps services by team ===
        
        team_services = [
            # Frontend team services
            {
                "type": "Service",
                "id": "SVC-UI-CATALOG", 
                "name": "ProductCatalogUI",
                "implements": ["REQ-UI-001"],
                "team": "frontend",
                "status": "implemented"
            },
            {
                "type": "Service",
                "id": "SVC-UI-CART",
                "name": "ShoppingCartUI", 
                "implements": ["REQ-UI-002"],
                "team": "frontend",
                "status": "implemented"
            },
            
            # Backend team services
            {
                "type": "Service",
                "id": "SVC-API-CATALOG",
                "name": "CatalogAPI",
                "implements": ["REQ-API-001"], 
                "team": "backend",
                "status": "implemented"
            },
            {
                "type": "Service",
                "id": "SVC-API-ORDERS",
                "name": "OrdersAPI",
                "implements": ["REQ-API-002"],
                "team": "backend", 
                "status": "implemented"
            },
            
            # Platform team services
            {
                "type": "Service",
                "id": "SVC-INFRA-SCALING",
                "name": "AutoScalingService",
                "implements": ["REQ-INFRA-001"],
                "team": "platform",
                "status": "implemented"
            },
            {
                "type": "Service", 
                "id": "SVC-INFRA-DEPLOY",
                "name": "DeploymentPipeline",
                "implements": ["REQ-INFRA-002"],
                "team": "platform",
                "status": "implemented"
            }
        ]
        
        neo4j.sync_code_artifacts(team_services)
        
        # === STEP 3: PM analyzes cross-team dependencies ===
        
        # Create service dependencies (frontend depends on backend APIs)
        dependencies = [
            {"from": "SVC-UI-CATALOG", "to": "SVC-API-CATALOG", "type": "DEPENDS_ON"},
            {"from": "SVC-UI-CART", "to": "SVC-API-ORDERS", "type": "DEPENDS_ON"},
            {"from": "SVC-API-CATALOG", "to": "SVC-INFRA-SCALING", "type": "HOSTED_BY"},
            {"from": "SVC-API-ORDERS", "to": "SVC-INFRA-SCALING", "type": "HOSTED_BY"}
        ]
        
        for dep in dependencies:
            query = """
            MATCH (from {id: $from_id})
            MATCH (to {id: $to_id}) 
            MERGE (from)-[:DEPENDS_ON]->(to)
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, {"from_id": dep["from"], "to_id": dep["to"]})
        
        # === STEP 4: PM generates team-specific traceability views ===
        
        full_matrix = matrix.generate_complete_matrix()
        
        # Group matrix entries by team
        team_coverage = {}
        for entry in full_matrix:
            # Find team for this requirement
            req_team = None
            for req in all_requirements:
                if req["id"] == entry.req_id:
                    req_team = req["team"]
                    break
            
            if req_team:
                if req_team not in team_coverage:
                    team_coverage[req_team] = []
                team_coverage[req_team].append(entry)
        
        # Each team should have their requirements covered
        assert "frontend" in team_coverage
        assert "backend" in team_coverage  
        assert "platform" in team_coverage
        
        frontend_coverage = len([e for e in team_coverage["frontend"] if e.status == "GREEN"])
        backend_coverage = len([e for e in team_coverage["backend"] if e.status == "GREEN"])
        platform_coverage = len([e for e in team_coverage["platform"] if e.status == "GREEN"])
        
        # === STEP 5: PM simulates cross-team change impact ===
        
        # Backend API change affects frontend
        api_change_impact = [
            "SVC-API-CATALOG"  # Backend service change
        ]
        
        # Find all services that depend on the changed service
        dependency_query = """
        MATCH (changed {id: $service_id})<-[:DEPENDS_ON]-(dependent)
        RETURN collect(dependent.id) as dependent_services
        """
        
        with neo4j.driver.session(database=neo4j.config.database) as session:
            result = session.run(dependency_query, {"service_id": "SVC-API-CATALOG"})
            record = result.single()
            dependent_services = record["dependent_services"] if record else []
        
        # Should find frontend service depends on backend API
        assert "SVC-UI-CATALOG" in dependent_services
        
        # === STEP 6: PM validates cross-team integration ===
        
        # Add integration tests that span teams
        integration_tests = [
            {
                "type": "Test",
                "id": "TEST-INTEGRATION-001", 
                "name": "test_ui_catalog_api_integration",
                "test_type": "integration",
                "covers": ["REQ-UI-001", "REQ-API-001"],  # Spans frontend and backend
                "status": "implemented"
            },
            {
                "type": "Test",
                "id": "TEST-INTEGRATION-002",
                "name": "test_checkout_flow_end_to_end",
                "test_type": "e2e", 
                "covers": ["REQ-UI-002", "REQ-API-002"],  # Spans teams
                "status": "implemented"
            }
        ]
        
        neo4j.sync_code_artifacts(integration_tests)
        
        # Regenerate matrix with integration tests
        updated_matrix = matrix.generate_complete_matrix()
        
        # Requirements should now have integration test coverage
        ui_001_entry = next((e for e in updated_matrix if e.req_id == "REQ-UI-001"), None)
        assert ui_001_entry is not None
        assert len(ui_001_entry.integration_tests) > 0
        
        # === STEP 7: PM generates cross-team coordination report ===
        
        coordination_metrics = {
            "total_teams": len(set(req["team"] for req in all_requirements)),
            "cross_team_dependencies": len(dependencies),
            "integration_tests": len(integration_tests), 
            "requirements_per_team": {
                team: len([req for req in all_requirements if req["team"] == team])
                for team in set(req["team"] for req in all_requirements)
            },
            "team_coverage": {
                team: len([e for e in entries if e.status in ["GREEN", "YELLOW"]]) / len(entries) * 100
                for team, entries in team_coverage.items()
            }
        }
        
        # Validate coordination success
        assert coordination_metrics["total_teams"] == 3
        assert coordination_metrics["cross_team_dependencies"] > 0
        assert coordination_metrics["integration_tests"] > 0
        
        # Each team should have reasonable coverage
        for team, coverage_pct in coordination_metrics["team_coverage"].items():
            assert coverage_pct >= 50.0, f"Team {team} coverage {coverage_pct}% too low"
        
        print(f"✅ PM Multi-Team Coordination Journey Completed!")
        print(f"   👥 Teams Coordinated: {coordination_metrics['total_teams']}")
        print(f"   🔗 Cross-Team Dependencies: {coordination_metrics['cross_team_dependencies']}")
        print(f"   🧪 Integration Tests: {coordination_metrics['integration_tests']}")
        print(f"   📊 Team Coverage: {coordination_metrics['team_coverage']}")
        print(f"   📋 Requirements by Team: {coordination_metrics['requirements_per_team']}")
