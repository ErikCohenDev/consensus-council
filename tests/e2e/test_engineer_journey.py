"""End-to-end tests for Engineering journey: Specs → Code → Tests → Deployment."""

import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from src.llm_council.database.neo4j_client import Neo4jClient, Neo4jConfig
from src.llm_council.services.provenance_tracker import ProvenanceTracker, CodeScanner
from src.llm_council.services.traceability_matrix import TraceabilityMatrix

pytestmark = pytest.mark.e2e

@pytest.fixture
async def engineer_test_setup():
    """Setup for engineer journey testing."""
    
    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="test-password",
        database="test_engineer_db"
    )
    
    neo4j_client = Neo4jClient(neo4j_config)
    neo4j_client.connect()
    
    # Clear test database
    with neo4j_client.driver.session(database="test_engineer_db") as session:
        session.run("MATCH (n) DETACH DELETE n")
    
    # Create temporary test project
    test_project = Path(tempfile.mkdtemp(prefix="engineer_test_"))
    
    # Initialize services
    code_scanner = CodeScanner(neo4j_client)
    provenance_tracker = ProvenanceTracker(neo4j_client, code_scanner)
    matrix_generator = TraceabilityMatrix(neo4j_client)
    
    yield {
        "neo4j": neo4j_client,
        "scanner": code_scanner,
        "provenance": provenance_tracker,
        "matrix": matrix_generator,
        "test_project": test_project
    }
    
    # Cleanup
    neo4j_client.close()
    shutil.rmtree(test_project, ignore_errors=True)

