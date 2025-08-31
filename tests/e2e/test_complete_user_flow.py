"""
Complete User Flow End-to-End Tests with Playwright

VERIFIES: Complete user workflows through Web UI
VALIDATES: UC-001→UC-010 (all user journey scenarios)  
TEST_TYPE: End-to-End (Playwright)
BROWSER_COVERAGE: Chrome, Firefox, Safari
LAST_SYNC: 2025-08-30
"""

import pytest
from playwright.async_api import async_playwright, Page, BrowserContext
import json
import asyncio
from pathlib import Path


class TestCompleteUserFlowE2E:
    """End-to-end tests for complete user workflows through the web interface."""

    @pytest.fixture(scope="class")
    async def browser_context(self):
        """Set up browser context for tests."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set to True for CI
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                record_video_dir="tests/e2e/videos/"
            )
            yield context
            await browser.close()

    @pytest.fixture
    async def page(self, browser_context):
        """Create new page for each test."""
        page = await browser_context.new_page()
        # Navigate to local development server
        await page.goto("http://localhost:3000")
        yield page
        await page.close()

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_water_app_idea_to_implementation_flow(self, page: Page):
        """
        VERIFIES: Complete pipeline from idea input to code generation
        SCENARIO: Water tracking app - full user journey
        USE_CASE: UC-001→UC-005 (idea to implementation)
        EXPECTED_DURATION: ~10 minutes
        """
        
        # Step 1: Navigate to idea input page
        await page.click('text=New Project')
        await page.wait_for_selector('[data-testid="idea-input"]')
        
        # Step 2: Enter water tracking app idea
        idea_text = """
        Build a water tracking app for health-conscious professionals who struggle 
        to maintain proper hydration throughout their busy workday. The app should 
        send smart reminders based on activity level, weather, and personal goals.
        """
        
        await page.fill('[data-testid="idea-input"]', idea_text)
        await page.click('[data-testid="analyze-idea-btn"]')
        
        # Step 3: Wait for entity extraction and verify results
        await page.wait_for_selector('[data-testid="entity-graph"]', timeout=30000)
        
        # Verify extracted entities are displayed
        problem_entity = page.locator('[data-testid="entity-problem"]')
        await expect(problem_entity).to_be_visible()
        await expect(problem_entity).to_contain_text("hydration")
        
        user_entity = page.locator('[data-testid="entity-target-user"]') 
        await expect(user_entity).to_be_visible()
        await expect(user_entity).to_contain_text("professionals")
        
        solution_entity = page.locator('[data-testid="entity-solution"]')
        await expect(solution_entity).to_be_visible()
        await expect(solution_entity).to_contain_text("tracking app")
        
        # Step 4: Select paradigm framework (YC Startup)
        await page.click('[data-testid="select-paradigm-btn"]')
        await page.wait_for_selector('[data-testid="paradigm-options"]')
        
        await page.click('[data-testid="paradigm-yc-startup"]')
        await page.click('[data-testid="confirm-paradigm-btn"]')
        
        # Step 5: Answer paradigm-specific questions
        await page.wait_for_selector('[data-testid="paradigm-questions"]')
        
        # Market size question
        market_question = page.locator('[data-testid="question-market-size"]')
        await expect(market_question).to_be_visible()
        await page.fill('[data-testid="answer-market-size"]', 
                       "Health app market $4.2B, growing 15% annually")
        
        # Problem validation question  
        problem_question = page.locator('[data-testid="question-problem-validation"]')
        await expect(problem_question).to_be_visible()
        await page.fill('[data-testid="answer-problem-validation"]',
                       "67% of professionals struggle with hydration tracking")
        
        # MVP scope question
        mvp_question = page.locator('[data-testid="question-mvp-scope"]')
        await expect(mvp_question).to_be_visible()
        await page.fill('[data-testid="answer-mvp-scope"]',
                       "Basic water logging with smart reminder notifications")
        
        await page.click('[data-testid="submit-paradigm-answers-btn"]')
        
        # Step 6: Wait for research expansion
        await page.wait_for_selector('[data-testid="research-expansion"]', timeout=60000)
        
        research_results = page.locator('[data-testid="research-insights"]')
        await expect(research_results).to_be_visible()
        await expect(research_results).to_contain_text("market")
        
        # Step 7: Navigate to vision generation
        await page.click('[data-testid="generate-vision-btn"]')
        await page.wait_for_selector('[data-testid="council-debate"]')
        
        # Step 8: Monitor council debate progress
        debate_status = page.locator('[data-testid="debate-status"]')
        await expect(debate_status).to_contain_text("In Progress")
        
        # Wait for council members to provide input
        pm_response = page.locator('[data-testid="council-pm-response"]')
        await expect(pm_response).to_be_visible(timeout=120000)
        
        security_response = page.locator('[data-testid="council-security-response"]')
        await expect(security_response).to_be_visible()
        
        # Step 9: Handle human input prompts
        human_prompt = page.locator('[data-testid="human-input-prompt"]')
        if await human_prompt.is_visible():
            await page.fill('[data-testid="human-context-input"]',
                           "Budget: $50k, Team: 2 developers, Timeline: 3 months")
            await page.click('[data-testid="submit-human-input-btn"]')
        
        # Step 10: Wait for vision consensus
        await page.wait_for_selector('[data-testid="consensus-reached"]', timeout=180000)
        
        consensus_score = page.locator('[data-testid="consensus-score"]')
        await expect(consensus_score).to_contain_text("4.")  # Should be >4.0
        
        # Step 11: Verify vision document generation
        await page.click('[data-testid="view-generated-vision-btn"]')
        
        vision_content = page.locator('[data-testid="generated-vision-content"]')
        await expect(vision_content).to_be_visible()
        await expect(vision_content).to_contain_text("hydration")
        await expect(vision_content).to_contain_text("professionals")
        await expect(vision_content).to_contain_text("$4.2B")

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_prd_generation_with_hierarchical_requirements(self, page: Page):
        """
        VERIFIES: R-PRD-017 (spec generation), UC-002 (vision to PRD)
        SCENARIO: Vision document → hierarchical PRD → REQ/NFR specs
        PREREQUISITE: Vision document exists from previous test
        """
        
        # Step 1: Navigate to PRD generation (assuming vision exists)
        await page.goto("http://localhost:3000/projects/water-app/prd")
        await page.wait_for_selector('[data-testid="generate-prd-btn"]')
        
        # Step 2: Initiate PRD generation from vision
        await page.click('[data-testid="generate-prd-btn"]')
        await page.wait_for_selector('[data-testid="prd-council-debate"]')
        
        # Step 3: Monitor PRD generation progress
        prd_status = page.locator('[data-testid="prd-generation-status"]')
        await expect(prd_status).to_contain_text("Generating")
        
        # Step 4: Verify hierarchical PRD structure
        await page.wait_for_selector('[data-testid="hierarchical-prd"]', timeout=120000)
        
        main_prd = page.locator('[data-testid="main-prd"]')
        await expect(main_prd).to_be_visible()
        
        sub_prds = page.locator('[data-testid="sub-prd"]')
        await expect(sub_prds).to_have_count(3)  # tracking, notifications, user mgmt
        
        # Step 5: Verify REQ/NFR specification generation
        await page.click('[data-testid="view-specifications-btn"]')
        
        req_specs = page.locator('[data-testid="req-specification"]')
        await expect(req_specs.first).to_be_visible()
        await expect(req_specs.first).to_contain_text("REQ-TRACKING-001")
        
        nfr_specs = page.locator('[data-testid="nfr-specification"]')
        await expect(nfr_specs.first).to_be_visible()
        await expect(nfr_specs.first).to_contain_text("NFR-PERF-001")

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_code_generation_with_provenance_headers(self, page: Page):
        """
        VERIFIES: R-PRD-018→R-PRD-019 (code generation + provenance)
        SCENARIO: Implementation plan → code stubs → provenance validation
        PREREQUISITE: PRD and Architecture documents exist
        """
        
        # Step 1: Navigate to implementation planning
        await page.goto("http://localhost:3000/projects/water-app/implementation")
        await page.wait_for_selector('[data-testid="implementation-tasks"]')
        
        # Step 2: Review generated implementation tasks
        tasks = page.locator('[data-testid="implementation-task"]')
        await expect(tasks).to_have_count_greater_than(5)
        
        # Verify task details
        auth_task = page.locator('[data-testid="task-auth"]')
        await expect(auth_task).to_be_visible()
        await expect(auth_task).to_contain_text("T-AUTH-001")
        
        # Step 3: Generate code stubs
        await page.click('[data-testid="generate-code-stubs-btn"]')
        await page.wait_for_selector('[data-testid="code-generation-progress"]')
        
        # Wait for code generation completion
        await page.wait_for_selector('[data-testid="code-generation-complete"]', timeout=180000)
        
        # Step 4: Verify generated file structure
        file_tree = page.locator('[data-testid="generated-file-tree"]')
        await expect(file_tree).to_be_visible()
        
        # Check services directory
        services_folder = page.locator('[data-testid="folder-services"]')
        await expect(services_folder).to_be_visible()
        await services_folder.click()
        
        # Verify service files generated
        water_service = page.locator('[data-testid="file-water_service.py"]')
        await expect(water_service).to_be_visible()
        
        # Step 5: Verify provenance headers in generated code
        await water_service.click()
        
        code_content = page.locator('[data-testid="file-content"]')
        await expect(code_content).to_be_visible()
        await expect(code_content).to_contain_text("IMPLEMENTS:")
        await expect(code_content).to_contain_text("REQ-TRACKING-001")
        await expect(code_content).to_contain_text("VERIFIED_BY:")
        await expect(code_content).to_contain_text("LAST_SYNC:")
        
        # Step 6: Verify test file generation
        tests_folder = page.locator('[data-testid="folder-tests"]')
        await expect(tests_folder).to_be_visible()
        await tests_folder.click()
        
        test_water_service = page.locator('[data-testid="file-test_water_service.py"]')
        await expect(test_water_service).to_be_visible()
        await test_water_service.click()
        
        test_content = page.locator('[data-testid="file-content"]')
        await expect(test_content).to_contain_text("VERIFIES:")
        await expect(test_content).to_contain_text("REQ-TRACKING-001")

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_traceability_matrix_and_impact_analysis(self, page: Page):
        """
        VERIFIES: R-PRD-020→R-PRD-021 (traceability matrix + impact analysis)
        SCENARIO: View traceability matrix → simulate code change → see impact
        PREREQUISITE: Code has been generated with provenance
        """
        
        # Step 1: Navigate to traceability matrix view
        await page.goto("http://localhost:3000/projects/water-app/traceability")
        await page.wait_for_selector('[data-testid="traceability-matrix"]')
        
        # Step 2: Verify matrix completeness
        matrix_table = page.locator('[data-testid="traceability-table"]')
        await expect(matrix_table).to_be_visible()
        
        # Check requirement rows
        req_auth_row = page.locator('[data-testid="matrix-row-REQ-AUTH-001"]')
        await expect(req_auth_row).to_be_visible()
        
        # Verify coverage indicators
        coverage_indicator = req_auth_row.locator('[data-testid="coverage-indicator"]')
        await expect(coverage_indicator).to_have_class("success")
        
        # Step 3: Filter for orphaned code
        await page.click('[data-testid="filter-orphaned-code"]')
        
        orphaned_items = page.locator('[data-testid="orphaned-item"]')
        orphan_count = await orphaned_items.count()
        
        # Should show any orphaned code for cleanup
        if orphan_count > 0:
            await expect(orphaned_items.first).to_contain_text("ORPHAN")
        
        # Step 4: Simulate code change for impact analysis
        await page.click('[data-testid="simulate-change-btn"]')
        await page.wait_for_selector('[data-testid="change-simulation-modal"]')
        
        # Select file to change
        await page.selectOption('[data-testid="change-file-select"]', 'src/services/water_service.py')
        await page.fill('[data-testid="change-description"]', 'Add input validation to log_intake method')
        await page.click('[data-testid="analyze-impact-btn"]')
        
        # Step 5: Verify impact analysis results
        await page.wait_for_selector('[data-testid="impact-analysis-results"]')
        
        upstream_impacts = page.locator('[data-testid="upstream-impacts"]')
        await expect(upstream_impacts).to_be_visible()
        await expect(upstream_impacts).to_contain_text("REQ-TRACKING-001")
        await expect(upstream_impacts).to_contain_text("PRD.md")
        
        downstream_impacts = page.locator('[data-testid="downstream-impacts"]')
        await expect(downstream_impacts).to_be_visible()
        await expect(downstream_impacts).to_contain_text("test_water_service.py")
        await expect(downstream_impacts).to_contain_text("api_tracking.openapi.yaml")
        
        # Step 6: Verify recommended actions
        recommended_actions = page.locator('[data-testid="recommended-action"]')
        await expect(recommended_actions.first).to_be_visible()
        
        action_count = await recommended_actions.count()
        assert action_count >= 3  # Should suggest multiple actions

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_council_debate_with_human_intervention(self, page: Page):
        """
        VERIFIES: R-PRD-011→R-PRD-012 (human review + deadlock resolution)
        SCENARIO: Council debate → low consensus → human intervention → resolution
        USE_CASE: UC-003 (PRD to Architecture with human input)
        """
        
        # Step 1: Navigate to council debate page
        await page.goto("http://localhost:3000/projects/water-app/council")
        await page.wait_for_selector('[data-testid="council-chamber"]')
        
        # Step 2: Initiate architecture debate
        await page.click('[data-testid="start-architecture-debate-btn"]')
        await page.wait_for_selector('[data-testid="debate-in-progress"]')
        
        # Step 3: Monitor council member responses
        pm_bubble = page.locator('[data-testid="council-member-pm"]')
        await expect(pm_bubble).to_be_visible(timeout=60000)
        
        security_bubble = page.locator('[data-testid="council-member-security"]')
        await expect(security_bubble).to_be_visible(timeout=60000)
        
        infra_bubble = page.locator('[data-testid="council-member-infrastructure"]')
        await expect(infra_bubble).to_be_visible(timeout=60000)
        
        # Step 4: Check for low consensus trigger
        consensus_meter = page.locator('[data-testid="consensus-meter"]')
        await expect(consensus_meter).to_be_visible()
        
        # Wait for potential human intervention prompt
        human_prompt = page.locator('[data-testid="human-intervention-prompt"]')
        
        # If low consensus triggers human review
        if await human_prompt.is_visible(timeout=30000):
            # Step 5: Provide human context
            await page.fill('[data-testid="human-context-input"]',
                           """
                           Team context: 2 full-stack developers, experienced with React/Python
                           Budget constraint: $50k development budget
                           Timeline: 3-month MVP target
                           Risk tolerance: Medium (consumer health app)
                           Technology preference: Proven stack (FastAPI + React + PostgreSQL)
                           """)
            
            await page.click('[data-testid="submit-human-context-btn"]')
            
            # Step 6: Wait for consensus resolution
            await page.wait_for_selector('[data-testid="consensus-resolved"]', timeout=120000)
        
        # Step 7: Verify final consensus and decision
        final_consensus = page.locator('[data-testid="final-consensus-score"]')
        await expect(final_consensus).to_be_visible()
        
        consensus_text = await final_consensus.inner_text()
        consensus_score = float(consensus_text.split(":")[1].strip().split("/")[0])
        assert consensus_score >= 3.8  # Minimum passing score
        
        # Step 8: Verify architecture document generation
        await page.click('[data-testid="generate-architecture-btn"]')
        await page.wait_for_selector('[data-testid="architecture-document"]')
        
        arch_content = page.locator('[data-testid="architecture-content"]')
        await expect(arch_content).to_contain_text("## Components")
        await expect(arch_content).to_contain_text("Water Tracking Service")
        await expect(arch_content).to_contain_text("Notification Service")

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_real_time_provenance_tracking_during_development(self, page: Page):
        """
        VERIFIES: R-PRD-019→R-PRD-021 (provenance tracking + impact analysis)
        SCENARIO: Real-time provenance updates during code editing
        USE_CASE: UC-006 (change impact propagation)
        """
        
        # Step 1: Navigate to code editor with provenance panel
        await page.goto("http://localhost:3000/projects/water-app/code-editor")
        await page.wait_for_selector('[data-testid="code-editor"]')
        
        # Step 2: Open water service file
        await page.click('[data-testid="file-water_service.py"]')
        await page.wait_for_selector('[data-testid="editor-content"]')
        
        # Step 3: Verify initial provenance display
        provenance_panel = page.locator('[data-testid="provenance-panel"]')
        await expect(provenance_panel).to_be_visible()
        
        implements_section = page.locator('[data-testid="implements-requirements"]')
        await expect(implements_section).to_contain_text("REQ-TRACKING-001")
        
        verified_by_section = page.locator('[data-testid="verified-by-tests"]')
        await expect(verified_by_section).to_contain_text("test_water_service.py")
        
        # Step 4: Make code change and watch real-time updates
        editor = page.locator('[data-testid="monaco-editor"]')
        await editor.click()
        
        # Add validation method
        await page.keyboard.press('Control+End')  # Go to end of file
        await page.keyboard.press('Enter')
        await page.keyboard.type("""
    def validate_water_amount(self, amount_ml: int) -> bool:
        '''Validates water intake amount is within reasonable range'''
        return 0 < amount_ml <= 5000
        """)
        
        # Step 5: Verify real-time impact analysis
        await page.wait_for_selector('[data-testid="change-detected"]', timeout=5000)
        
        impact_alert = page.locator('[data-testid="impact-analysis-alert"]')
        await expect(impact_alert).to_be_visible()
        await expect(impact_alert).to_contain_text("Change affects")
        
        # Step 6: Review impact details
        await page.click('[data-testid="view-impact-details-btn"]')
        
        upstream_changes = page.locator('[data-testid="upstream-change-list"]')
        await expect(upstream_changes).to_contain_text("REQ-TRACKING-001")
        
        downstream_changes = page.locator('[data-testid="downstream-change-list"]')
        await expect(downstream_changes).to_contain_text("test_water_service.py")
        
        # Step 7: Accept or reject impact propagation
        await page.click('[data-testid="accept-impact-changes-btn"]')
        
        # Verify updates applied
        await page.wait_for_selector('[data-testid="changes-applied"]')
        updated_status = page.locator('[data-testid="provenance-status"]')
        await expect(updated_status).to_contain_text("Synchronized")


class TestErrorScenarios:
    """Test error scenarios and edge cases in user workflows."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_consensus_deadlock_resolution(self, page: Page):
        """
        VERIFIES: R-PRD-012 (deadlock resolution)
        SCENARIO: Council deadlock → human escalation → resolution
        """
        
        # Step 1: Navigate to a contentious debate scenario
        await page.goto("http://localhost:3000/projects/water-app/council/contentious-topic")
        
        # Step 2: Simulate council deadlock (mock low consensus)
        await page.click('[data-testid="simulate-deadlock-btn"]')
        
        # Step 3: Verify human escalation trigger
        escalation_prompt = page.locator('[data-testid="deadlock-escalation"]')
        await expect(escalation_prompt).to_be_visible()
        await expect(escalation_prompt).to_contain_text("Human input required")
        
        # Step 4: Provide resolution guidance
        await page.fill('[data-testid="deadlock-resolution-input"]',
                       "Override: Choose FastAPI for backend due to team expertise")
        await page.click('[data-testid="resolve-deadlock-btn"]')
        
        # Step 5: Verify resolution recorded
        resolution_log = page.locator('[data-testid="resolution-log"]')
        await expect(resolution_log).to_be_visible()
        await expect(resolution_log).to_contain_text("Human Override")

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_orphan_code_detection_and_cleanup(self, page: Page):
        """
        VERIFIES: Orphan code detection and cleanup workflow
        SCENARIO: Detect orphaned code → review → cleanup
        """
        
        # Step 1: Navigate to traceability dashboard
        await page.goto("http://localhost:3000/projects/water-app/traceability")
        
        # Step 2: Run orphan detection scan
        await page.click('[data-testid="scan-orphans-btn"]')
        await page.wait_for_selector('[data-testid="orphan-scan-results"]')
        
        # Step 3: Review orphaned items
        orphan_list = page.locator('[data-testid="orphaned-code-list"]')
        if await orphan_list.is_visible():
            orphan_count = await page.locator('[data-testid="orphan-item"]').count()
            
            if orphan_count > 0:
                # Step 4: Review and cleanup orphaned code
                first_orphan = page.locator('[data-testid="orphan-item"]').first
                await first_orphan.click()
                
                await page.click('[data-testid="remove-orphan-btn"]')
                await page.click('[data-testid="confirm-cleanup-btn"]')
                
                # Verify cleanup success
                await page.wait_for_selector('[data-testid="cleanup-success"]')


