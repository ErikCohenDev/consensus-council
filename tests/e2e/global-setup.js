/**
 * Playwright Global Setup
 * 
 * VERIFIES: E2E test environment preparation
 * SCENARIO: Set up test data, user accounts, and environment state
 */

import { chromium } from '@playwright/test';

async function globalSetup() {
  console.log('🚀 Setting up E2E test environment...');
  
  // Launch browser for setup
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Step 1: Verify backend services are running
    console.log('📡 Checking backend health...');
    await page.goto('http://localhost:8000/api/healthz');
    const healthResponse = await page.textContent('body');
    
    if (!healthResponse.includes('healthy') && !healthResponse.includes('ok')) {
      throw new Error('Backend health check failed');
    }
    
    // Step 2: Verify frontend is accessible
    console.log('🌐 Checking frontend availability...');
    await page.goto('http://localhost:3000');
    await page.waitForSelector('[data-testid="app-root"]', { timeout: 30000 });
    
    // Step 3: Set up test project data
    console.log('📊 Creating test project data...');
    
    // Create water tracking app test project
    const testProjectData = {
      project_id: 'e2e-water-app',
      name: 'Water Tracking App (E2E Test)',
      idea: 'Build a water tracking app for health-conscious professionals',
      paradigm: 'yc_startup',
      status: 'initialized',
      created_at: new Date().toISOString()
    };
    
    // Store test data in localStorage for tests to use
    await page.evaluate((data) => {
      localStorage.setItem('e2e_test_project', JSON.stringify(data));
    }, testProjectData);
    
    // Step 4: Set up mock API responses for consistent testing
    await page.route('**/api/ideas/extract-context', async route => {
      const mockEntities = {
        entities: [
          {
            id: 'prob_001',
            label: 'Hydration Tracking Difficulty',
            type: 'problem',
            description: 'Professionals struggle to track water intake consistently',
            importance: 0.9,
            certainty: 0.8
          },
          {
            id: 'user_001', 
            label: 'Health-conscious Professionals',
            type: 'target_user',
            description: 'Working professionals aged 25-45 who prioritize health',
            importance: 0.85,
            certainty: 0.9
          },
          {
            id: 'sol_001',
            label: 'Automated Water Tracking',
            type: 'solution', 
            description: 'Smart app that tracks water intake with minimal user effort',
            importance: 0.8,
            certainty: 0.7
          }
        ],
        relationships: [
          {
            id: 'rel_001',
            source_id: 'prob_001',
            target_id: 'user_001',
            type: 'affects',
            label: 'problem affects user group',
            strength: 0.9
          },
          {
            id: 'rel_002',
            source_id: 'sol_001', 
            target_id: 'prob_001',
            type: 'solves',
            label: 'solution addresses problem',
            strength: 0.85
          }
        ]
      };
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockEntities)
      });
    });
    
    // Step 5: Set up paradigm framework mock responses
    await page.route('**/api/paradigms/yc_startup/questions', async route => {
      const mockQuestions = [
        {
          question_id: 'market_size',
          text: 'What is the total addressable market (TAM) for your solution?',
          type: 'market_analysis',
          weight: 2.0,
          human_input_required: true
        },
        {
          question_id: 'problem_validation',
          text: 'How do you know this problem is worth solving?',
          type: 'problem_validation', 
          weight: 2.2,
          human_input_required: true
        },
        {
          question_id: 'unique_insight',
          text: 'What unique insight do you have that others missed?',
          type: 'strategic',
          weight: 1.8,
          human_input_required: true
        }
      ];
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ questions: mockQuestions })
      });
    });
    
    // Step 6: Verify test data persistence
    const storedData = await page.evaluate(() => {
      return localStorage.getItem('e2e_test_project');
    });
    
    if (!storedData) {
      throw new Error('Failed to store test project data');
    }
    
    console.log('✅ E2E test environment setup complete');
    
  } catch (error) {
    console.error('❌ E2E setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;