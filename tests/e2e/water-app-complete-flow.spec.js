/**
 * Complete Water App User Flow - Playwright E2E Tests
 * 
 * VERIFIES: Complete user journey from idea input to code generation
 * VALIDATES: UC-001→UC-010 (all user workflow scenarios)
 * TEST_SCENARIO: Water tracking app for health-conscious professionals
 * EXPECTED_DURATION: ~15 minutes full flow
 * BROWSERS: Chrome, Firefox, Safari
 */

import { test, expect } from '@playwright/test';

test.describe('Complete Water App User Flow', () => {
  
  test.beforeEach(async ({ page }) => {
    // Load test project data
    await page.goto('/');
    
    const testProjectData = await page.evaluate(() => {
      return JSON.parse(localStorage.getItem('e2e_test_project') || '{}');
    });
    
    expect(testProjectData.project_id).toBe('e2e-water-app');
  });

  test('UC-001: Idea Input → Paradigm Selection → Entity Extraction', async ({ page }) => {
    /**
     * VERIFIES: R-PRD-016 (paradigm engine), UC-001 (idea to vision start)
     * SCENARIO: User enters idea → selects YC framework → sees entity graph
     * DURATION: ~2 minutes
     */
    
    // Step 1: Navigate to new project page
    await page.goto('/');
    await page.click('[data-testid="new-project-btn"]');
    await expect(page).toHaveURL(/\/projects\/new/);
    
    // Step 2: Enter water tracking app idea
    const ideaText = `
      Build a water tracking app for health-conscious professionals who struggle 
      to maintain proper hydration throughout their busy workday. The app should 
      send smart reminders based on activity level, weather, and personal goals.
      Target: working professionals aged 25-45 who care about health but have limited time.
    `;
    
    await page.fill('[data-testid="idea-input-textarea"]', ideaText);
    await expect(page.locator('[data-testid="idea-input-textarea"]')).toHaveValue(ideaText);
    
    // Step 3: Analyze idea and extract entities
    await page.click('[data-testid="analyze-idea-btn"]');
    await page.waitForSelector('[data-testid="entity-extraction-progress"]');
    
    // Wait for entity extraction completion
    await page.waitForSelector('[data-testid="entity-extraction-complete"]', { timeout: 30000 });
    
    // Step 4: Verify extracted entities are displayed
    const problemEntity = page.locator('[data-testid="entity-problem"]');
    await expect(problemEntity).toBeVisible();
    await expect(problemEntity).toContainText('hydration');
    
    const userEntity = page.locator('[data-testid="entity-target-user"]');
    await expect(userEntity).toBeVisible();
    await expect(userEntity).toContainText('professionals');
    
    const solutionEntity = page.locator('[data-testid="entity-solution"]');
    await expect(solutionEntity).toBeVisible();
    await expect(solutionEntity).toContainText('tracking');
    
    // Step 5: Select YC Startup paradigm
    await page.click('[data-testid="select-paradigm-btn"]');
    await page.waitForSelector('[data-testid="paradigm-selector"]');
    
    await page.click('[data-testid="paradigm-yc-startup"]');
    await expect(page.locator('[data-testid="selected-paradigm"]')).toContainText('YC Startup');
    
    await page.click('[data-testid="confirm-paradigm-btn"]');
    
    // Step 6: Verify paradigm-specific questions appear
    await page.waitForSelector('[data-testid="paradigm-questions"]');
    
    const marketQuestion = page.locator('[data-testid="question-market-size"]');
    await expect(marketQuestion).toBeVisible();
    await expect(marketQuestion).toContainText('market');
    
    const problemQuestion = page.locator('[data-testid="question-problem-validation"]');
    await expect(problemQuestion).toBeVisible();
    await expect(problemQuestion).toContainText('problem');
    
    // Step 7: Take screenshot for documentation
    await page.screenshot({ 
      path: 'tests/e2e/screenshots/01-paradigm-questions.png',
      fullPage: true 
    });
  });

  test('UC-002: Paradigm Questions → Research Expansion → Context Graph', async ({ page }) => {
    /**
     * VERIFIES: Research expansion and context graph generation
     * SCENARIO: Answer YC questions → trigger research → see enriched graph
     * PREREQUISITE: Completed UC-001 (idea input and paradigm selection)
     * DURATION: ~3 minutes
     */
    
    // Navigate to paradigm questions page (assume previous step completed)
    await page.goto('/projects/e2e-water-app/paradigm-questions');
    await page.waitForSelector('[data-testid="paradigm-questions"]');
    
    // Step 1: Answer YC paradigm questions
    const paradigmAnswers = {
      'market-size': 'Health app market $4.2B globally, growing 15% annually',
      'problem-validation': '67% of professionals struggle with hydration tracking (survey 500 users)',
      'target-customer': 'Health-conscious working professionals aged 25-45 in urban areas',
      'unique-insight': 'Automated tracking reduces friction vs manual logging apps',
      'mvp-scope': 'Water logging + smart reminders + basic progress tracking',
      'business-model': 'Freemium: free basic tracking, premium analytics $4.99/month'
    };
    
    for (const [questionId, answer] of Object.entries(paradigmAnswers)) {
      await page.fill(`[data-testid="answer-${questionId}"]`, answer);
    }
    
    // Step 2: Submit answers and trigger research expansion
    await page.click('[data-testid="submit-paradigm-answers-btn"]');
    await page.waitForSelector('[data-testid="research-expansion-progress"]');
    
    // Step 3: Wait for research completion
    await page.waitForSelector('[data-testid="research-expansion-complete"]', { timeout: 60000 });
    
    // Step 4: Verify research insights added to context
    const researchInsights = page.locator('[data-testid="research-insights"]');
    await expect(researchInsights).toBeVisible();
    
    const marketInsight = page.locator('[data-testid="insight-market-analysis"]');
    await expect(marketInsight).toBeVisible();
    await expect(marketInsight).toContainText('market');
    
    const competitionInsight = page.locator('[data-testid="insight-competition"]');
    await expect(competitionInsight).toBeVisible();
    
    // Step 5: Navigate to enhanced context graph
    await page.click('[data-testid="view-context-graph-btn"]');
    await page.waitForSelector('[data-testid="context-graph-canvas"]');
    
    // Step 6: Verify graph visualization
    const graphCanvas = page.locator('[data-testid="context-graph-canvas"]');
    await expect(graphCanvas).toBeVisible();
    
    // Verify entity nodes are rendered
    const entityNodes = page.locator('[data-testid^="graph-node-"]');
    await expect(entityNodes).toHaveCountGreaterThan(5); // Original + research entities
    
    // Verify relationship edges are rendered
    const relationshipEdges = page.locator('[data-testid^="graph-edge-"]');
    await expect(relationshipEdges).toHaveCountGreaterThan(3);
    
    // Step 7: Test graph interactivity
    const problemNode = page.locator('[data-testid="graph-node-prob_001"]');
    await problemNode.click();
    
    // Verify node details panel appears
    const nodeDetails = page.locator('[data-testid="node-details-panel"]');
    await expect(nodeDetails).toBeVisible();
    await expect(nodeDetails).toContainText('Hydration Tracking Difficulty');
    
    // Step 8: Take screenshot for documentation
    await page.screenshot({ 
      path: 'tests/e2e/screenshots/02-context-graph.png',
      fullPage: true 
    });
  });

  test('UC-003: Vision Generation → Council Debate → Consensus', async ({ page }) => {
    /**
     * VERIFIES: R-PRD-011→R-PRD-012 (human review + consensus), UC-003 (vision generation)
     * SCENARIO: Generate vision → council debate → human input → consensus reached
     * PREREQUISITE: Completed UC-002 (context graph ready)
     * DURATION: ~4 minutes
     */
    
    // Navigate to vision generation
    await page.goto('/projects/e2e-water-app/vision');
    await page.waitForSelector('[data-testid="generate-vision-btn"]');
    
    // Step 1: Initiate vision generation
    await page.click('[data-testid="generate-vision-btn"]');
    await page.waitForSelector('[data-testid="council-debate-chamber"]');
    
    // Step 2: Monitor council member responses
    await page.waitForSelector('[data-testid="council-member-pm"]', { timeout: 60000 });
    const pmResponse = page.locator('[data-testid="council-member-pm"] [data-testid="response-content"]');
    await expect(pmResponse).toBeVisible();
    await expect(pmResponse).toContainText('market'); // PM should mention market
    
    await page.waitForSelector('[data-testid="council-member-security"]', { timeout: 30000 });
    const securityResponse = page.locator('[data-testid="council-member-security"] [data-testid="response-content"]');
    await expect(securityResponse).toBeVisible();
    
    // Step 3: Check consensus meter
    const consensusMeter = page.locator('[data-testid="consensus-meter"]');
    await expect(consensusMeter).toBeVisible();
    
    const consensusScore = await page.locator('[data-testid="consensus-score"]').textContent();
    const score = parseFloat(consensusScore.split('/')[0]);
    
    // Step 4: Handle human input if consensus is low
    if (score < 3.8) {
      const humanPrompt = page.locator('[data-testid="human-input-prompt"]');
      await expect(humanPrompt).toBeVisible();
      
      // Provide strategic context
      await page.fill('[data-testid="human-context-input"]', `
        Team context: 2 full-stack developers with React/Python experience
        Budget: $50k development budget, $500/month operational
        Timeline: 3-month MVP target for beta launch
        Market validation: Conducted 50 user interviews, 78% expressed interest
        Risk tolerance: Medium - need to validate quickly but avoid major failures
      `);
      
      await page.click('[data-testid="submit-human-context-btn"]');
      
      // Wait for consensus re-evaluation
      await page.waitForSelector('[data-testid="consensus-updated"]', { timeout: 120000 });
    }
    
    // Step 5: Verify final consensus reached
    await page.waitForSelector('[data-testid="consensus-reached"]');
    const finalConsensus = await page.locator('[data-testid="final-consensus-score"]').textContent();
    const finalScore = parseFloat(finalConsensus.split('/')[0]);
    expect(finalScore).toBeGreaterThanOrEqual(3.8);
    
    // Step 6: Generate vision document
    await page.click('[data-testid="generate-vision-document-btn"]');
    await page.waitForSelector('[data-testid="vision-document-generated"]');
    
    // Step 7: Verify vision document content
    const visionContent = page.locator('[data-testid="vision-document-content"]');
    await expect(visionContent).toBeVisible();
    await expect(visionContent).toContainText('Problem & JTBD');
    await expect(visionContent).toContainText('Target users');
    await expect(visionContent).toContainText('professionals');
    await expect(visionContent).toContainText('hydration');
    
    // Step 8: Take screenshot for documentation
    await page.screenshot({ 
      path: 'tests/e2e/screenshots/03-vision-consensus.png',
      fullPage: true 
    });
  });

  test('UC-004: PRD Generation → Hierarchical Requirements → Spec Creation', async ({ page }) => {
    /**
     * VERIFIES: R-PRD-017 (spec generation), UC-002 (vision to PRD)
     * SCENARIO: Vision → hierarchical PRD → REQ/NFR YAML specifications
     * PREREQUISITE: Vision document exists
     * DURATION: ~3 minutes
     */
    
    // Navigate to PRD generation
    await page.goto('/projects/e2e-water-app/prd');
    await page.waitForSelector('[data-testid="generate-prd-btn"]');
    
    // Step 1: Generate PRD from vision
    await page.click('[data-testid="generate-prd-btn"]');
    await page.waitForSelector('[data-testid="prd-generation-progress"]');
    
    // Step 2: Wait for hierarchical PRD structure
    await page.waitForSelector('[data-testid="hierarchical-prd-complete"]', { timeout: 90000 });
    
    // Step 3: Verify main PRD document
    const mainPrd = page.locator('[data-testid="main-prd-document"]');
    await expect(mainPrd).toBeVisible();
    await expect(mainPrd).toContainText('## Goals & Non-Goals');
    
    // Step 4: Verify sub-PRD generation
    const subPrdList = page.locator('[data-testid="sub-prd-list"]');
    await expect(subPrdList).toBeVisible();
    
    const trackingPrd = page.locator('[data-testid="sub-prd-FRS-TRACKING-001"]');
    await expect(trackingPrd).toBeVisible();
    await expect(trackingPrd).toContainText('Water Tracking');
    
    const notificationPrd = page.locator('[data-testid="sub-prd-FRS-NOTIF-002"]');
    await expect(notificationPrd).toBeVisible();
    await expect(notificationPrd).toContainText('Notification');
    
    // Step 5: Generate specifications from PRD
    await page.click('[data-testid="generate-specifications-btn"]');
    await page.waitForSelector('[data-testid="spec-generation-complete"]');
    
    // Step 6: Verify REQ YAML files generated
    const reqSpecList = page.locator('[data-testid="req-specifications"]');
    await expect(reqSpecList).toBeVisible();
    
    const trackingReq = page.locator('[data-testid="spec-REQ-TRACKING-001"]');
    await expect(trackingReq).toBeVisible();
    await trackingReq.click();
    
    // Verify YAML structure
    const reqContent = page.locator('[data-testid="spec-content"]');
    await expect(reqContent).toContainText('id: REQ-TRACKING-001');
    await expect(reqContent).toContainText('acceptance_criteria:');
    await expect(reqContent).toContainText('source_documents:');
    
    // Step 7: Verify NFR YAML files generated
    const nfrSpecList = page.locator('[data-testid="nfr-specifications"]');
    await expect(nfrSpecList).toBeVisible();
    
    const perfNfr = page.locator('[data-testid="spec-NFR-PERF-001"]');
    await expect(perfNfr).toBeVisible();
    await expect(perfNfr).toContainText('Performance');
    
    // Step 8: Take screenshot for documentation
    await page.screenshot({ 
      path: 'tests/e2e/screenshots/04-prd-specifications.png',
      fullPage: true 
    });
  });

  test('UC-005: Architecture → Implementation → Code Generation', async ({ page }) => {
    /**
     * VERIFIES: R-PRD-018→R-PRD-019 (code generation + provenance)
     * SCENARIO: Architecture design → implementation tasks → code stubs with provenance
     * PREREQUISITE: PRD and specifications exist
     * DURATION: ~4 minutes
     */
    
    // Navigate to architecture design
    await page.goto('/projects/e2e-water-app/architecture');
    await page.waitForSelector('[data-testid="generate-architecture-btn"]');
    
    // Step 1: Generate architecture from PRD
    await page.click('[data-testid="generate-architecture-btn"]');
    await page.waitForSelector('[data-testid="architecture-generation-progress"]');
    
    // Step 2: Wait for architecture completion
    await page.waitForSelector('[data-testid="architecture-complete"]', { timeout: 90000 });
    
    // Step 3: Verify architecture components
    const componentDiagram = page.locator('[data-testid="component-diagram"]');
    await expect(componentDiagram).toBeVisible();
    
    const waterService = page.locator('[data-testid="component-water-service"]');
    await expect(waterService).toBeVisible();
    
    const notificationService = page.locator('[data-testid="component-notification-service"]');
    await expect(notificationService).toBeVisible();
    
    // Step 4: Navigate to implementation planning
    await page.click('[data-testid="proceed-to-implementation-btn"]');
    await page.waitForSelector('[data-testid="implementation-tasks"]');
    
    // Step 5: Review generated implementation tasks
    const taskList = page.locator('[data-testid="implementation-task"]');
    await expect(taskList).toHaveCountGreaterThan(5);
    
    // Verify task details
    const authTask = page.locator('[data-testid="task-T-AUTH-001"]');
    await expect(authTask).toBeVisible();
    await expect(authTask).toContainText('authentication');
    
    const trackingTask = page.locator('[data-testid="task-T-TRACKING-001"]');
    await expect(trackingTask).toBeVisible();
    await expect(trackingTask).toContainText('water');
    
    // Step 6: Generate code stubs
    await page.click('[data-testid="generate-code-stubs-btn"]');
    await page.waitForSelector('[data-testid="code-generation-progress"]');
    
    // Step 7: Wait for code generation completion
    await page.waitForSelector('[data-testid="code-generation-complete"]', { timeout: 180000 });
    
    // Step 8: Verify generated file structure
    const fileTree = page.locator('[data-testid="generated-file-tree"]');
    await expect(fileTree).toBeVisible();
    
    // Expand services folder
    await page.click('[data-testid="folder-services"]');
    
    const waterServiceFile = page.locator('[data-testid="file-water_service.py"]');
    await expect(waterServiceFile).toBeVisible();
    
    const authServiceFile = page.locator('[data-testid="file-auth_service.py"]');
    await expect(authServiceFile).toBeVisible();
    
    // Step 9: Verify provenance headers in generated code
    await waterServiceFile.click();
    
    const fileContent = page.locator('[data-testid="file-content-display"]');
    await expect(fileContent).toBeVisible();
    await expect(fileContent).toContainText('IMPLEMENTS:');
    await expect(fileContent).toContainText('REQ-TRACKING-001');
    await expect(fileContent).toContainText('VERIFIED_BY:');
    await expect(fileContent).toContainText('test_water_service.py');
    
    // Step 10: Take screenshot for documentation
    await page.screenshot({ 
      path: 'tests/e2e/screenshots/05-code-generation.png',
      fullPage: true 
    });
  });

  test('UC-006: Change Impact Analysis → Traceability Matrix', async ({ page }) => {
    /**
     * VERIFIES: R-PRD-020→R-PRD-021 (traceability + impact analysis)
     * SCENARIO: Code change → impact analysis → traceability matrix update
     * PREREQUISITE: Code has been generated
     * DURATION: ~3 minutes
     */
    
    // Navigate to code editor with traceability
    await page.goto('/projects/e2e-water-app/code-editor');
    await page.waitForSelector('[data-testid="code-editor"]');
    
    // Step 1: Open water service file
    await page.click('[data-testid="file-water_service.py"]');
    await page.waitForSelector('[data-testid="monaco-editor"]');
    
    // Step 2: Verify initial traceability display
    const traceabilityPanel = page.locator('[data-testid="traceability-panel"]');
    await expect(traceabilityPanel).toBeVisible();
    
    const implementsSection = page.locator('[data-testid="implements-requirements"]');
    await expect(implementsSection).toContainText('REQ-TRACKING-001');
    
    // Step 3: Make a code change
    const editor = page.locator('[data-testid="monaco-editor"]');
    await editor.click({ position: { x: 100, y: 100 } });
    
    // Add validation method
    await page.keyboard.press('Control+End');
    await page.keyboard.press('Enter');
    await page.keyboard.type(`
    def validate_water_amount(self, amount_ml: int) -> bool:
        """Validate water intake amount is within reasonable range"""
        if amount_ml <= 0:
            raise ValueError("Water amount must be positive")
        if amount_ml > 5000:  # 5 liters max reasonable intake
            raise ValueError("Water amount exceeds reasonable limit")
        return True
    `);
    
    // Step 4: Trigger impact analysis
    await page.keyboard.press('Control+S'); // Save triggers analysis
    await page.waitForSelector('[data-testid="change-impact-detected"]');
    
    // Step 5: Verify impact analysis results
    const impactPanel = page.locator('[data-testid="impact-analysis-panel"]');
    await expect(impactPanel).toBeVisible();
    
    const upstreamImpacts = page.locator('[data-testid="upstream-impacts"]');
    await expect(upstreamImpacts).toContainText('REQ-TRACKING-001');
    await expect(upstreamImpacts).toContainText('PRD.md');
    
    const downstreamImpacts = page.locator('[data-testid="downstream-impacts"]');
    await expect(downstreamImpacts).toContainText('test_water_service.py');
    
    // Step 6: View traceability matrix
    await page.click('[data-testid="view-traceability-matrix-btn"]');
    await page.waitForSelector('[data-testid="traceability-matrix-table"]');
    
    // Step 7: Verify matrix shows updated relationships
    const matrixTable = page.locator('[data-testid="traceability-matrix-table"]');
    await expect(matrixTable).toBeVisible();
    
    const reqRow = page.locator('[data-testid="matrix-row-REQ-TRACKING-001"]');
    await expect(reqRow).toBeVisible();
    await expect(reqRow).toContainText('water_service.py');
    await expect(reqRow).toContainText('test_water_service.py');
    
    // Step 8: Check coverage percentage
    const coverageIndicator = reqRow.locator('[data-testid="coverage-percentage"]');
    const coverageText = await coverageIndicator.textContent();
    const coverage = parseFloat(coverageText.replace('%', ''));
    expect(coverage).toBeGreaterThan(0);
    
    // Step 9: Take screenshot for documentation
    await page.screenshot({ 
      path: 'tests/e2e/screenshots/06-traceability-matrix.png',
      fullPage: true 
    });
  });

  test('UC-007: Orphan Detection → Symmetry Validation', async ({ page }) => {
    /**
     * VERIFIES: Orphan code detection and symmetry enforcement
     * SCENARIO: Detect orphaned code/requirements → cleanup → validate symmetry
     * DURATION: ~2 minutes
     */
    
    // Navigate to symmetry validation dashboard
    await page.goto('/projects/e2e-water-app/symmetry');
    await page.waitForSelector('[data-testid="symmetry-dashboard"]');
    
    // Step 1: Run orphan detection scan
    await page.click('[data-testid="scan-orphans-btn"]');
    await page.waitForSelector('[data-testid="orphan-scan-complete"]');
    
    // Step 2: Review orphan detection results
    const orphanResults = page.locator('[data-testid="orphan-detection-results"]');
    await expect(orphanResults).toBeVisible();
    
    const orphanedCode = page.locator('[data-testid="orphaned-code-list"]');
    const orphanedReqs = page.locator('[data-testid="orphaned-requirements-list"]');
    
    // Step 3: Check symmetry score
    const symmetryScore = page.locator('[data-testid="symmetry-score"]');
    await expect(symmetryScore).toBeVisible();
    
    const scoreText = await symmetryScore.textContent();
    const score = parseFloat(scoreText.split(':')[1].trim());
    
    // Step 4: If orphans found, test cleanup process
    const orphanCount = await page.locator('[data-testid="orphan-item"]').count();
    
    if (orphanCount > 0) {
      // Select first orphaned item
      await page.click('[data-testid="orphan-item"]:first-child');
      
      // Review orphan details
      const orphanDetails = page.locator('[data-testid="orphan-details-panel"]');
      await expect(orphanDetails).toBeVisible();
      
      // Choose cleanup action
      await page.click('[data-testid="cleanup-orphan-btn"]');
      await page.click('[data-testid="confirm-cleanup-btn"]');
      
      // Verify cleanup success
      await page.waitForSelector('[data-testid="cleanup-complete"]');
    }
    
    // Step 5: Verify final symmetry status
    await page.click('[data-testid="refresh-symmetry-btn"]');
    await page.waitForSelector('[data-testid="symmetry-updated"]');
    
    const finalSymmetryScore = page.locator('[data-testid="final-symmetry-score"]');
    const finalScoreText = await finalSymmetryScore.textContent();
    const finalScore = parseFloat(finalScoreText.split(':')[1].trim());
    
    expect(finalScore).toBeGreaterThanOrEqual(0.85); // High symmetry target
    
    // Step 6: Take screenshot for documentation
    await page.screenshot({ 
      path: 'tests/e2e/screenshots/07-symmetry-validation.png',
      fullPage: true 
    });
  });

  test('UC-008: Complete Pipeline Validation → Export Artifacts', async ({ page }) => {
    /**
     * VERIFIES: Complete pipeline validation and artifact export
     * SCENARIO: Validate entire pipeline → export all artifacts → verify completeness
     * PREREQUISITE: Complete pipeline has been executed
     * DURATION: ~2 minutes
     */
    
    // Navigate to pipeline overview
    await page.goto('/projects/e2e-water-app/overview');
    await page.waitForSelector('[data-testid="pipeline-overview"]');
    
    // Step 1: Verify all pipeline layers completed
    const layerStatuses = [
      'paradigm-complete',
      'context-complete', 
      'vision-complete',
      'prd-complete',
      'architecture-complete',
      'implementation-complete',
      'code-complete',
      'tests-complete'
    ];
    
    for (const layerStatus of layerStatuses) {
      const statusIndicator = page.locator(`[data-testid="${layerStatus}"]`);
      await expect(statusIndicator).toBeVisible();
      await expect(statusIndicator).toHaveClass(/success|complete/);
    }
    
    // Step 2: Run complete pipeline validation
    await page.click('[data-testid="validate-complete-pipeline-btn"]');
    await page.waitForSelector('[data-testid="pipeline-validation-complete"]');
    
    // Step 3: Verify validation results
    const validationResults = page.locator('[data-testid="pipeline-validation-results"]');
    await expect(validationResults).toBeVisible();
    
    const coverageScore = page.locator('[data-testid="requirement-coverage-score"]');
    const coverageText = await coverageScore.textContent();
    const coverage = parseFloat(coverageText.replace('%', ''));
    expect(coverage).toBeGreaterThanOrEqual(90);
    
    // Step 4: Export complete artifact set
    await page.click('[data-testid="export-artifacts-btn"]');
    await page.waitForSelector('[data-testid="export-options"]');
    
    // Select export formats
    await page.check('[data-testid="export-documents"]');
    await page.check('[data-testid="export-specifications"]');
    await page.check('[data-testid="export-code"]');
    await page.check('[data-testid="export-traceability-matrix"]');
    
    await page.click('[data-testid="confirm-export-btn"]');
    
    // Step 5: Verify export completion
    await page.waitForSelector('[data-testid="export-complete"]', { timeout: 30000 });
    
    const exportSummary = page.locator('[data-testid="export-summary"]');
    await expect(exportSummary).toBeVisible();
    await expect(exportSummary).toContainText('documents');
    await expect(exportSummary).toContainText('specifications');
    await expect(exportSummary).toContainText('code files');
    
    // Step 6: Verify download links
    const downloadLinks = page.locator('[data-testid="download-link"]');
    await expect(downloadLinks).toHaveCountGreaterThan(3);
    
    // Step 7: Take final screenshot
    await page.screenshot({ 
      path: 'tests/e2e/screenshots/08-pipeline-complete.png',
      fullPage: true 
    });
  });

  test('UC-009: Error Scenarios → Recovery Workflows', async ({ page }) => {
    /**
     * VERIFIES: Error handling and recovery mechanisms
     * SCENARIO: Simulate failures → test recovery → validate system resilience
     * DURATION: ~3 minutes
     */
    
    // Navigate to a new test project for error scenarios
    await page.goto('/projects/new');
    await page.fill('[data-testid="idea-input-textarea"]', 'Test idea for error scenarios');
    
    // Step 1: Simulate LLM API failure during entity extraction
    await page.route('**/api/ideas/extract-context', route => route.abort());
    
    await page.click('[data-testid="analyze-idea-btn"]');
    
    // Step 2: Verify error handling
    await page.waitForSelector('[data-testid="extraction-error"]', { timeout: 30000 });
    const errorMessage = page.locator('[data-testid="error-message"]');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('failed');
    
    // Step 3: Test retry mechanism
    await page.unroute('**/api/ideas/extract-context'); // Remove route block
    await page.click('[data-testid="retry-extraction-btn"]');
    
    // Step 4: Verify recovery success
    await page.waitForSelector('[data-testid="entity-extraction-complete"]', { timeout: 30000 });
    
    // Step 5: Simulate consensus deadlock
    await page.goto('/projects/e2e-water-app/council');
    
    // Mock low consensus scores to trigger deadlock
    await page.route('**/api/council/debate', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          consensus_score: 2.1,  // Very low consensus
          requires_human_input: true,
          deadlock_detected: true
        })
      });
    });
    
    await page.click('[data-testid="start-debate-btn"]');
    
    // Step 6: Verify deadlock escalation
    await page.waitForSelector('[data-testid="deadlock-escalation"]');
    const escalationPrompt = page.locator('[data-testid="deadlock-message"]');
    await expect(escalationPrompt).toContainText('Human input required');
    
    // Step 7: Provide deadlock resolution
    await page.fill('[data-testid="deadlock-resolution-input"]',
                   'Override: Proceed with FastAPI backend due to team expertise');
    await page.click('[data-testid="resolve-deadlock-btn"]');
    
    // Step 8: Verify resolution logged
    await page.waitForSelector('[data-testid="deadlock-resolved"]');
    const resolutionLog = page.locator('[data-testid="resolution-log-entry"]');
    await expect(resolutionLog).toContainText('Human Override');
    await expect(resolutionLog).toContainText('FastAPI');
  });

});

