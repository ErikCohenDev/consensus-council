"""Traceability matrix generation with complete REQ ↔ Code ↔ Tests ↔ Schema coverage."""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from ..database.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

class TraceabilityEntry(BaseModel):
    """Single entry in traceability matrix."""
    req_id: str
    frs_id: Optional[str] = None
    description: str
    implementing_code: List[str] = Field(default_factory=list)
    unit_tests: List[str] = Field(default_factory=list)
    integration_tests: List[str] = Field(default_factory=list)
    e2e_tests: List[str] = Field(default_factory=list)
    nfr_tests: List[str] = Field(default_factory=list)
    schemas: List[str] = Field(default_factory=list)
    contracts: List[str] = Field(default_factory=list)
    coverage_percentage: float = 0.0
    status: str = "RED"  # GREEN, YELLOW, RED
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    risk_level: str = "medium"  # low, medium, high
    priority: str = "M"  # M (must), S (should), C (could)

class OrphanReport(BaseModel):
    """Report of orphaned code and requirements."""
    orphan_code: List[Dict[str, Any]] = Field(default_factory=list)
    orphan_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    untested_code: List[Dict[str, Any]] = Field(default_factory=list)
    uncovered_schemas: List[Dict[str, Any]] = Field(default_factory=list)
    drift_warnings: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict)

class CoverageReport(BaseModel):
    """Coverage report by different dimensions."""
    overall_coverage: float = 0.0
    by_requirement_type: Dict[str, float] = Field(default_factory=dict)
    by_priority: Dict[str, float] = Field(default_factory=dict)
    by_increment: Dict[str, float] = Field(default_factory=dict)
    by_service: Dict[str, float] = Field(default_factory=dict)
    trend_data: List[Dict[str, Any]] = Field(default_factory=list)