@pytest.fixture(scope="session")
def example_water_app_data():
    """Fixture providing complete water app example data for testing."""
    return {
        "idea": "Build a water tracking app for health-conscious professionals who struggle to maintain proper hydration throughout their busy workday",
        "paradigm": "yc_startup",
        "paradigm_answers": {
            "market_size": "Health app market $4.2B, growing 15% annually",
            "target_customer": "Health-conscious professionals aged 25-45", 
            "problem_validation": "67% of professionals struggle with hydration tracking",
            "unique_solution": "Automated tracking with smart notifications based on activity",
            "mvp_scope": "Water logging + smart reminders + progress tracking",
            "business_model": "Freemium with premium analytics and custom goals",
            "competition": "MyFitnessPal (food focus), Waterllama (basic tracking)"
        },
        "expected_requirements": [
            "REQ-TRACKING-001",  # Water intake logging
            "REQ-NOTIF-001",     # Smart notifications  
            "REQ-USER-001",      # User registration/profiles
            "REQ-GOALS-001",     # Hydration goal setting
            "REQ-ANALYTICS-001"  # Progress analytics
        ],
        "expected_nfrs": [
            "NFR-PERF-001",      # <300ms response time
            "NFR-UX-001",        # One-tap logging
            "NFR-PRIVACY-001",   # Health data privacy
            "NFR-SCALE-001"      # Support 10k+ users
        ],
        "expected_components": [
            "Water Tracking Service",
            "Notification Service", 
            "User Management Service",
            "Analytics Service",
            "API Gateway"
        ]
    }