test.describe('Cross-Browser Compatibility', () => {
  
  test('Key workflows work across all browsers', async ({ page, browserName }) => {
    /**
     * VERIFIES: Cross-browser compatibility for core workflows
     * SCENARIO: Test core functionality on Chrome, Firefox, Safari
     */
    
    console.log(`Testing on ${browserName}`);
    
    // Test basic navigation and core interactions
    await page.goto('/');
    await expect(page.locator('[data-testid="app-root"]')).toBeVisible();
    
    // Test idea input (critical path)
    await page.click('[data-testid="new-project-btn"]');
    await page.fill('[data-testid="idea-input-textarea"]', 'Cross-browser test idea');
    await page.click('[data-testid="analyze-idea-btn"]');
    
    // Verify entity extraction works across browsers
    await page.waitForSelector('[data-testid="entity-extraction-complete"]', { timeout: 30000 });
    const entities = page.locator('[data-testid^="entity-"]');
    await expect(entities).toHaveCountGreaterThan(2);
    
    // Test graph visualization (WebGL/Canvas compatibility)
    await page.click('[data-testid="view-context-graph-btn"]');
    const graphCanvas = page.locator('[data-testid="context-graph-canvas"]');
    await expect(graphCanvas).toBeVisible();
    
    // Verify graph interactivity works
    const firstNode = page.locator('[data-testid^="graph-node-"]').first();
    await firstNode.click();
    
    const nodeDetails = page.locator('[data-testid="node-details-panel"]');
    await expect(nodeDetails).toBeVisible();
  });

});

