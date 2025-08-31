#!/usr/bin/env python3
"""Smoke test for basic system functionality.

This script runs basic smoke tests to verify core components work
before running the full E2E test suite.

Usage:
    python scripts/smoke-test.py
    python scripts/smoke-test.py --verbose
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmokeTestRunner:
    """Basic smoke tests for core system components."""
    
    def __init__(self):
        self.test_results = {}
    
    def run_smoke_tests(self, verbose: bool = False) -> bool:
        """Run all smoke tests."""
        
        logger.info("🔥 Running Smoke Tests for Idea Operating System")
        logger.info("=" * 60)
        
        tests = [
            ("Import Core Modules", self._test_core_imports),
            ("Model Validation", self._test_model_validation),
            ("Service Initialization", self._test_service_initialization),
            ("Config Loading", self._test_config_loading),
            ("Schema Validation", self._test_schema_validation)
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            logger.info(f"🧪 Running: {test_name}")
            
            try:
                result = test_func()
                self.test_results[test_name] = {"success": True, "result": result}
                logger.info(f"   ✅ {test_name} PASSED")
                
                if verbose and result:
                    logger.info(f"      Result: {result}")
                    
            except Exception as e:
                self.test_results[test_name] = {"success": False, "error": str(e)}
                logger.error(f"   ❌ {test_name} FAILED: {e}")
                all_passed = False
        
        # Summary
        logger.info("=" * 60)
        passed_count = len([r for r in self.test_results.values() if r["success"]])
        total_count = len(self.test_results)
        
        if all_passed:
            logger.info(f"🎉 All smoke tests PASSED ({passed_count}/{total_count})")
            logger.info("✅ Core system components are functional")
        else:
            logger.error(f"❌ Smoke tests FAILED ({passed_count}/{total_count})")
            logger.error("🔧 Please fix core issues before running E2E tests")
        
        return all_passed
    
    def _test_core_imports(self) -> str:
        """Test that core modules can be imported."""
        
        # Test core module imports
        from llm_council.models.idea_models import Problem, ICP, Assumption, ExtractedEntities
        from llm_council.database.neo4j_client import Neo4jClient, Neo4jConfig
        from llm_council.services.question_engine import QuestionEngine
        from llm_council.services.council_system import CouncilSystem
        from llm_council.multi_model import MultiModelClient
        from llm_council.schemas import AuditorResponse, DimensionScore
        
        return "Core modules imported successfully"
    
    def _test_model_validation(self) -> str:
        """Test Pydantic model validation."""
        
        from llm_council.models.idea_models import Problem, ICP, Assumption
        
        # Test Problem model
        problem = Problem(
            id="P-001",
            statement="Test problem statement",
            impact_metric="Test metric",
            pain_level=0.8,
            frequency=1.0,
            confidence=0.9
        )
        
        assert problem.id == "P-001"
        assert problem.pain_level == 0.8
        
        # Test ICP model
        icp = ICP(
            id="ICP-001",
            segment="Test segment",
            size=1000,
            pains=["pain1", "pain2"],
            gains=["gain1", "gain2"],
            wtp=100.0,
            confidence=0.8
        )
        
        assert icp.size == 1000
        assert len(icp.pains) == 2
        
        # Test Assumption model
        assumption = Assumption(
            id="A-001",
            statement="Test assumption",
            type="market",
            criticality=0.9,
            confidence=0.7,
            validation_method="interview"
        )
        
        assert assumption.criticality == 0.9
        
        return "Pydantic models validate correctly"
    
    def _test_service_initialization(self) -> str:
        """Test that services can be initialized without errors."""
        
        from llm_council.multi_model import MultiModelClient
        from llm_council.database.neo4j_client import Neo4jConfig
        
        # Test MultiModelClient initialization
        multi_model = MultiModelClient()
        assert multi_model is not None
        
        # Test Neo4j config creation
        neo4j_config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="test-password"
        )
        
        assert neo4j_config.uri == "bolt://localhost:7687"
        
        return "Services initialize without errors"
    
    def _test_config_loading(self) -> str:
        """Test configuration loading."""
        
        # Test basic config structures exist
        import os
        from pathlib import Path
        
        # Check if basic config files exist
        root_path = Path(__file__).parent.parent
        config_files = ["requirements.txt", "pytest.ini"]
        
        existing_configs = []
        for config_file in config_files:
            if (root_path / config_file).exists():
                existing_configs.append(config_file)
        
        return f"Found {len(existing_configs)} config files: {existing_configs}"
    
    def _test_schema_validation(self) -> str:
        """Test schema validation."""
        
        from llm_council.schemas import DimensionScore, OverallAssessment
        
        # Test DimensionScore schema
        dimension_score = DimensionScore(
            score=4,
            **{"pass": True},  # Use the alias
            justification="This is a test justification that meets the minimum length requirement for validation",
            improvements=["improvement1", "improvement2"]
        )
        
        assert dimension_score.score == 4
        assert dimension_score.pass_ == True
        
        # Test OverallAssessment schema
        overall_assessment = OverallAssessment(
            average_score=4.0,
            overall_pass=True,
            summary="This is a test summary that meets the minimum length requirement for validation",
            top_strengths=["strength1", "strength2"],
            top_risks=["risk1", "risk2"],
            quick_wins=["win1", "win2"]
        )
        
        assert overall_assessment.average_score == 4.0
        assert overall_assessment.overall_pass == True
        
        return "Schema validation working correctly"

def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(description="Smoke Test Runner")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Run smoke tests
    runner = SmokeTestRunner()
    
    try:
        success = runner.run_smoke_tests(verbose=args.verbose)
        
        if success:
            logger.info("🚀 Smoke tests passed - system ready for E2E validation!")
            sys.exit(0)
        else:
            logger.error("❌ Smoke tests failed - please fix core issues")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Smoke tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Smoke tests failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()