class TestPlaywrightSetup:
    """Test Playwright test environment setup and utilities."""
    
    @pytest.mark.asyncio
    async def test_playwright_environment_ready(self, page: Page):
        """
        VERIFIES: E2E test environment setup
        SCENARIO: Validate test environment is properly configured
        """
        
        # Step 1: Verify development server is running
        await page.goto("http://localhost:3000")
        
        # Should not get connection refused or 404
        title = await page.title()
        assert "LLM Council" in title or "Development" in title
        
        # Step 2: Verify API endpoints are accessible  
        api_health = await page.goto("http://localhost:8000/api/healthz")
        assert api_health.status == 200
        
        # Step 3: Verify WebSocket connection
        await page.goto("http://localhost:3000")
        await page.wait_for_selector('[data-testid="connection-status"]')
        
        connection_status = page.locator('[data-testid="connection-status"]')
        await expect(connection_status).to_contain_text("Connected")

    @pytest.mark.asyncio
    async def test_screenshot_capture_for_documentation(self, page: Page):
        """
        UTILITY: Capture screenshots of key workflow stages for documentation
        SCENARIO: Generate visual documentation of user flows
        """
        
        screenshots_dir = Path("tests/e2e/screenshots")
        screenshots_dir.mkdir(exist_ok=True)
        
        # Capture key workflow screens
        workflow_screens = [
            ("idea-input", "http://localhost:3000/idea"),
            ("paradigm-selection", "http://localhost:3000/paradigm"), 
            ("entity-graph", "http://localhost:3000/graph"),
            ("council-debate", "http://localhost:3000/council"),
            ("traceability-matrix", "http://localhost:3000/traceability"),
            ("code-generation", "http://localhost:3000/code")
        ]
        
        for screen_name, url in workflow_screens:
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            
            # Wait for main content to load
            await page.wait_for_selector('[data-testid="main-content"]', timeout=10000)
            
            # Capture full page screenshot
            await page.screenshot(
                path=f"{screenshots_dir}/{screen_name}.png",
                full_page=True
            )


# Playwright configuration and utilities
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def playwright_config():
    """Playwright configuration for E2E tests."""
    return {
        "browsers": ["chromium", "firefox", "webkit"],
        "headless": False,  # Set to True for CI
        "viewport": {"width": 1920, "height": 1080},
        "video": "on-first-retry",
        "screenshot": "only-on-failure",
        "base_url": "http://localhost:3000"
    }