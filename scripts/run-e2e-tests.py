#!/usr/bin/env python3
"""Complete E2E test runner for the Idea Operating System.

This script sets up the test environment, runs all E2E tests, and provides
comprehensive validation of the complete system functionality.

Usage:
    python scripts/run-e2e-tests.py --full
    python scripts/run-e2e-tests.py --user-journey founder
    python scripts/run-e2e-tests.py --quick --no-setup
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class E2ETestRunner:
    """Complete E2E test runner with environment setup and validation."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.test_results = {}
        self.start_time = None
        self.neo4j_container_name = "neo4j-e2e-test"
        
    def run_complete_e2e_suite(
        self,
        user_journey: Optional[str] = None,
        setup_environment: bool = True,
        cleanup_after: bool = True,
        verbose: bool = True
    ) -> Dict[str, any]:
        """Run complete E2E test suite with environment setup."""
        
        self.start_time = datetime.utcnow()
        
        logger.info("🚀 Starting Complete E2E Test Suite for Idea Operating System")
        logger.info("=" * 80)
        
        try:
            # Step 1: Environment setup
            if setup_environment:
                self._setup_test_environment()
            
            # Step 2: Validate prerequisites
            self._validate_prerequisites()
            
            # Step 3: Run E2E tests
            test_results = self._run_e2e_tests(user_journey, verbose)
            
            # Step 4: Generate summary report
            summary = self._generate_test_summary(test_results)
            
            # Step 5: Cleanup
            if cleanup_after:
                self._cleanup_test_environment()
            
            return summary
            
        except Exception as e:
            logger.error(f"E2E test suite failed: {e}")
            if cleanup_after:
                self._cleanup_test_environment()
            raise
    
    def _setup_test_environment(self) -> None:
        """Set up test environment including Neo4j database."""
        
        logger.info("🔧 Setting up test environment...")
        
        # Step 1: Stop any existing test container
        try:
            subprocess.run(
                ["docker", "stop", self.neo4j_container_name],
                capture_output=True,
                check=False
            )
            subprocess.run(
                ["docker", "rm", self.neo4j_container_name], 
                capture_output=True,
                check=False
            )
        except Exception:
            pass  # Container might not exist
        
        # Step 2: Start Neo4j test database
        neo4j_cmd = [
            "docker", "run", "-d",
            "--name", self.neo4j_container_name,
            "-e", "NEO4J_AUTH=neo4j/test-password",
            "-e", 'NEO4J_PLUGINS=["apoc"]',
            "-p", "7687:7687",
            "-p", "7474:7474",
            "neo4j:5.15-community"
        ]
        
        result = subprocess.run(neo4j_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to start Neo4j container: {result.stderr}")
        
        logger.info("   ✅ Neo4j test database started")
        
        # Step 3: Wait for Neo4j to be ready
        logger.info("   ⏳ Waiting for Neo4j to be ready...")
        
        max_wait = 60  # seconds
        wait_time = 0
        
        while wait_time < max_wait:
            try:
                # Test connection
                test_cmd = [
                    "docker", "exec", self.neo4j_container_name,
                    "cypher-shell", "-u", "neo4j", "-p", "test-password",
                    "RETURN 1 as test"
                ]
                
                result = subprocess.run(test_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    break
                
            except Exception:
                pass
            
            time.sleep(2)
            wait_time += 2
        
        if wait_time >= max_wait:
            raise Exception("Neo4j failed to start within timeout")
        
        logger.info("   ✅ Neo4j ready for connections")
        
        # Step 4: Set environment variables
        os.environ["NEO4J_TEST_URI"] = "bolt://localhost:7687"
        os.environ["NEO4J_TEST_USER"] = "neo4j"
        os.environ["NEO4J_TEST_PASSWORD"] = "test-password"
        
        # Step 5: Install Python dependencies if needed
        try:
            import pytest
            import neo4j
            logger.info("   ✅ Python dependencies available")
        except ImportError as e:
            logger.info("   📦 Installing missing Python dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        logger.info("🔧 Test environment setup complete!")
    
    def _validate_prerequisites(self) -> None:
        """Validate that all prerequisites are met."""
        
        logger.info("🔍 Validating prerequisites...")
        
        # Check if Neo4j is accessible
        try:
            result = subprocess.run(
                ["docker", "exec", self.neo4j_container_name, "echo", "test"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise Exception("Neo4j container not accessible")
        except Exception as e:
            raise Exception(f"Neo4j validation failed: {e}")
        
        # Check Python path setup
        test_src_path = self.root_path / "src"
        if not test_src_path.exists():
            raise Exception(f"Source directory not found: {test_src_path}")
        
        # Check test files exist
        e2e_dir = self.root_path / "tests" / "e2e"
        if not e2e_dir.exists():
            raise Exception(f"E2E test directory not found: {e2e_dir}")
        
        expected_test_files = [
            "test_founder_journey.py",
            "test_pm_journey.py", 
            "test_engineer_journey.py",
            "test_team_journey.py",
            "test_complete_system_journey.py"
        ]
        
        for test_file in expected_test_files:
            if not (e2e_dir / test_file).exists():
                raise Exception(f"Required test file missing: {test_file}")
        
        logger.info("   ✅ All prerequisites validated")
    
    def _run_e2e_tests(self, user_journey: Optional[str], verbose: bool) -> Dict[str, any]:
        """Run E2E tests with proper environment configuration."""
        
        logger.info("🧪 Running E2E tests...")
        
        # Set up Python path
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.root_path / "src")
        
        # Define test files to run
        if user_journey:
            test_files = [f"tests/e2e/test_{user_journey}_journey.py"]
        else:
            test_files = [
                "tests/e2e/test_founder_journey.py",
                "tests/e2e/test_pm_journey.py",
                "tests/e2e/test_engineer_journey.py", 
                "tests/e2e/test_team_journey.py",
                "tests/e2e/test_complete_system_journey.py"
            ]
        
        test_results = {}
        
        for test_file in test_files:
            logger.info(f"   📋 Running {test_file}...")
            
            # Build pytest command
            pytest_cmd = [
                sys.executable, "-m", "pytest",
                test_file,
                "-v" if verbose else "-q",
                "--tb=short",
                "--maxfail=1",  # Stop on first failure for faster feedback
                "--disable-warnings"
            ]
            
            # Run test
            start_time = time.time()
            result = subprocess.run(
                pytest_cmd,
                cwd=str(self.root_path),
                env=env,
                capture_output=True,
                text=True
            )
            end_time = time.time()
            
            # Parse results
            test_name = Path(test_file).stem
            test_results[test_name] = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration_seconds": end_time - start_time,
                "success": result.returncode == 0
            }
            
            if result.returncode == 0:
                logger.info(f"   ✅ {test_name} PASSED ({test_results[test_name]['duration_seconds']:.1f}s)")
            else:
                logger.error(f"   ❌ {test_name} FAILED ({test_results[test_name]['duration_seconds']:.1f}s)")
                if verbose:
                    logger.error(f"   Error output: {result.stderr}")
        
        return test_results
    
    def _generate_test_summary(self, test_results: Dict[str, any]) -> Dict[str, any]:
        """Generate comprehensive test summary report."""
        
        logger.info("📊 Generating test summary...")
        
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results.values() if r["success"]])
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(r["duration_seconds"] for r in test_results.values())
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "total_duration_seconds": total_duration,
            "average_duration_seconds": total_duration / total_tests if total_tests > 0 else 0,
            "test_details": test_results,
            "overall_success": failed_tests == 0,
            "started_at": self.start_time.isoformat() if self.start_time else None,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # Categorize results by user journey
        journey_results = {
            "founder": test_results.get("test_founder_journey", {}).get("success", False),
            "pm": test_results.get("test_pm_journey", {}).get("success", False),
            "engineer": test_results.get("test_engineer_journey", {}).get("success", False),
            "team": test_results.get("test_team_journey", {}).get("success", False),
            "complete_system": test_results.get("test_complete_system_journey", {}).get("success", False)
        }
        
        summary["journey_results"] = journey_results
        summary["journey_success_rate"] = (sum(1 for success in journey_results.values() if success) / 
                                         len(journey_results)) * 100
        
        return summary
    
    def _cleanup_test_environment(self) -> None:
        """Clean up test environment."""
        
        logger.info("🧹 Cleaning up test environment...")
        
        try:
            # Stop and remove Neo4j container
            subprocess.run(
                ["docker", "stop", self.neo4j_container_name],
                capture_output=True,
                check=False
            )
            subprocess.run(
                ["docker", "rm", self.neo4j_container_name],
                capture_output=True, 
                check=False
            )
            logger.info("   ✅ Neo4j test container removed")
        except Exception as e:
            logger.warning(f"   ⚠️  Failed to cleanup Neo4j container: {e}")
        
        # Clean up environment variables
        test_env_vars = ["NEO4J_TEST_URI", "NEO4J_TEST_USER", "NEO4J_TEST_PASSWORD"]
        for var in test_env_vars:
            if var in os.environ:
                del os.environ[var]
        
        logger.info("🧹 Cleanup complete!")
    
    def _print_final_report(self, summary: Dict[str, any]) -> None:
        """Print comprehensive final test report."""
        
        logger.info("=" * 80)
        logger.info("🎯 COMPLETE E2E TEST RESULTS")
        logger.info("=" * 80)
        
        # Overall results
        overall_status = "✅ SUCCESS" if summary["overall_success"] else "❌ FAILURE"
        logger.info(f"Status: {overall_status}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}% ({summary['passed_tests']}/{summary['total_tests']} tests passed)")
        logger.info(f"Total Duration: {summary['total_duration_seconds']:.1f} seconds")
        logger.info(f"Average Test Duration: {summary['average_duration_seconds']:.1f} seconds")
        
        logger.info("")
        logger.info("📋 USER JOURNEY RESULTS:")
        
        journey_icons = {
            "founder": "🚀",
            "pm": "📋", 
            "engineer": "💻",
            "team": "👥",
            "complete_system": "🎯"
        }
        
        for journey, success in summary["journey_results"].items():
            icon = journey_icons.get(journey, "📄")
            status = "✅ PASS" if success else "❌ FAIL"
            duration = summary["test_details"].get(f"test_{journey}_journey", {}).get("duration_seconds", 0)
            logger.info(f"   {icon} {journey.replace('_', ' ').title()}: {status} ({duration:.1f}s)")
        
        logger.info(f"\n🏆 Journey Success Rate: {summary['journey_success_rate']:.1f}%")
        
        # Detailed failures if any
        failed_tests = [name for name, result in summary["test_details"].items() if not result["success"]]
        if failed_tests:
            logger.info("")
            logger.info("❌ FAILED TESTS:")
            for test_name in failed_tests:
                result = summary["test_details"][test_name]
                logger.error(f"   {test_name}:")
                logger.error(f"      Duration: {result['duration_seconds']:.1f}s")
                if result["stderr"]:
                    # Show first few lines of error
                    error_lines = result["stderr"].split('\n')[:3]
                    for line in error_lines:
                        if line.strip():
                            logger.error(f"      {line}")
        
        # Success summary
        if summary["overall_success"]:
            logger.info("")
            logger.info("🎉 ALL E2E TESTS PASSED!")
            logger.info("✅ Complete Idea Operating System validated end-to-end")
            logger.info("✅ All user journeys working correctly")
            logger.info("✅ Full traceability from idea to production code")
            logger.info("✅ Multi-model council system functioning")
            logger.info("✅ Research integration and question generation working")
            logger.info("✅ Provenance tracking and impact analysis operational")
        else:
            logger.error("")
            logger.error("❌ E2E TEST FAILURES DETECTED")
            logger.error("🔧 Please review failed tests and fix issues before deployment")
        
        logger.info("=" * 80)

def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(description="Complete E2E Test Runner")
    parser.add_argument("--full", action="store_true", help="Run complete test suite (default)")
    parser.add_argument("--user-journey", choices=["founder", "pm", "engineer", "team", "complete_system"], 
                       help="Run specific user journey tests only")
    parser.add_argument("--quick", action="store_true", help="Quick test run (less verbose)")
    parser.add_argument("--no-setup", action="store_true", help="Skip environment setup (assume already configured)")
    parser.add_argument("--no-cleanup", action="store_true", help="Skip cleanup (leave test environment running)")
    parser.add_argument("--root-path", default=".", help="Root path of the project")
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = E2ETestRunner(args.root_path)
    
    try:
        # Run tests
        summary = runner.run_complete_e2e_suite(
            user_journey=args.user_journey,
            setup_environment=not args.no_setup,
            cleanup_after=not args.no_cleanup,
            verbose=not args.quick
        )
        
        # Print final report
        runner._print_final_report(summary)
        
        # Exit with appropriate code
        if summary["overall_success"]:
            logger.info("🚀 E2E validation complete - system ready for production!")
            sys.exit(0)
        else:
            logger.error("❌ E2E validation failed - please fix issues before deployment")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("E2E test run interrupted by user")
        runner._cleanup_test_environment()
        sys.exit(1)
    except Exception as e:
        logger.error(f"E2E test run failed: {e}")
        runner._cleanup_test_environment()
        sys.exit(1)

if __name__ == "__main__":
    main()
