#!/usr/bin/env python3
"""CI/CD traceability enforcement script.

Scans codebase, validates provenance, generates traceability matrix,
and enforces alignment gates for continuous integration.

Usage:
    python scripts/trace-check.py --increment mvp --enforce
    python scripts/trace-check.py --scan-only --output trace/matrix.csv
    python scripts/trace-check.py --validate-headers --fix-missing
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_council.database.neo4j_client import Neo4jClient, Neo4jConfig
from llm_council.services.provenance_tracker import CodeScanner, ProvenanceTracker
from llm_council.services.traceability_matrix import TraceabilityMatrix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TraceabilityEnforcer:
    """CI/CD traceability enforcement with configurable gates."""
    
    def __init__(self, root_path: str, neo4j_config: Neo4jConfig):
        self.root_path = Path(root_path)
        self.neo4j_client = Neo4jClient(neo4j_config)
        self.code_scanner = CodeScanner(self.neo4j_client)
        self.provenance_tracker = ProvenanceTracker(self.neo4j_client, self.code_scanner)
        self.matrix_generator = TraceabilityMatrix(self.neo4j_client)
        
        # Default enforcement rules
        self.enforcement_rules = {
            "min_coverage_percentage": 85.0,
            "allow_orphan_code": False,
            "allow_orphan_requirements": False,
            "require_provenance_headers": True,
            "min_test_coverage_per_req": 80.0,
            "require_e2e_for_critical": True,
            "max_complexity_without_tests": 10
        }
    
    def run_full_check(
        self, 
        increment: str = "mvp",
        enforce: bool = False,
        output_dir: str = "trace"
    ) -> Dict[str, any]:
        """Run complete traceability check and enforcement."""
        
        logger.info(f"Starting full traceability check for increment: {increment}")
        
        # Step 1: Connect to Neo4j
        try:
            self.neo4j_client.connect()
            logger.info("Connected to Neo4j successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return {"success": False, "error": str(e)}
        
        try:
            # Step 2: Scan codebase and sync to Neo4j
            scan_results = self.scan_and_sync_codebase()
            
            # Step 3: Generate traceability matrix
            matrix_results = self.generate_matrix_reports(increment, output_dir)
            
            # Step 4: Validate provenance headers
            header_validation = self.validate_provenance_headers()
            
            # Step 5: Run enforcement gates
            gate_results = self.run_enforcement_gates(increment, enforce)
            
            # Combine results
            results = {
                "success": True,
                "increment": increment,
                "scan_results": scan_results,
                "matrix_results": matrix_results,
                "header_validation": header_validation,
                "gate_results": gate_results,
                "enforcement_enabled": enforce
            }
            
            # Log summary
            self._log_summary(results)
            
            return results
            
        finally:
            self.neo4j_client.close()
    
    def scan_and_sync_codebase(self) -> Dict[str, any]:
        """Scan codebase and sync artifacts to Neo4j."""
        
        logger.info("Scanning codebase for artifacts...")
        
        # Scan codebase
        scan_results = self.code_scanner.scan_codebase(str(self.root_path))
        
        # Sync to Neo4j
        logger.info("Syncing artifacts to Neo4j...")
        self.provenance_tracker.sync_artifacts_to_neo4j(scan_results)
        
        logger.info(f"Scanned {scan_results['scanned_files']}/{scan_results['total_files']} files")
        
        return {
            "total_files": scan_results["total_files"],
            "scanned_files": scan_results["scanned_files"],
            "services_found": len(scan_results["services"]),
            "classes_found": len(scan_results["classes"]),
            "functions_found": len(scan_results["functions"]),
            "tests_found": len(scan_results["tests"]),
            "dependencies": len(scan_results["dependencies"])
        }
    
    def generate_matrix_reports(self, increment: str, output_dir: str) -> Dict[str, any]:
        """Generate traceability matrix and reports."""
        
        logger.info("Generating traceability matrix...")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate matrix
        matrix_entries = self.matrix_generator.generate_complete_matrix(increment)
        
        # Generate coverage report
        coverage_report = self.matrix_generator.generate_coverage_report(increment)
        
        # Find orphans
        orphan_report = self.matrix_generator.find_orphans()
        
        # Export in multiple formats
        csv_path = self.matrix_generator.export_matrix_csv(
            matrix_entries, 
            str(output_path / f"traceability_matrix_{increment}.csv")
        )
        
        json_path = self.matrix_generator.export_matrix_json(
            matrix_entries,
            str(output_path / f"traceability_matrix_{increment}.json")
        )
        
        html_path = self.matrix_generator.generate_html_dashboard(
            matrix_entries,
            coverage_report,
            orphan_report,
            str(output_path / f"traceability_dashboard_{increment}.html")
        )
        
        return {
            "total_entries": len(matrix_entries),
            "green_count": len([e for e in matrix_entries if e.status == "GREEN"]),
            "yellow_count": len([e for e in matrix_entries if e.status == "YELLOW"]),
            "red_count": len([e for e in matrix_entries if e.status == "RED"]),
            "overall_coverage": coverage_report.overall_coverage,
            "orphan_code_count": orphan_report.summary.get("orphan_code_count", 0),
            "orphan_requirements_count": orphan_report.summary.get("orphan_requirements_count", 0),
            "exports": {
                "csv": csv_path,
                "json": json_path,
                "html": html_path
            }
        }
    
    def validate_provenance_headers(self) -> Dict[str, any]:
        """Validate provenance headers across codebase."""
        
        logger.info("Validating provenance headers...")
        
        validation_report = self.provenance_tracker.validate_provenance_headers(str(self.root_path))
        
        logger.info(f"Header validation: {validation_report['files_with_headers']}/{validation_report['total_files']} files have headers")
        
        return validation_report
    
    def run_enforcement_gates(self, increment: str, enforce: bool) -> Dict[str, any]:
        """Run enforcement gates and optionally fail if violations found."""
        
        logger.info("Running enforcement gates...")
        
        gate_results = {
            "passed": True,
            "violations": [],
            "warnings": [],
            "summary": {}
        }
        
        # Gate 1: Check increment readiness
        readiness_check = self.matrix_generator.validate_increment_readiness(increment)
        
        if not readiness_check["ready_for_release"]:
            gate_results["passed"] = False
            for issue in readiness_check["blocking_issues"]:
                gate_results["violations"].append({
                    "gate": "increment_readiness",
                    "issue": issue,
                    "severity": "error"
                })
        
        # Gate 2: Check for orphan code
        if not self.enforcement_rules["allow_orphan_code"]:
            orphan_report = self.matrix_generator.find_orphans()
            if orphan_report.summary.get("orphan_code_count", 0) > 0:
                gate_results["passed"] = False
                gate_results["violations"].append({
                    "gate": "orphan_code",
                    "issue": f"Found {orphan_report.summary['orphan_code_count']} orphan code artifacts",
                    "severity": "error",
                    "details": orphan_report.orphan_code[:5]  # First 5 for brevity
                })
        
        # Gate 3: Check for orphan requirements
        if not self.enforcement_rules["allow_orphan_requirements"]:
            orphan_report = self.matrix_generator.find_orphans()
            if orphan_report.summary.get("orphan_requirements_count", 0) > 0:
                gate_results["passed"] = False
                gate_results["violations"].append({
                    "gate": "orphan_requirements",
                    "issue": f"Found {orphan_report.summary['orphan_requirements_count']} orphan requirements",
                    "severity": "error",
                    "details": orphan_report.orphan_requirements[:5]
                })
        
        # Gate 4: Check provenance headers
        if self.enforcement_rules["require_provenance_headers"]:
            validation_report = self.provenance_tracker.validate_provenance_headers(str(self.root_path))
            if validation_report["coverage_rate"] < 0.9:  # 90% coverage required
                gate_results["warnings"].append({
                    "gate": "provenance_headers",
                    "issue": f"Provenance header coverage {validation_report['coverage_rate']:.1%} < 90%",
                    "severity": "warning"
                })
        
        # Gate 5: Check test coverage
        coverage_report = self.matrix_generator.generate_coverage_report(increment)
        if coverage_report.overall_coverage < self.enforcement_rules["min_coverage_percentage"]:
            gate_results["passed"] = False
            gate_results["violations"].append({
                "gate": "test_coverage",
                "issue": f"Overall coverage {coverage_report.overall_coverage:.1f}% < {self.enforcement_rules['min_coverage_percentage']}%",
                "severity": "error"
            })
        
        gate_results["summary"] = {
            "total_violations": len(gate_results["violations"]),
            "total_warnings": len(gate_results["warnings"]),
            "overall_readiness": readiness_check["ready_for_release"],
            "coverage_percentage": coverage_report.overall_coverage
        }
        
        # If enforcement enabled and violations found, this will cause CI to fail
        if enforce and not gate_results["passed"]:
            logger.error("ENFORCEMENT FAILURE: Traceability gates failed")
            for violation in gate_results["violations"]:
                logger.error(f"❌ {violation['gate']}: {violation['issue']}")
        
        # Log warnings
        for warning in gate_results["warnings"]:
            logger.warning(f"⚠️  {warning['gate']}: {warning['issue']}")
        
        return gate_results
    
    def _log_summary(self, results: Dict[str, any]) -> None:
        """Log comprehensive summary of traceability check."""
        
        logger.info("=" * 60)
        logger.info("TRACEABILITY CHECK SUMMARY")
        logger.info("=" * 60)
        
        # Scan results
        scan = results["scan_results"]
        logger.info(f"📁 Scanned: {scan['scanned_files']}/{scan['total_files']} files")
        logger.info(f"🔧 Found: {scan['services_found']} services, {scan['functions_found']} functions, {scan['tests_found']} tests")
        
        # Matrix results
        matrix = results["matrix_results"]
        logger.info(f"📊 Matrix: {matrix['total_entries']} requirements")
        logger.info(f"   ✅ GREEN: {matrix['green_count']}")
        logger.info(f"   🟡 YELLOW: {matrix['yellow_count']}")
        logger.info(f"   🔴 RED: {matrix['red_count']}")
        logger.info(f"   📈 Coverage: {matrix['overall_coverage']:.1f}%")
        
        # Orphan issues
        if matrix["orphan_code_count"] > 0 or matrix["orphan_requirements_count"] > 0:
            logger.warning(f"⚠️  Issues: {matrix['orphan_code_count']} orphan code, {matrix['orphan_requirements_count']} orphan requirements")
        
        # Gate results
        gates = results["gate_results"]
        if gates["passed"]:
            logger.info("✅ All enforcement gates PASSED")
        else:
            logger.error(f"❌ {gates['summary']['total_violations']} enforcement violations")
        
        # Export paths
        exports = matrix["exports"]
        logger.info(f"📄 Reports: {exports['html']}")
        logger.info("=" * 60)

def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(description="CI/CD Traceability Enforcement")
    parser.add_argument("--increment", default="mvp", help="Increment to check (default: mvp)")
    parser.add_argument("--enforce", action="store_true", help="Enforce gates (fail on violations)")
    parser.add_argument("--output-dir", default="trace", help="Output directory for reports")
    parser.add_argument("--scan-only", action="store_true", help="Only scan codebase, skip enforcement")
    parser.add_argument("--validate-headers", action="store_true", help="Only validate provenance headers")
    parser.add_argument("--neo4j-uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--neo4j-user", default="neo4j", help="Neo4j username")
    parser.add_argument("--neo4j-password", default="password", help="Neo4j password")
    parser.add_argument("--root-path", default=".", help="Root path to scan")
    
    args = parser.parse_args()
    
    # Configure Neo4j
    neo4j_config = Neo4jConfig(
        uri=args.neo4j_uri,
        username=args.neo4j_user,
        password=args.neo4j_password
    )
    
    # Initialize enforcer
    enforcer = TraceabilityEnforcer(args.root_path, neo4j_config)
    
    try:
        if args.validate_headers:
            # Header validation only
            logger.info("Running header validation only...")
            enforcer.neo4j_client.connect()
            validation_report = enforcer.validate_provenance_headers()
            logger.info(f"Header coverage: {validation_report['coverage_rate']:.1%}")
            if validation_report["files_without_headers"]:
                logger.warning(f"Files without headers: {len(validation_report['files_without_headers'])}")
                for file_path in validation_report["files_without_headers"][:10]:  # Show first 10
                    logger.warning(f"  - {file_path}")
        
        elif args.scan_only:
            # Scan only
            logger.info("Running codebase scan only...")
            enforcer.neo4j_client.connect()
            scan_results = enforcer.scan_and_sync_codebase()
            logger.info(f"Scan complete: {scan_results}")
        
        else:
            # Full check
            results = enforcer.run_full_check(
                increment=args.increment,
                enforce=args.enforce,
                output_dir=args.output_dir
            )
            
            # Exit with appropriate code
            if not results.get("success", False):
                sys.exit(1)
            elif args.enforce and not results["gate_results"]["passed"]:
                logger.error("Traceability enforcement failed - blocking deployment")
                sys.exit(1)
            else:
                logger.info("Traceability check completed successfully")
                sys.exit(0)
    
    except KeyboardInterrupt:
        logger.info("Traceability check interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Traceability check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