class TraceabilityMatrix:
    """Complete traceability matrix generator and analyzer."""
    
    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j = neo4j_client
        self.matrix_cache = {}
        self.last_generated = None
    
    def generate_complete_matrix(
        self,
        increment_filter: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[TraceabilityEntry]:
        """Generate complete traceability matrix from Neo4j graph."""
        
        logger.info(f"Generating traceability matrix for increment: {increment_filter}")
        
        # Build complex Cypher query
        query = self._build_matrix_query(increment_filter, include_inactive)
        
        matrix_entries = []
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(query, {
                "increment": increment_filter or "mvp",
                "include_inactive": include_inactive
            })
            
            for record in result:
                entry_data = record["entry"]
                
                # Calculate status based on coverage
                status = self._calculate_status(
                    entry_data["implementing_code"],
                    entry_data["unit_tests"], 
                    entry_data["integration_tests"],
                    entry_data["e2e_tests"]
                )
                
                # Calculate coverage percentage
                coverage = self._calculate_coverage_percentage(entry_data)
                
                entry = TraceabilityEntry(
                    req_id=entry_data["req_id"],
                    frs_id=entry_data.get("frs_id"),
                    description=entry_data["description"],
                    implementing_code=entry_data["implementing_code"],
                    unit_tests=entry_data["unit_tests"],
                    integration_tests=entry_data["integration_tests"],
                    e2e_tests=entry_data["e2e_tests"],
                    nfr_tests=entry_data.get("nfr_tests", []),
                    schemas=entry_data.get("schemas", []),
                    contracts=entry_data.get("contracts", []),
                    coverage_percentage=coverage,
                    status=status,
                    risk_level=entry_data.get("risk_level", "medium"),
                    priority=entry_data.get("priority", "M")
                )
                
                matrix_entries.append(entry)
        
        # Sort by priority and status
        matrix_entries.sort(key=lambda x: (
            {"M": 0, "S": 1, "C": 2}.get(x.priority, 2),
            {"RED": 0, "YELLOW": 1, "GREEN": 2}.get(x.status, 0)
        ))
        
        self.matrix_cache[increment_filter or "all"] = matrix_entries
        self.last_generated = datetime.utcnow()
        
        logger.info(f"Generated matrix with {len(matrix_entries)} entries")
        
        return matrix_entries
    
    def _build_matrix_query(self, increment_filter: Optional[str], include_inactive: bool) -> str:
        """Build comprehensive Cypher query for traceability matrix."""
        
        increment_clause = ""
        if increment_filter:
            increment_clause = "AND (r)-[:INCLUDED_IN]->(:Increment {name: $increment})"
        
        inactive_clause = ""
        if not include_inactive:
            inactive_clause = "AND r.status <> 'inactive'"
        
        query = f"""
        MATCH (r:Requirement)
        WHERE r.type IN ['FR', 'NFR'] {increment_clause} {inactive_clause}
        
        // Get implementing code
        OPTIONAL MATCH (r)<-[:IMPLEMENTS]-(code)
        WHERE code:Service OR code:Module OR code:Class OR code:Function
        
        // Get unit tests
        OPTIONAL MATCH (code)<-[:VERIFIES]-(unit_test:Test)
        WHERE unit_test.test_type = 'unit'
        
        // Get integration tests  
        OPTIONAL MATCH (r)<-[:COVERS]-(integration_test:Test)
        WHERE integration_test.test_type = 'integration'
        
        // Get E2E tests
        OPTIONAL MATCH (r)<-[:VALIDATES]-(e2e_test:Test)
        WHERE e2e_test.test_type = 'e2e'
        
        // Get NFR tests (for NFR requirements)
        OPTIONAL MATCH (r)<-[:PROVES]-(nfr_test:Test)
        WHERE r.type = 'NFR' AND nfr_test.test_type = 'nfr'
        
        // Get related schemas
        OPTIONAL MATCH (code)-[:EXPOSES|CONSUMES]->(schema:Schema)
        
        // Get API contracts
        OPTIONAL MATCH (code)-[:IMPLEMENTS]->(contract:Contract)
        
        // Get FRS if linked
        OPTIONAL MATCH (r)<-[:DERIVES]-(frs:FRS)
        
        WITH r, frs,
             collect(DISTINCT code.name) as implementing_code,
             collect(DISTINCT unit_test.id) as unit_tests,
             collect(DISTINCT integration_test.id) as integration_tests,
             collect(DISTINCT e2e_test.id) as e2e_tests,
             collect(DISTINCT nfr_test.id) as nfr_tests,
             collect(DISTINCT schema.name) as schemas,
             collect(DISTINCT contract.name) as contracts
        
        RETURN {{
            req_id: r.id,
            frs_id: frs.id,
            description: r.description,
            priority: r.priority,
            risk_level: CASE 
                WHEN r.criticality > 0.8 THEN 'high'
                WHEN r.criticality > 0.5 THEN 'medium' 
                ELSE 'low' END,
            implementing_code: implementing_code,
            unit_tests: unit_tests,
            integration_tests: integration_tests,
            e2e_tests: e2e_tests,
            nfr_tests: nfr_tests,
            schemas: schemas,
            contracts: contracts
        }} as entry
        ORDER BY r.priority, r.id
        """
        
        return query
    
    def _calculate_status(
        self,
        implementing_code: List[str],
        unit_tests: List[str],
        integration_tests: List[str],
        e2e_tests: List[str]
    ) -> str:
        """Calculate status based on implementation and test coverage."""
        
        has_code = len(implementing_code) > 0
        has_unit_tests = len(unit_tests) > 0
        has_integration_tests = len(integration_tests) > 0
        
        if has_code and has_unit_tests and has_integration_tests:
            return "GREEN"
        elif has_code and (has_unit_tests or has_integration_tests):
            return "YELLOW"
        else:
            return "RED"
    
    def _calculate_coverage_percentage(self, entry_data: Dict[str, Any]) -> float:
        """Calculate coverage percentage for a requirement."""
        
        total_coverage_points = 0
        max_points = 0
        
        # Implementation coverage (40 points max)
        if entry_data["implementing_code"]:
            total_coverage_points += 40
        max_points += 40
        
        # Unit test coverage (30 points max)
        if entry_data["unit_tests"]:
            total_coverage_points += 30
        max_points += 30
        
        # Integration test coverage (20 points max)
        if entry_data["integration_tests"]:
            total_coverage_points += 20
        max_points += 20
        
        # E2E test coverage (10 points max)
        if entry_data["e2e_tests"]:
            total_coverage_points += 10
        max_points += 10
        
        return (total_coverage_points / max_points) * 100 if max_points > 0 else 0.0
    
    def find_orphans(self) -> OrphanReport:
        """Find orphaned code, requirements, and other inconsistencies."""
        
        logger.info("Scanning for orphaned artifacts and inconsistencies")
        
        report = OrphanReport()
        
        # Find orphan code (not linked to any requirement)
        orphan_code_query = """
        MATCH (code)
        WHERE (code:Service OR code:Module OR code:Class OR code:Function)
        AND NOT (code)-[:IMPLEMENTS]->(:Requirement)
        AND NOT code.name CONTAINS 'test'
        RETURN {
            type: labels(code)[0],
            id: code.id,
            name: code.name,
            file_path: code.file_path,
            complexity: code.complexity
        } as orphan
        ORDER BY orphan.complexity DESC
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(orphan_code_query)
            report.orphan_code = [record["orphan"] for record in result]
        
        # Find orphan requirements (no implementing code)
        orphan_req_query = """
        MATCH (r:Requirement)
        WHERE r.status = 'active'
        AND NOT (r)<-[:IMPLEMENTS]-()
        RETURN {
            req_id: r.id,
            description: r.description,
            priority: r.priority,
            stage: r.stage,
            created_at: r.created_at
        } as orphan
        ORDER BY r.priority, r.created_at
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(orphan_req_query)
            report.orphan_requirements = [record["orphan"] for record in result]
        
        # Find untested code
        untested_code_query = """
        MATCH (code)
        WHERE (code:Service OR code:Function OR code:Class)
        AND NOT (code)<-[:VERIFIES]-(:Test)
        AND (code)-[:IMPLEMENTS]->(:Requirement)
        RETURN {
            type: labels(code)[0],
            id: code.id, 
            name: code.name,
            file_path: code.file_path,
            implements: [(code)-[:IMPLEMENTS]->(r:Requirement) | r.id]
        } as untested
        ORDER BY size(untested.implements) DESC
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(untested_code_query)
            report.untested_code = [record["untested"] for record in result]
        
        # Find uncovered schemas (no contract tests)
        uncovered_schema_query = """
        MATCH (s:Schema)
        WHERE NOT (s)<-[:VALIDATES]-(:Test)
        RETURN {
            name: s.name,
            type: s.type,
            file_path: s.file_path,
            exposed_by: [(s)<-[:EXPOSES]-(code) | code.name]
        } as uncovered
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(uncovered_schema_query)
            report.uncovered_schemas = [record["uncovered"] for record in result]
        
        # Generate summary
        report.summary = {
            "orphan_code_count": len(report.orphan_code),
            "orphan_requirements_count": len(report.orphan_requirements),
            "untested_code_count": len(report.untested_code),
            "uncovered_schemas_count": len(report.uncovered_schemas),
            "total_issues": (
                len(report.orphan_code) + 
                len(report.orphan_requirements) + 
                len(report.untested_code) + 
                len(report.uncovered_schemas)
            )
        }
        
        logger.info(f"Found {report.summary['total_issues']} total traceability issues")
        
        return report
    
    def generate_coverage_report(self, increment: str = "mvp") -> CoverageReport:
        """Generate comprehensive coverage report."""
        
        logger.info(f"Generating coverage report for {increment}")
        
        report = CoverageReport()
        
        # Get overall coverage
        overall_query = """
        MATCH (r:Requirement)-[:INCLUDED_IN]->(:Increment {name: $increment})
        WITH count(r) as total_reqs
        MATCH (r:Requirement)-[:INCLUDED_IN]->(:Increment {name: $increment})
        WHERE (r)<-[:IMPLEMENTS]-() AND (r)<-[:COVERS|VALIDATES]-(:Test)
        WITH total_reqs, count(r) as covered_reqs
        RETURN CASE WHEN total_reqs > 0 THEN toFloat(covered_reqs) / total_reqs ELSE 0.0 END * 100 as coverage
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(overall_query, {"increment": increment})
            record = result.single()
            report.overall_coverage = record["coverage"] if record else 0.0
        
        # Coverage by requirement type
        type_coverage_query = """
        MATCH (r:Requirement)-[:INCLUDED_IN]->(:Increment {name: $increment})
        WITH r.type as req_type, count(r) as total
        MATCH (r:Requirement {type: req_type})-[:INCLUDED_IN]->(:Increment {name: $increment})
        WHERE (r)<-[:IMPLEMENTS]-() AND (r)<-[:COVERS|VALIDATES]-(:Test)
        WITH req_type, total, count(r) as covered
        RETURN req_type, CASE WHEN total > 0 THEN toFloat(covered) / total ELSE 0.0 END * 100 as coverage
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(type_coverage_query, {"increment": increment})
            for record in result:
                report.by_requirement_type[record["req_type"]] = record["coverage"]
        
        # Coverage by priority
        priority_coverage_query = """
        MATCH (r:Requirement)-[:INCLUDED_IN]->(:Increment {name: $increment})
        WITH r.priority as priority, count(r) as total
        MATCH (r:Requirement {priority: priority})-[:INCLUDED_IN]->(:Increment {name: $increment})
        WHERE (r)<-[:IMPLEMENTS]-() AND (r)<-[:COVERS|VALIDATES]-(:Test)
        WITH priority, total, count(r) as covered
        RETURN priority, CASE WHEN total > 0 THEN toFloat(covered) / total ELSE 0.0 END * 100 as coverage
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(priority_coverage_query, {"increment": increment})
            for record in result:
                report.by_priority[record["priority"]] = record["coverage"]
        
        # Coverage by service
        service_coverage_query = """
        MATCH (s:Service)-[:IMPLEMENTS]->(r:Requirement)-[:INCLUDED_IN]->(:Increment {name: $increment})
        WITH s.name as service, count(DISTINCT r) as total_reqs
        MATCH (s:Service {name: service})-[:IMPLEMENTS]->(r:Requirement)-[:INCLUDED_IN]->(:Increment {name: $increment})
        WHERE (s)<-[:VERIFIES]-(:Test)
        WITH service, total_reqs, count(DISTINCT r) as covered_reqs
        RETURN service, CASE WHEN total_reqs > 0 THEN toFloat(covered_reqs) / total_reqs ELSE 0.0 END * 100 as coverage
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(service_coverage_query, {"increment": increment})
            for record in result:
                report.by_service[record["service"]] = record["coverage"]
        
        return report
    
    def export_matrix_csv(
        self, 
        matrix_entries: List[TraceabilityEntry], 
        output_path: str
    ) -> str:
        """Export traceability matrix to CSV format."""
        
        csv_path = Path(output_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'REQ_ID', 'FRS_ID', 'Description', 'Priority', 'Status',
                'Implementing_Code', 'Unit_Tests', 'Integration_Tests', 'E2E_Tests',
                'Schemas', 'Contracts', 'Coverage_%', 'Risk_Level', 'Last_Updated'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in matrix_entries:
                writer.writerow({
                    'REQ_ID': entry.req_id,
                    'FRS_ID': entry.frs_id or '',
                    'Description': entry.description,
                    'Priority': entry.priority,
                    'Status': entry.status,
                    'Implementing_Code': '; '.join(entry.implementing_code),
                    'Unit_Tests': '; '.join(entry.unit_tests),
                    'Integration_Tests': '; '.join(entry.integration_tests),
                    'E2E_Tests': '; '.join(entry.e2e_tests),
                    'Schemas': '; '.join(entry.schemas),
                    'Contracts': '; '.join(entry.contracts),
                    'Coverage_%': f"{entry.coverage_percentage:.1f}",
                    'Risk_Level': entry.risk_level,
                    'Last_Updated': entry.last_updated.strftime('%Y-%m-%d %H:%M')
                })
        
        logger.info(f"Exported traceability matrix to {csv_path}")
        return str(csv_path)
    
    def export_matrix_json(
        self, 
        matrix_entries: List[TraceabilityEntry], 
        output_path: str
    ) -> str:
        """Export traceability matrix to JSON format."""
        
        json_path = Path(output_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        matrix_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_entries": len(matrix_entries),
            "summary": {
                "green": len([e for e in matrix_entries if e.status == "GREEN"]),
                "yellow": len([e for e in matrix_entries if e.status == "YELLOW"]),
                "red": len([e for e in matrix_entries if e.status == "RED"])
            },
            "entries": [entry.dict() for entry in matrix_entries]
        }
        
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(matrix_data, jsonfile, indent=2, default=str)
        
        logger.info(f"Exported traceability matrix to {json_path}")
        return str(json_path)
    
    def generate_html_dashboard(
        self, 
        matrix_entries: List[TraceabilityEntry],
        coverage_report: CoverageReport,
        orphan_report: OrphanReport,
        output_path: str
    ) -> str:
        """Generate HTML dashboard with traceability overview."""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Traceability Matrix Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .summary { display: flex; gap: 20px; margin-bottom: 30px; }
                .card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; min-width: 150px; }
                .green { background-color: #d4edda; }
                .yellow { background-color: #fff3cd; }
                .red { background-color: #f8d7da; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .status-green { background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; }
                .status-yellow { background-color: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; }
                .status-red { background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>Traceability Matrix Dashboard</h1>
            
            <div class="summary">
                <div class="card green">
                    <h3>GREEN</h3>
                    <p>{green_count} requirements</p>
                    <p>Full coverage</p>
                </div>
                <div class="card yellow">
                    <h3>YELLOW</h3>
                    <p>{yellow_count} requirements</p>
                    <p>Partial coverage</p>
                </div>
                <div class="card red">
                    <h3>RED</h3>
                    <p>{red_count} requirements</p>
                    <p>Missing coverage</p>
                </div>
                <div class="card">
                    <h3>Overall Coverage</h3>
                    <p>{overall_coverage:.1f}%</p>
                    <p>Requirements covered</p>
                </div>
            </div>
            
            <h2>Issues Summary</h2>
            <ul>
                <li>Orphan Code: {orphan_code_count}</li>
                <li>Orphan Requirements: {orphan_req_count}</li>
                <li>Untested Code: {untested_code_count}</li>
                <li>Uncovered Schemas: {uncovered_schema_count}</li>
            </ul>
            
            <h2>Traceability Matrix</h2>
            <table>
                <thead>
                    <tr>
                        <th>REQ ID</th>
                        <th>Description</th>
                        <th>Priority</th>
                        <th>Status</th>
                        <th>Code</th>
                        <th>Tests</th>
                        <th>Coverage</th>
                    </tr>
                </thead>
                <tbody>
                    {matrix_rows}
                </tbody>
            </table>
            
            <p><em>Generated at {timestamp}</em></p>
        </body>
        </html>
        """
        
        # Count statuses
        green_count = len([e for e in matrix_entries if e.status == "GREEN"])
        yellow_count = len([e for e in matrix_entries if e.status == "YELLOW"])
        red_count = len([e for e in matrix_entries if e.status == "RED"])
        
        # Generate table rows
        matrix_rows = []
        for entry in matrix_entries[:50]:  # Limit to first 50 for readability
            status_class = f"status-{entry.status.lower()}"
            code_count = len(entry.implementing_code)
            test_count = len(entry.unit_tests) + len(entry.integration_tests) + len(entry.e2e_tests)
            
            row = f"""
                <tr>
                    <td>{entry.req_id}</td>
                    <td>{entry.description[:60]}...</td>
                    <td>{entry.priority}</td>
                    <td><span class="{status_class}">{entry.status}</span></td>
                    <td>{code_count} artifacts</td>
                    <td>{test_count} tests</td>
                    <td>{entry.coverage_percentage:.1f}%</td>
                </tr>
            """
            matrix_rows.append(row)
        
        html_content = html_template.format(
            green_count=green_count,
            yellow_count=yellow_count,
            red_count=red_count,
            overall_coverage=coverage_report.overall_coverage,
            orphan_code_count=orphan_report.summary.get("orphan_code_count", 0),
            orphan_req_count=orphan_report.summary.get("orphan_requirements_count", 0),
            untested_code_count=orphan_report.summary.get("untested_code_count", 0),
            uncovered_schema_count=orphan_report.summary.get("uncovered_schemas_count", 0),
            matrix_rows='\n'.join(matrix_rows),
            timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        
        html_path = Path(output_path)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_content, encoding='utf-8')
        
        logger.info(f"Generated HTML dashboard at {html_path}")
        return str(html_path)
    
    def validate_increment_readiness(self, increment: str) -> Dict[str, Any]:
        """Validate if an increment is ready for release based on coverage."""
        
        matrix = self.generate_complete_matrix(increment_filter=increment)
        coverage_report = self.generate_coverage_report(increment)
        orphan_report = self.find_orphans()
        
        # Define readiness criteria
        criteria = {
            "min_overall_coverage": 85.0,
            "min_critical_coverage": 100.0,
            "max_orphan_code": 0,
            "max_orphan_requirements": 0,
            "max_untested_critical": 0
        }
        
        # Calculate readiness
        critical_entries = [e for e in matrix if e.priority == "M"]
        critical_coverage = sum(e.coverage_percentage for e in critical_entries) / len(critical_entries) if critical_entries else 0
        
        readiness_check = {
            "increment": increment,
            "overall_coverage": coverage_report.overall_coverage,
            "critical_coverage": critical_coverage,
            "orphan_code_count": orphan_report.summary.get("orphan_code_count", 0),
            "orphan_requirements_count": orphan_report.summary.get("orphan_requirements_count", 0),
            "untested_code_count": orphan_report.summary.get("untested_code_count", 0),
            "criteria": criteria,
            "passed_checks": 0,
            "total_checks": len(criteria),
            "ready_for_release": False,
            "blocking_issues": []
        }
        
        # Check each criterion
        if coverage_report.overall_coverage >= criteria["min_overall_coverage"]:
            readiness_check["passed_checks"] += 1
        else:
            readiness_check["blocking_issues"].append(
                f"Overall coverage {coverage_report.overall_coverage:.1f}% < {criteria['min_overall_coverage']}%"
            )
        
        if critical_coverage >= criteria["min_critical_coverage"]:
            readiness_check["passed_checks"] += 1
        else:
            readiness_check["blocking_issues"].append(
                f"Critical coverage {critical_coverage:.1f}% < {criteria['min_critical_coverage']}%"
            )
        
        if orphan_report.summary.get("orphan_code_count", 0) <= criteria["max_orphan_code"]:
            readiness_check["passed_checks"] += 1
        else:
            readiness_check["blocking_issues"].append(
                f"Orphan code count {orphan_report.summary['orphan_code_count']} > {criteria['max_orphan_code']}"
            )
        
        if orphan_report.summary.get("orphan_requirements_count", 0) <= criteria["max_orphan_requirements"]:
            readiness_check["passed_checks"] += 1
        else:
            readiness_check["blocking_issues"].append(
                f"Orphan requirements {orphan_report.summary['orphan_requirements_count']} > {criteria['max_orphan_requirements']}"
            )
        
        if orphan_report.summary.get("untested_code_count", 0) <= criteria["max_untested_critical"]:
            readiness_check["passed_checks"] += 1
        else:
            readiness_check["blocking_issues"].append(
                f"Untested code count {orphan_report.summary['untested_code_count']} > {criteria['max_untested_critical']}"
            )
        
        readiness_check["ready_for_release"] = readiness_check["passed_checks"] == readiness_check["total_checks"]
        
        return readiness_check