test.describe('Performance Validation', () => {
  
  test('Pipeline performance meets SLA requirements', async ({ page }) => {
    /**
     * VERIFIES: Performance SLAs for complete user workflows
     * SCENARIO: Measure workflow timing against documented targets
     */
    
    const startTime = Date.now();
    
    // Execute core workflow with timing
    await page.goto('/projects/new');
    
    const ideaInputTime = Date.now();
    await page.fill('[data-testid="idea-input-textarea"]', 'Performance test water tracking app');
    await page.click('[data-testid="analyze-idea-btn"]');
    
    await page.waitForSelector('[data-testid="entity-extraction-complete"]');
    const entityExtractionTime = Date.now();
    
    await page.click('[data-testid="select-paradigm-btn"]');
    await page.click('[data-testid="paradigm-yc-startup"]');
    await page.click('[data-testid="confirm-paradigm-btn"]');
    
    const paradigmSelectionTime = Date.now();
    
    // Verify timing meets SLA targets from VISION.md
    const entityExtractionDuration = (entityExtractionTime - ideaInputTime) / 1000;
    const paradigmSelectionDuration = (paradigmSelectionTime - entityExtractionTime) / 1000;
    
    // SLA: Entity extraction ≤ 30 seconds
    expect(entityExtractionDuration).toBeLessThanOrEqual(30);
    
    // SLA: Paradigm selection ≤ 5 seconds  
    expect(paradigmSelectionDuration).toBeLessThanOrEqual(5);
    
    console.log(`Performance: Entity extraction ${entityExtractionDuration}s, Paradigm selection ${paradigmSelectionDuration}s`);
  });

});