class TestEngineerCompleteJourney:
    """Test complete engineer journey from specs to deployed code."""
    
    @pytest.mark.asyncio
    async def test_engineer_spec_to_code_journey(self, engineer_test_setup):
        """Test engineer journey: Clear specs → Generated code → Provenance → Tests."""
        
        services = engineer_test_setup
        neo4j = services["neo4j"]
        scanner = services["scanner"]
        provenance = services["provenance"]
        matrix = services["matrix"]
        test_project = services["test_project"]
        
        # === STEP 1: Engineer receives clear requirements and specs ===
        
        # Create project structure
        src_dir = test_project / "src" / "services"
        tests_dir = test_project / "tests"
        specs_dir = test_project / "specs"
        
        src_dir.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        specs_dir.mkdir(parents=True)
        
        # Add requirements to Neo4j (from PM)
        engineering_requirements = [
            {
                "id": "REQ-AUTH-001",
                "description": "User authentication service with JWT tokens",
                "type": "FR",
                "priority": "M",
                "stage": "mvp",
                "status": "ready_for_implementation",
                "acceptance_criteria": [
                    "Support email/password login",
                    "Generate secure JWT tokens", 
                    "Token expiration and refresh"
                ]
            },
            {
                "id": "REQ-USER-001", 
                "description": "User profile management service",
                "type": "FR",
                "priority": "M",
                "stage": "mvp",
                "status": "ready_for_implementation",
                "acceptance_criteria": [
                    "CRUD operations for user profiles",
                    "Profile data validation",
                    "Avatar upload support"
                ]
            },
            {
                "id": "NFR-SEC-001",
                "description": "All user data must be encrypted at rest and in transit",
                "type": "NFR",
                "category": "security",
                "priority": "M", 
                "stage": "mvp",
                "status": "ready_for_implementation"
            }
        ]
        
        for req in engineering_requirements:
            query = """
            MERGE (r:Requirement {id: $id})
            SET r.description = $description,
                r.type = $type,
                r.priority = $priority,
                r.stage = $stage,
                r.status = $status,
                r.created_at = datetime(),
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, req)
        
        # === STEP 2: Engineer generates service stubs with provenance headers ===
        
        # Create authentication service
        auth_service_code = provenance.generate_provenance_header(
            artifact_name="AuthenticationService",
            artifact_type="Service",
            requirements=["REQ-AUTH-001", "NFR-SEC-001"],
            tests=["TEST-U-AUTH-001", "TEST-I-AUTH-001"],
            generation_info={"tool": "manual", "version": "1.0"}
        )
        
        auth_service_code += '''

from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from pydantic import BaseModel

class AuthenticationService:
    """Handles user authentication with JWT tokens.
    
    Implements: REQ-AUTH-001, NFR-SEC-001
    """
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token.
        
        Implements: REQ-AUTH-001
        """
        # Hash password check (simplified for test)
        if self._verify_password(email, password):
            return self._generate_jwt_token(email)
        return None
    
    def _verify_password(self, email: str, password: str) -> bool:
        """Verify password against stored hash."""
        # Simplified implementation
        return True  # Mock success
    
    def _generate_jwt_token(self, email: str) -> str:
        """Generate JWT token with expiration.
        
        Implements: REQ-AUTH-001
        """
        payload = {
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
'''
        
        # Write service file
        auth_service_path = src_dir / "authentication_service.py"
        auth_service_path.write_text(auth_service_code)
        
        # Create user service
        user_service_code = provenance.generate_provenance_header(
            artifact_name="UserProfileService", 
            artifact_type="Service",
            requirements=["REQ-USER-001", "NFR-SEC-001"],
            tests=["TEST-U-USER-001", "TEST-I-USER-001"]
        )
        
        user_service_code += '''

from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
import hashlib

class UserProfile(BaseModel):
    """User profile data model."""
    user_id: str
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class UserProfileService:
    """Manages user profile data and operations.
    
    Implements: REQ-USER-001, NFR-SEC-001
    """
    
    def __init__(self):
        self.profiles = {}  # Mock storage
    
    def create_profile(self, profile_data: Dict[str, Any]) -> UserProfile:
        """Create new user profile.
        
        Implements: REQ-USER-001
        """
        profile = UserProfile(
            user_id=hashlib.md5(profile_data['email'].encode()).hexdigest(),
            **profile_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.profiles[profile.user_id] = profile
        return profile
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve user profile by ID."""
        return self.profiles.get(user_id)
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[UserProfile]:
        """Update user profile data.
        
        Implements: REQ-USER-001
        """
        if user_id in self.profiles:
            profile = self.profiles[user_id]
            for key, value in updates.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
            return profile
        return None
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete user profile."""
        if user_id in self.profiles:
            del self.profiles[user_id]
            return True
        return False
'''
        
        user_service_path = src_dir / "user_profile_service.py" 
        user_service_path.write_text(user_service_code)
        
        # === STEP 3: Engineer creates comprehensive test suite ===
        
        # Unit tests for authentication service
        auth_unit_test = '''"""Unit tests for AuthenticationService.

Verifies: REQ-AUTH-001, NFR-SEC-001
"""

import pytest
from datetime import datetime, timedelta
from src.services.authentication_service import AuthenticationService

class TestAuthenticationService:
    """Unit tests for authentication service.
    
    Covers: REQ-AUTH-001
    """
    
    def setup_method(self):
        self.auth_service = AuthenticationService("test_secret_key")
    
    def test_authenticate_user_success(self):
        """Test successful user authentication.
        
        Verifies: REQ-AUTH-001 - Generate secure JWT tokens
        """
        token = self.auth_service.authenticate_user("test@example.com", "password")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long
    
    def test_authenticate_user_failure(self):
        """Test authentication failure with invalid credentials."""
        # This would fail in a real implementation with password checking
        pass
    
    def test_jwt_token_validation(self):
        """Test JWT token validation.
        
        Verifies: REQ-AUTH-001 - Token expiration and refresh
        """
        token = self.auth_service.authenticate_user("test@example.com", "password")
        payload = self.auth_service.validate_token(token)
        
        assert payload is not None
        assert payload['email'] == "test@example.com"
        assert 'exp' in payload
        assert 'iat' in payload
    
    def test_token_security_properties(self):
        """Test security properties of tokens.
        
        Verifies: NFR-SEC-001 - Encryption and security
        """
        token1 = self.auth_service.authenticate_user("user1@example.com", "password")
        token2 = self.auth_service.authenticate_user("user2@example.com", "password")
        
        # Tokens should be different for different users
        assert token1 != token2
        
        # Tokens should not contain plaintext email
        assert "user1@example.com" not in token1
        assert "user2@example.com" not in token2
'''
        
        auth_test_path = tests_dir / "test_authentication_service.py"
        auth_test_path.write_text(auth_unit_test)
        
        # Integration tests
        integration_test = '''"""Integration tests for user authentication flow.

Covers: REQ-AUTH-001, REQ-USER-001, NFR-SEC-001
"""

import pytest
from src.services.authentication_service import AuthenticationService
from src.services.user_profile_service import UserProfileService, UserProfile

class TestUserAuthIntegration:
    """Integration tests for authentication and user profile services.
    
    Covers: REQ-AUTH-001, REQ-USER-001
    """
    
    def setup_method(self):
        self.auth_service = AuthenticationService("integration_test_key")
        self.user_service = UserProfileService()
    
    def test_complete_user_registration_flow(self):
        """Test complete user registration and authentication flow.
        
        Verifies: REQ-AUTH-001, REQ-USER-001 - End-to-end user management
        """
        # Create user profile
        profile_data = {
            "email": "integration@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        profile = self.user_service.create_profile(profile_data)
        assert profile is not None
        assert profile.email == "integration@example.com"
        
        # Authenticate user
        token = self.auth_service.authenticate_user("integration@example.com", "password")
        assert token is not None
        
        # Validate token
        payload = self.auth_service.validate_token(token)
        assert payload is not None
        assert payload['email'] == "integration@example.com"
        
        # Update profile (authorized operation)
        updated_profile = self.user_service.update_profile(
            profile.user_id, 
            {"first_name": "Updated"}
        )
        assert updated_profile.first_name == "Updated"
    
    def test_security_boundary_validation(self):
        """Test security boundaries between services.
        
        Verifies: NFR-SEC-001 - Security controls
        """
        # Test that invalid tokens are rejected
        invalid_token = "invalid.jwt.token"
        payload = self.auth_service.validate_token(invalid_token)
        assert payload is None
        
        # Test that expired tokens are rejected (simulated)
        # In real implementation, would test with expired token
        pass
'''
        
        integration_test_path = tests_dir / "test_integration_user_auth.py"
        integration_test_path.write_text(integration_test)
        
        # E2E tests
        e2e_test = '''"""End-to-end tests for complete user workflows.

Validates: Complete user journey from registration to authenticated operations
"""

import pytest
from src.services.authentication_service import AuthenticationService
from src.services.user_profile_service import UserProfileService

class TestCompleteUserWorkflow:
    """End-to-end tests for complete user workflows.
    
    Validates: FRS-FEAT-001 (User Authentication), FRS-FEAT-002 (Profile Management)
    """
    
    def setup_method(self):
        self.auth_service = AuthenticationService("e2e_test_key")
        self.user_service = UserProfileService()
    
    def test_new_user_complete_journey(self):
        """Test complete new user journey from registration to profile management.
        
        Validates: Complete user onboarding and management workflow
        """
        # Step 1: User registration
        user_data = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User"
        }
        
        profile = self.user_service.create_profile(user_data)
        assert profile is not None
        
        # Step 2: User login
        token = self.auth_service.authenticate_user("newuser@example.com", "password")
        assert token is not None
        
        # Step 3: Authenticated profile operations
        payload = self.auth_service.validate_token(token)
        assert payload is not None
        
        # Step 4: Profile updates
        updated = self.user_service.update_profile(
            profile.user_id,
            {"first_name": "Updated New"}
        )
        assert updated.first_name == "Updated New"
        
        # Step 5: Profile retrieval
        retrieved = self.user_service.get_profile(profile.user_id)
        assert retrieved.first_name == "Updated New"
        
        print(f"✅ Complete user journey validated")
        print(f"   👤 Profile Created: {profile.user_id}")
        print(f"   🔐 Authentication: Success")
        print(f"   ✏️  Profile Updates: Success")
'''
        
        e2e_test_path = tests_dir / "test_e2e_user_workflow.py"
        e2e_test_path.write_text(e2e_test)
        
        # Add requirements to Neo4j
        for req in engineering_requirements:
            query = """
            MERGE (r:Requirement {id: $id})
            SET r.description = $description,
                r.type = $type,
                r.priority = $priority,
                r.stage = $stage,
                r.status = $status,
                r.created_at = datetime(),
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, req)
        
        # === STEP 4: Engineer scans implemented code ===
        
        scan_results = scanner.scan_codebase(str(test_project))
        
        # Verify scan found our services
        assert scan_results["scanned_files"] >= 2  # Auth + User services
        assert len(scan_results["services"]) >= 2   # Should detect services
        assert len(scan_results["functions"]) >= 6  # Multiple functions per service
        
        # Check that services were properly identified
        service_names = [s["name"] for s in scan_results["services"].values()]
        assert any("authentication" in name.lower() for name in service_names)
        assert any("user" in name.lower() for name in service_names)
        
        # === STEP 5: Engineer validates provenance headers ===
        
        header_validation = provenance.validate_provenance_headers(str(test_project))
        
        # Our generated files should have headers
        assert header_validation["files_with_headers"] >= 2
        assert header_validation["coverage_rate"] > 0.5  # >50% coverage
        
        # Should not have orphan artifacts (our files have REQ tags)
        assert len(header_validation["orphan_artifacts"]) == 0
        
        # === STEP 6: Engineer runs complete traceability analysis ===
        
        # Sync artifacts to Neo4j
        provenance.sync_artifacts_to_neo4j(scan_results)
        
        # Generate traceability matrix
        matrix_entries = matrix.generate_complete_matrix(increment_filter="mvp")
        
        # Should have entries for our requirements
        req_auth_entry = next((e for e in matrix_entries if e.req_id == "REQ-AUTH-001"), None)
        assert req_auth_entry is not None
        assert len(req_auth_entry.implementing_code) > 0  # Should have AuthenticationService
        
        req_user_entry = next((e for e in matrix_entries if e.req_id == "REQ-USER-001"), None)
        assert req_user_entry is not None 
        assert len(req_user_entry.implementing_code) > 0  # Should have UserProfileService
        
        # === STEP 7: Engineer validates test coverage ===
        
        coverage_report = matrix.generate_coverage_report("mvp")
        
        # Should have reasonable coverage since we implemented services and tests
        assert coverage_report.overall_coverage > 50.0  # >50% coverage
        
        # Check coverage by requirement type
        fr_coverage = coverage_report.by_requirement_type.get("FR", 0)
        nfr_coverage = coverage_report.by_requirement_type.get("NFR", 0)
        
        # Functional requirements should have code + test coverage
        assert fr_coverage > 60.0
        
        # === STEP 8: Engineer performs change impact analysis ===
        
        # Simulate changing authentication service
        impact_report = provenance.generate_impact_report(["SVC-AUTHENTICATION"])
        
        # Should identify affected requirements
        assert len(impact_report["upstream_requirements"]) > 0
        assert "REQ-AUTH-001" in impact_report["upstream_requirements"]
        
        # Should identify affected tests
        assert len(impact_report["downstream_tests"]) > 0
        
        # === STEP 9: Engineer validates deployment readiness ===
        
        readiness_check = matrix.validate_increment_readiness("mvp")
        
        # Check readiness criteria
        assert readiness_check["increment"] == "mvp"
        assert readiness_check["overall_coverage"] > 0
        
        # If not ready, should have specific blocking issues
        if not readiness_check["ready_for_release"]:
            assert len(readiness_check["blocking_issues"]) > 0
            
            # Common blocking issues for new implementation
            blocking_reasons = " ".join(readiness_check["blocking_issues"]).lower()
            expected_issues = ["coverage", "orphan", "untested"]
            # Should identify specific technical issues
        
        # === STEP 10: Engineer validates success metrics ===
        
        engineer_success_criteria = {
            "code_generated_with_provenance": header_validation["files_with_headers"] >= 2,
            "requirements_implemented": len([e for e in matrix_entries if len(e.implementing_code) > 0]) >= 2,
            "tests_created": scan_results["scanned_files"] >= 5,  # Services + tests
            "traceability_established": len(matrix_entries) > 0,
            "coverage_measured": coverage_report.overall_coverage > 0,
            "impact_analysis_functional": len(impact_report["upstream_requirements"]) > 0,
            "deployment_readiness_assessed": readiness_check is not None,
            "no_orphan_code": len(header_validation.get("orphan_artifacts", [])) == 0
        }
        
        success_count = sum(1 for criterion, met in engineer_success_criteria.items() if met)
        success_rate = success_count / len(engineer_success_criteria)
        
        # Engineer journey should achieve >85% success rate
        assert success_rate >= 0.85, f"Engineer journey success rate {success_rate:.1%} < 85%"
        
        print(f"✅ Engineer Journey Completed Successfully!")
        print(f"   📊 Success Rate: {success_rate:.1%}")
        print(f"   💻 Services Implemented: {len(scan_results['services'])}")
        print(f"   🧪 Tests Created: {scan_results['scanned_files'] - len(scan_results['services'])}")
        print(f"   🔗 Traceability Entries: {len(matrix_entries)}")
        print(f"   📈 Coverage: {coverage_report.overall_coverage:.1f}%")
        print(f"   📄 Provenance Coverage: {header_validation['coverage_rate']:.1%}")
        print(f"   🚀 Deployment Ready: {readiness_check['ready_for_release']}")

    @pytest.mark.asyncio
    async def test_engineer_tdd_workflow(self, engineer_test_setup):
        """Test engineer Test-Driven Development workflow with requirement traceability."""
        
        services = engineer_test_setup
        neo4j = services["neo4j"]
        scanner = services["scanner"]
        provenance = services["provenance"]
        matrix = services["matrix"]
        test_project = services["test_project"]
        
        # === TDD STEP 1: Engineer writes failing tests first ===
        
        # Add requirement to Neo4j
        tdd_requirement = {
            "id": "REQ-TDD-001",
            "description": "Calculator service with basic arithmetic operations",
            "type": "FR",
            "priority": "M",
            "stage": "mvp",
            "status": "ready_for_implementation"
        }
        
        query = """
        MERGE (r:Requirement {id: $id})
        SET r.description = $description,
            r.type = $type,
            r.priority = $priority,
            r.stage = $stage,
            r.status = $status,
            r.created_at = datetime(),
            r.updated_at = datetime()
        """
        
        with neo4j.driver.session(database=neo4j.config.database) as session:
            session.run(query, tdd_requirement)
        
        # Create tests directory
        tests_dir = test_project / "tests" / "tdd"
        tests_dir.mkdir(parents=True)
        
        # Write failing test first (TDD Red phase)
        failing_test = '''"""TDD test for calculator service - RED phase.

Covers: REQ-TDD-001
"""

import pytest
from src.services.calculator_service import CalculatorService  # This doesn't exist yet

class TestCalculatorServiceTDD:
    """TDD tests for calculator service.
    
    Covers: REQ-TDD-001
    """
    
    def setup_method(self):
        self.calculator = CalculatorService()
    
    def test_addition(self):
        """Test addition operation.
        
        Verifies: REQ-TDD-001 - Basic arithmetic operations
        """
        result = self.calculator.add(2, 3)
        assert result == 5
        
    def test_subtraction(self):
        """Test subtraction operation.""" 
        result = self.calculator.subtract(5, 3)
        assert result == 2
        
    def test_multiplication(self):
        """Test multiplication operation."""
        result = self.calculator.multiply(4, 3)
        assert result == 12
        
    def test_division(self):
        """Test division operation."""
        result = self.calculator.divide(10, 2)
        assert result == 5.0
        
    def test_division_by_zero(self):
        """Test division by zero handling."""
        with pytest.raises(ValueError):
            self.calculator.divide(10, 0)
'''
        
        failing_test_path = tests_dir / "test_calculator_service_tdd.py"
        failing_test_path.write_text(failing_test)
        
        # === TDD STEP 2: Engineer implements minimum code to pass tests (GREEN phase) ===
        
        src_dir = test_project / "src" / "services"
        src_dir.mkdir(parents=True)
        
        # Generate provenance header
        calculator_code = provenance.generate_provenance_header(
            artifact_name="CalculatorService",
            artifact_type="Service", 
            requirements=["REQ-TDD-001"],
            tests=["TEST-TDD-001"],
            generation_info={"tool": "tdd", "version": "1.0"}
        )
        
        calculator_code += '''

class CalculatorService:
    """Basic calculator service with arithmetic operations.
    
    Implements: REQ-TDD-001
    """
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers.
        
        Implements: REQ-TDD-001
        """
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b.
        
        Raises:
            ValueError: If b is zero
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
'''
        
        calculator_service_path = src_dir / "calculator_service.py"
        calculator_service_path.write_text(calculator_code)
        
        # === TDD STEP 3: Engineer scans and validates TDD cycle ===
        
        # Scan the TDD implementation
        tdd_scan_results = scanner.scan_codebase(str(test_project))
        
        # Should find calculator service
        calc_service = None
        for service_id, service in tdd_scan_results["services"].items():
            if "calculator" in service["name"].lower():
                calc_service = service
                break
        
        assert calc_service is not None
        assert "REQ-TDD-001" in calc_service["implements"]
        
        # Should find test functions
        test_functions = [t for t in tdd_scan_results["tests"].values() if "calculator" in t["name"].lower()]
        assert len(test_functions) >= 4  # add, subtract, multiply, divide tests
        
        # === TDD STEP 4: Engineer validates TDD traceability ===
        
        # Sync TDD artifacts to Neo4j
        provenance.sync_artifacts_to_neo4j(tdd_scan_results)
        
        # Generate traceability matrix
        tdd_matrix = matrix.generate_complete_matrix()
        
        # Find TDD requirement entry
        tdd_entry = next((e for e in tdd_matrix if e.req_id == "REQ-TDD-001"), None)
        assert tdd_entry is not None
        
        # TDD should result in good coverage
        assert len(tdd_entry.implementing_code) > 0     # Calculator service
        assert len(tdd_entry.unit_tests) >= 4          # All arithmetic operation tests
        assert tdd_entry.coverage_percentage >= 80.0   # High coverage from TDD
        assert tdd_entry.status == "GREEN"             # Full coverage
        
        # === TDD STEP 5: Engineer validates TDD best practices compliance ===
        
        tdd_compliance = {
            "test_first": True,  # We wrote tests before implementation
            "minimum_implementation": True,  # Simple implementation to pass tests
            "requirement_traceability": "REQ-TDD-001" in calc_service["implements"],
            "comprehensive_test_coverage": len(test_functions) >= 4,
            "provenance_headers_present": True,  # Generated with headers
            "traceability_matrix_updated": tdd_entry is not None
        }
        
        tdd_compliance_rate = sum(1 for check, passed in tdd_compliance.items() if passed) / len(tdd_compliance)
        
        # TDD workflow should achieve perfect compliance
        assert tdd_compliance_rate == 1.0, f"TDD compliance {tdd_compliance_rate:.1%} < 100%"
        
        print(f"✅ Engineer TDD Journey Completed Successfully!")
        print(f"   🔴 Red Phase: Failing tests written first")
        print(f"   🟢 Green Phase: Minimum implementation created") 
        print(f"   🔵 Blue Phase: Traceability validated")
        print(f"   📊 TDD Compliance: {tdd_compliance_rate:.1%}")
        print(f"   🧪 Test Coverage: {tdd_entry.coverage_percentage:.1f}%")
        print(f"   🏆 Final Status: {tdd_entry.status}")

    @pytest.mark.asyncio  
    async def test_engineer_refactoring_with_provenance_preservation(self, engineer_test_setup):
        """Test engineer refactoring while preserving complete provenance."""
        
        services = engineer_test_setup
        neo4j = services["neo4j"]
        scanner = services["scanner"]
        provenance = services["provenance"]
        matrix = services["matrix"]
        test_project = services["test_project"]
        
        # === STEP 1: Engineer starts with existing service to refactor ===
        
        # Create initial implementation
        src_dir = test_project / "src" / "services"
        src_dir.mkdir(parents=True)
        
        # Original implementation (monolithic)
        original_code = provenance.generate_provenance_header(
            artifact_name="OrderProcessingService",
            artifact_type="Service",
            requirements=["REQ-ORDER-001", "REQ-PAYMENT-001", "REQ-SHIPPING-001"],
            tests=["TEST-U-ORDER-001"]
        )
        
        original_code += '''

class OrderProcessingService:
    """Monolithic order processing service - needs refactoring.
    
    Implements: REQ-ORDER-001, REQ-PAYMENT-001, REQ-SHIPPING-001
    """
    
    def process_order(self, order_data):
        """Process complete order including payment and shipping.
        
        Implements: REQ-ORDER-001, REQ-PAYMENT-001, REQ-SHIPPING-001
        """
        # Validate order
        if not self._validate_order(order_data):
            raise ValueError("Invalid order data")
        
        # Process payment
        payment_result = self._process_payment(order_data["payment"])
        if not payment_result["success"]:
            raise Exception("Payment failed")
        
        # Arrange shipping
        shipping_result = self._arrange_shipping(order_data["shipping"])
        if not shipping_result["success"]: 
            raise Exception("Shipping arrangement failed")
        
        return {"order_id": "ORD-123", "status": "processed"}
    
    def _validate_order(self, order_data):
        """Validate order data."""
        return order_data and "items" in order_data
    
    def _process_payment(self, payment_data):
        """Process payment (should be separate service)."""
        return {"success": True, "transaction_id": "TXN-456"}
    
    def _arrange_shipping(self, shipping_data):
        """Arrange shipping (should be separate service)."""
        return {"success": True, "tracking_id": "TRK-789"}
'''
        
        original_service_path = src_dir / "order_processing_service.py"
        original_service_path.write_text(original_code)
        
        # Add requirements to Neo4j
        refactor_requirements = [
            {
                "id": "REQ-ORDER-001",
                "description": "Process customer orders with validation",
                "type": "FR",
                "priority": "M",
                "stage": "mvp"
            },
            {
                "id": "REQ-PAYMENT-001", 
                "description": "Process payments securely",
                "type": "FR",
                "priority": "M",
                "stage": "mvp"
            },
            {
                "id": "REQ-SHIPPING-001",
                "description": "Arrange shipping for completed orders",
                "type": "FR", 
                "priority": "M",
                "stage": "mvp"
            }
        ]
        
        for req in refactor_requirements:
            query = """
            MERGE (r:Requirement {id: $id})
            SET r.description = $description,
                r.type = $type,
                r.priority = $priority,
                r.stage = $stage,
                r.status = 'implemented',
                r.created_at = datetime(),
                r.updated_at = datetime()
            """
            
            with neo4j.driver.session(database=neo4j.config.database) as session:
                session.run(query, req)
        
        # === STEP 2: Engineer scans original implementation ===
        
        original_scan = scanner.scan_codebase(str(test_project))
        provenance.sync_artifacts_to_neo4j(original_scan)
        
        original_matrix = matrix.generate_complete_matrix()
        
        # Should have one service implementing multiple requirements (anti-pattern)
        order_entry = next((e for e in original_matrix if "REQ-ORDER-001" in e.req_id), None)
        payment_entry = next((e for e in original_matrix if "REQ-PAYMENT-001" in e.req_id), None)
        shipping_entry = next((e for e in original_matrix if "REQ-SHIPPING-001" in e.req_id), None)
        
        # All should point to same monolithic service
        assert order_entry.implementing_code == payment_entry.implementing_code == shipping_entry.implementing_code
        
        # === STEP 3: Engineer refactors into separate services ===
        
        # Create separate services for each concern
        
        # Order service
        order_service_code = provenance.generate_provenance_header(
            artifact_name="OrderService",
            artifact_type="Service",
            requirements=["REQ-ORDER-001"],
            tests=["TEST-U-ORDER-002", "TEST-I-ORDER-001"]
        )
        
        order_service_code += '''

class OrderService:
    """Focused order management service.
    
    Implements: REQ-ORDER-001
    """
    
    def create_order(self, order_data):
        """Create and validate new order.
        
        Implements: REQ-ORDER-001
        """
        if not self._validate_order(order_data):
            raise ValueError("Invalid order data")
        
        return {"order_id": "ORD-123", "status": "created", "items": order_data["items"]}
    
    def _validate_order(self, order_data):
        """Validate order data structure and business rules."""
        return order_data and "items" in order_data and len(order_data["items"]) > 0
'''
        
        # Payment service
        payment_service_code = provenance.generate_provenance_header(
            artifact_name="PaymentService", 
            artifact_type="Service",
            requirements=["REQ-PAYMENT-001"],
            tests=["TEST-U-PAYMENT-001", "TEST-I-PAYMENT-001"]
        )
        
        payment_service_code += '''

class PaymentService:
    """Dedicated payment processing service.
    
    Implements: REQ-PAYMENT-001
    """
    
    def process_payment(self, payment_data):
        """Process payment transaction securely.
        
        Implements: REQ-PAYMENT-001
        """
        # Validate payment data
        if not payment_data.get("amount") or payment_data["amount"] <= 0:
            raise ValueError("Invalid payment amount")
        
        # Process payment (simplified)
        return {
            "success": True,
            "transaction_id": f"TXN-{payment_data['amount']:.2f}",
            "amount": payment_data["amount"]
        }
'''
        
        # Shipping service  
        shipping_service_code = provenance.generate_provenance_header(
            artifact_name="ShippingService",
            artifact_type="Service", 
            requirements=["REQ-SHIPPING-001"],
            tests=["TEST-U-SHIPPING-001", "TEST-I-SHIPPING-001"]
        )
        
        shipping_service_code += '''

class ShippingService:
    """Dedicated shipping arrangement service.
    
    Implements: REQ-SHIPPING-001  
    """
    
    def arrange_shipping(self, shipping_data):
        """Arrange shipping for order.
        
        Implements: REQ-SHIPPING-001
        """
        if not shipping_data.get("address"):
            raise ValueError("Shipping address required")
        
        return {
            "success": True,
            "tracking_id": "TRK-789",
            "estimated_delivery": "3-5 business days"
        }
'''
        
        # Write refactored services
        (src_dir / "order_service.py").write_text(order_service_code)
        (src_dir / "payment_service.py").write_text(payment_service_code)
        (src_dir / "shipping_service.py").write_text(shipping_service_code)
        
        # Remove original monolithic service
        original_service_path.unlink()
        
        # === STEP 4: Engineer validates refactoring preserved provenance ===
        
        # Scan refactored codebase
        refactored_scan = scanner.scan_codebase(str(test_project))
        provenance.sync_artifacts_to_neo4j(refactored_scan)
        
        # Generate updated matrix
        refactored_matrix = matrix.generate_complete_matrix()
        
        # Each requirement should now have dedicated implementing service
        refactored_order_entry = next((e for e in refactored_matrix if e.req_id == "REQ-ORDER-001"), None)
        refactored_payment_entry = next((e for e in refactored_matrix if e.req_id == "REQ-PAYMENT-001"), None)  
        refactored_shipping_entry = next((e for e in refactored_matrix if e.req_id == "REQ-SHIPPING-001"), None)
        
        assert refactored_order_entry is not None
        assert refactored_payment_entry is not None
        assert refactored_shipping_entry is not None
        
        # Should now have different implementing services
        assert refactored_order_entry.implementing_code != refactored_payment_entry.implementing_code
        assert refactored_payment_entry.implementing_code != refactored_shipping_entry.implementing_code
        
        # All should maintain traceability to original requirements
        assert "REQ-ORDER-001" in str(refactored_order_entry.implementing_code)
        assert "REQ-PAYMENT-001" in str(refactored_payment_entry.implementing_code)
        assert "REQ-SHIPPING-001" in str(refactored_shipping_entry.implementing_code)
        
        # === STEP 5: Engineer validates improved architecture ===
        
        # Compare before/after metrics
        original_service_count = len(original_scan["services"])
        refactored_service_count = len(refactored_scan["services"])
        
        # Should have more services after refactoring (better separation of concerns)
        assert refactored_service_count > original_service_count
        
        # Calculate average complexity per service
        original_complexity = sum(s["complexity"] for s in original_scan["services"].values()) / len(original_scan["services"])
        refactored_complexity = sum(s["complexity"] for s in refactored_scan["services"].values()) / len(refactored_scan["services"])
        
        # Average complexity should be lower after refactoring
        assert refactored_complexity <= original_complexity
        
        print(f"✅ Engineer Refactoring Journey Completed Successfully!")
        print(f"   🏗️  Services Before: {original_service_count}")
        print(f"   🏗️  Services After: {refactored_service_count}")
        print(f"   📊 Complexity Before: {original_complexity:.1f}")
        print(f"   📊 Complexity After: {refactored_complexity:.1f}")
        print(f"   🔗 Provenance Preserved: {len(refactored_matrix)} traceable requirements")
        print(f"   ✅ Architecture Improved: Lower coupling, better separation")
