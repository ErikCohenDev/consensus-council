#!/usr/bin/env python3
"""Quick system status check for the Idea Operating System.

This script performs a rapid health check to verify the system is ready
for validation without running the full test suite.

Usage:
    python scripts/system-status.py
    python scripts/system-status.py --verbose
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemStatusChecker:
    """Quick system status and readiness checker."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.status_results = {}
    
    def check_system_status(self, verbose: bool = False) -> Dict[str, any]:
        """Perform comprehensive system status check."""
        
        logger.info("🔍 Checking Idea Operating System Status")
        logger.info("=" * 50)
        
        status_results = {
            "overall_ready": True,
            "checks": {},
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Check 1: Project Structure
        structure_status = self._check_project_structure()
        status_results["checks"]["project_structure"] = structure_status
        if not structure_status["success"]:
            status_results["overall_ready"] = False
            status_results["errors"].extend(structure_status["errors"])
        
        # Check 2: Python Environment
        python_status = self._check_python_environment()
        status_results["checks"]["python_environment"] = python_status
        if not python_status["success"]:
            status_results["overall_ready"] = False
            status_results["errors"].extend(python_status["errors"])
        
        # Check 3: Docker Environment
        docker_status = self._check_docker_environment()
        status_results["checks"]["docker_environment"] = docker_status
        if not docker_status["success"]:
            status_results["overall_ready"] = False
            status_results["errors"].extend(docker_status["errors"])
        
        # Check 4: Test Files
        test_status = self._check_test_files()
        status_results["checks"]["test_files"] = test_status
        if not test_status["success"]:
            status_results["overall_ready"] = False
            status_results["errors"].extend(test_status["errors"])
        
        # Check 5: Configuration Files
        config_status = self._check_configuration_files()
        status_results["checks"]["configuration_files"] = config_status
        status_results["warnings"].extend(config_status.get("warnings", []))
        
        # Check 6: Documentation
        docs_status = self._check_documentation()
        status_results["checks"]["documentation"] = docs_status
        status_results["warnings"].extend(docs_status.get("warnings", []))
        
        # Generate recommendations
        status_results["recommendations"] = self._generate_recommendations(status_results)
        
        # Log summary
        self._log_status_summary(status_results, verbose)
        
        return status_results
    
    def _check_project_structure(self) -> Dict[str, any]:
        """Check project directory structure."""
        
        logger.info("📁 Checking project structure...")
        
        required_dirs = [
            "src/llm_council",
            "tests/e2e", 
            "tests/integration",
            "docs",
            "scripts"
        ]
        
        optional_dirs = [
            "frontend",
            "backend", 
            "config",
            "shared"
        ]
        
        missing_required = []
        missing_optional = []
        
        for dir_path in required_dirs:
            if not (self.root_path / dir_path).exists():
                missing_required.append(dir_path)
        
        for dir_path in optional_dirs:
            if not (self.root_path / dir_path).exists():
                missing_optional.append(dir_path)
        
        result = {
            "success": len(missing_required) == 0,
            "required_dirs_found": len(required_dirs) - len(missing_required),
            "total_required_dirs": len(required_dirs),
            "optional_dirs_found": len(optional_dirs) - len(missing_optional),
            "total_optional_dirs": len(optional_dirs),
            "errors": [],
            "warnings": []
        }
        
        if missing_required:
            result["errors"] = [f"Missing required directories: {missing_required}"]
        
        if missing_optional:
            result["warnings"] = [f"Missing optional directories: {missing_optional}"]
        
        if result["success"]:
            logger.info("   ✅ Project structure OK")
        else:
            logger.error(f"   ❌ Missing required directories: {missing_required}")
        
        return result
    
    def _check_python_environment(self) -> Dict[str, any]:
        """Check Python environment and dependencies."""
        
        logger.info("🐍 Checking Python environment...")
        
        result = {
            "success": True,
            "python_version": None,
            "dependencies": {},
            "errors": [],
            "warnings": []
        }
        
        # Check Python version
        try:
            python_version = sys.version_info
            result["python_version"] = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
            
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
                result["errors"].append(f"Python 3.8+ required, found {result['python_version']}")
                result["success"] = False
        except Exception as e:
            result["errors"].append(f"Failed to check Python version: {e}")
            result["success"] = False
        
        # Check key dependencies
        key_dependencies = [
            "pytest",
            "neo4j", 
            "litellm",
            "pydantic",
            "asyncio"
        ]
        
        for dep in key_dependencies:
            try:
                __import__(dep)
                result["dependencies"][dep] = "✅ Available"
            except ImportError:
                result["dependencies"][dep] = "❌ Missing"
                result["warnings"].append(f"Missing dependency: {dep}")
        
        # Check if requirements.txt exists
        if (self.root_path / "requirements.txt").exists():
            result["requirements_file"] = "✅ Found"
        else:
            result["requirements_file"] = "⚠️  Missing"
            result["warnings"].append("requirements.txt not found")
        
        if result["success"]:
            logger.info(f"   ✅ Python {result['python_version']} OK")
        else:
            logger.error("   ❌ Python environment issues found")
        
        return result
    
    def _check_docker_environment(self) -> Dict[str, any]:
        """Check Docker environment."""
        
        logger.info("🐳 Checking Docker environment...")
        
        result = {
            "success": True,
            "docker_available": False,
            "docker_running": False,
            "neo4j_image_available": False,
            "errors": [],
            "warnings": []
        }
        
        # Check if Docker is installed
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            result["docker_available"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            result["docker_available"] = False
            result["errors"].append("Docker is not installed or not in PATH")
            result["success"] = False
        
        if result["docker_available"]:
            # Check if Docker daemon is running
            try:
                subprocess.run(["docker", "info"], capture_output=True, check=True)
                result["docker_running"] = True
            except subprocess.CalledProcessError:
                result["docker_running"] = False
                result["errors"].append("Docker daemon is not running")
                result["success"] = False
        
        if result["docker_running"]:
            # Check if Neo4j image is available
            try:
                result_cmd = subprocess.run(
                    ["docker", "images", "neo4j", "--format", "{{.Repository}}:{{.Tag}}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if "neo4j" in result_cmd.stdout:
                    result["neo4j_image_available"] = True
                else:
                    result["warnings"].append("Neo4j Docker image not found locally (will be downloaded)")
            except subprocess.CalledProcessError:
                result["warnings"].append("Could not check for Neo4j Docker image")
        
        if result["success"]:
            logger.info("   ✅ Docker environment OK")
        else:
            logger.error("   ❌ Docker environment issues found")
        
        return result
    
    def _check_test_files(self) -> Dict[str, any]:
        """Check test files exist."""
        
        logger.info("🧪 Checking test files...")
        
        expected_e2e_tests = [
            "tests/e2e/test_founder_journey.py",
            "tests/e2e/test_pm_journey.py",
            "tests/e2e/test_engineer_journey.py", 
            "tests/e2e/test_team_journey.py",
            "tests/e2e/test_complete_system_journey.py"
        ]
        
        expected_unit_tests = [
            "tests/test_council_members.py",
            "tests/test_consensus_engine.py",
            "tests/test_multi_model.py"
        ]
        
        missing_e2e = []
        missing_unit = []
        
        for test_file in expected_e2e_tests:
            if not (self.root_path / test_file).exists():
                missing_e2e.append(test_file)
        
        for test_file in expected_unit_tests:
            if not (self.root_path / test_file).exists():
                missing_unit.append(test_file)
        
        result = {
            "success": len(missing_e2e) == 0,
            "e2e_tests_found": len(expected_e2e_tests) - len(missing_e2e),
            "total_e2e_tests": len(expected_e2e_tests),
            "unit_tests_found": len(expected_unit_tests) - len(missing_unit),
            "total_unit_tests": len(expected_unit_tests),
            "errors": [],
            "warnings": []
        }
        
        if missing_e2e:
            result["errors"].append(f"Missing E2E tests: {missing_e2e}")
        
        if missing_unit:
            result["warnings"].append(f"Missing unit tests: {missing_unit}")
        
        if result["success"]:
            logger.info(f"   ✅ E2E tests OK ({result['e2e_tests_found']}/{result['total_e2e_tests']})")
        else:
            logger.error(f"   ❌ Missing E2E tests: {len(missing_e2e)}")
        
        return result
    
    def _check_configuration_files(self) -> Dict[str, any]:
        """Check configuration files."""
        
        logger.info("⚙️  Checking configuration files...")
        
        expected_configs = [
            "pytest.ini",
            "requirements.txt",
            ".gitignore"
        ]
        
        optional_configs = [
            "pyproject.toml",
            "setup.py",
            "Dockerfile",
            "docker-compose.yml"
        ]
        
        missing_required = []
        missing_optional = []
        
        for config_file in expected_configs:
            if not (self.root_path / config_file).exists():
                missing_required.append(config_file)
        
        for config_file in optional_configs:
            if not (self.root_path / config_file).exists():
                missing_optional.append(config_file)
        
        result = {
            "success": len(missing_required) == 0,
            "required_configs_found": len(expected_configs) - len(missing_required),
            "total_required_configs": len(expected_configs),
            "optional_configs_found": len(optional_configs) - len(missing_optional),
            "total_optional_configs": len(optional_configs),
            "warnings": []
        }
        
        if missing_required:
            result["warnings"].append(f"Missing config files: {missing_required}")
        
        if missing_optional:
            result["warnings"].append(f"Missing optional configs: {missing_optional}")
        
        logger.info(f"   ✅ Config files OK ({result['required_configs_found']}/{result['total_required_configs']})")
        
        return result
    
    def _check_documentation(self) -> Dict[str, any]:
        """Check documentation files."""
        
        logger.info("📚 Checking documentation...")
        
        expected_docs = [
            "README.md",
            "docs/VISION.md",
            "docs/PRD.md",
            "docs/ARCHITECTURE.md"
        ]
        
        missing_docs = []
        
        for doc_file in expected_docs:
            if not (self.root_path / doc_file).exists():
                missing_docs.append(doc_file)
        
        result = {
            "success": len(missing_docs) == 0,
            "docs_found": len(expected_docs) - len(missing_docs),
            "total_docs": len(expected_docs),
            "warnings": []
        }
        
        if missing_docs:
            result["warnings"].append(f"Missing documentation: {missing_docs}")
        
        logger.info(f"   ✅ Documentation OK ({result['docs_found']}/{result['total_docs']})")
        
        return result
    
    def _generate_recommendations(self, status_results: Dict[str, any]) -> List[str]:
        """Generate recommendations based on status check results."""
        
        recommendations = []
        
        # Python environment recommendations
        python_check = status_results["checks"].get("python_environment", {})
        if not python_check.get("success", True):
            recommendations.append("Install Python 3.8+ and required dependencies")
            recommendations.append("Run: pip install -r requirements.txt")
        
        # Docker recommendations
        docker_check = status_results["checks"].get("docker_environment", {})
        if not docker_check.get("success", True):
            if not docker_check.get("docker_available", False):
                recommendations.append("Install Docker Desktop or Docker Engine")
            elif not docker_check.get("docker_running", False):
                recommendations.append("Start Docker daemon")
        
        # Test file recommendations
        test_check = status_results["checks"].get("test_files", {})
        if not test_check.get("success", True):
            recommendations.append("Create missing E2E test files")
            recommendations.append("Review test implementation in tests/e2e/ directory")
        
        # General recommendations
        if not status_results["overall_ready"]:
            recommendations.append("Fix all errors before running full validation")
            recommendations.append("Use --quick mode for faster validation during development")
        else:
            recommendations.append("System ready for validation - run: ./run-validation.sh")
            recommendations.append("For quick validation: ./run-validation.sh --quick")
        
        return recommendations
    
    def _log_status_summary(self, status_results: Dict[str, any], verbose: bool) -> None:
        """Log comprehensive status summary."""
        
        logger.info("=" * 50)
        logger.info("📊 SYSTEM STATUS SUMMARY")
        logger.info("=" * 50)
        
        # Overall status
        overall_status = "✅ READY" if status_results["overall_ready"] else "❌ NOT READY"
        logger.info(f"Overall Status: {overall_status}")
        
        # Check summary
        checks = status_results["checks"]
        total_checks = len(checks)
        passed_checks = len([c for c in checks.values() if c.get("success", False)])
        
        logger.info(f"Checks Passed: {passed_checks}/{total_checks}")
        
        # Individual check results
        if verbose:
            logger.info("")
            logger.info("📋 DETAILED CHECK RESULTS:")
            
            check_icons = {
                "project_structure": "📁",
                "python_environment": "🐍",
                "docker_environment": "🐳",
                "test_files": "🧪",
                "configuration_files": "⚙️",
                "documentation": "📚"
            }
            
            for check_name, check_result in checks.items():
                icon = check_icons.get(check_name, "📄")
                status = "✅ PASS" if check_result.get("success", False) else "❌ FAIL"
                logger.info(f"   {icon} {check_name.replace('_', ' ').title()}: {status}")
        
        # Errors
        if status_results["errors"]:
            logger.info("")
            logger.info("❌ ERRORS TO FIX:")
            for i, error in enumerate(status_results["errors"], 1):
                logger.error(f"   {i}. {error}")
        
        # Warnings
        if status_results["warnings"] and verbose:
            logger.info("")
            logger.info("⚠️  WARNINGS:")
            for i, warning in enumerate(status_results["warnings"], 1):
                logger.warning(f"   {i}. {warning}")
        
        # Recommendations
        if status_results["recommendations"]:
            logger.info("")
            logger.info("💡 RECOMMENDATIONS:")
            for i, rec in enumerate(status_results["recommendations"], 1):
                logger.info(f"   {i}. {rec}")
        
        logger.info("=" * 50)

def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(description="System Status Checker")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--root-path", default=".", help="Root path of the project")
    
    args = parser.parse_args()
    
    # Initialize status checker
    checker = SystemStatusChecker(args.root_path)
    
    try:
        # Check system status
        status_results = checker.check_system_status(verbose=args.verbose)
        
        # Exit with appropriate code
        if status_results["overall_ready"]:
            logger.info("🚀 System is ready for validation!")
            sys.exit(0)
        else:
            logger.error("❌ System is not ready - please fix issues above")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Status check interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()