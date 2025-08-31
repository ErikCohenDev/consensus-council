"""Code Artifact Graph models for provenance and traceability."""

from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any, Set
from pydantic import BaseModel, Field
from datetime import datetime


class ArtifactType(str, Enum):
    """Types of code artifacts in the system."""
    MODULE = "module"
    SERVICE = "service"
    CLASS = "class"
    FILE = "file"
    SCHEMA = "schema"
    TEST = "test"
    BUILD_TARGET = "build_target"
    PIPELINE = "pipeline"
    REQUIREMENT = "requirement"
    NFR = "nfr"
    FEATURE_SPEC = "feature_spec"


class ArtifactStatus(str, Enum):
    """Development status of code artifacts."""
    IDEATED = "ideated"
    STUBBED = "stubbed"
    IMPLEMENTED = "implemented"
    TESTED = "tested"


class DriftType(str, Enum):
    """Types of drift between artifacts and requirements."""
    REQUIREMENT_DRIFT = "requirement_drift"
    IMPLEMENTATION_DRIFT = "implementation_drift"
    TEST_DRIFT = "test_drift"
    INTERFACE_DRIFT = "interface_drift"
    DEPENDENCY_DRIFT = "dependency_drift"


class TraceabilityType(str, Enum):
    """Types of traceability links between artifacts."""
    IMPLEMENTS = "implements"
    VERIFIES = "verifies"
    DEPENDS_ON = "depends_on"
    TRACES_TO = "traces_to"
    VALIDATES = "validates"
    DEPRECATED = "deprecated"


class RelationType(str, Enum):
    """Types of relationships between code artifacts."""
    IMPLEMENTS = "implements"
    DEPENDS_ON = "depends_on"
    EXPOSES = "exposes"
    CONSUMES = "consumes"
    VERIFIED_BY = "verified_by"
    GENERATED_FROM = "generated_from"
    EVIDENCE = "evidence"
    OWNED_BY = "owned_by"
    CONTRACTS = "contracts"


class ProvenanceData(BaseModel):
    """Provenance metadata for code artifacts."""
    source: str = Field(description="Source document or spec ID")
    tool: str = Field(description="Tool that generated this artifact")
    version: str = Field(description="Tool/spec version")
    timestamp: datetime = Field(default_factory=datetime.now)
    commit_hash: Optional[str] = None


class CoverageData(BaseModel):
    """Test coverage data for code artifacts."""
    lines_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    branches_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    by_requirement: Dict[str, float] = Field(default_factory=dict, description="Coverage by REQ ID")


class RiskData(BaseModel):
    """Risk assessment for code artifacts."""
    security: float = Field(default=0.0, ge=0.0, le=1.0, description="Security risk level")
    complexity: float = Field(default=0.0, ge=0.0, le=1.0, description="Implementation complexity")
    change_frequency: float = Field(default=0.0, ge=0.0, le=1.0, description="Code churn risk")


class CodeArtifactMeta(BaseModel):
    """Metadata for code artifacts."""
    trace_ids: List[str] = Field(default_factory=list, description="REQ/NFR/FRS IDs this artifact traces to")
    provenance: Optional[ProvenanceData] = None
    coverage: Optional[CoverageData] = None
    risk: Optional[RiskData] = None
    status: ArtifactStatus = ArtifactStatus.IDEATED
    owners: List[str] = Field(default_factory=list, description="Team/individual owners")
    file_path: Optional[str] = None
    generated: bool = Field(default=False, description="Whether this artifact is code-generated")


class CodeArtifact(BaseModel):
    """Code artifact node in the system."""
    id: str = Field(description="Unique artifact ID (e.g., SVC-101, TEST-U-045)")
    name: str = Field(description="Human readable name")
    type: ArtifactType
    description: str
    meta: CodeArtifactMeta = Field(default_factory=CodeArtifactMeta)


class CodeRelationship(BaseModel):
    """Relationship between code artifacts."""
    id: str
    source_id: str
    target_id: str
    type: RelationType
    description: str
    contract_reference: Optional[str] = None  # Reference to schema/API spec
    strength: float = Field(default=1.0, ge=0.0, le=1.0)


class CodeArtifactGraph(BaseModel):
    """Complete code artifact graph with provenance tracking."""
    artifacts: List[CodeArtifact]
    relationships: List[CodeRelationship]
    repo_root: str
    last_updated: datetime = Field(default_factory=datetime.now)
    trace_matrix_path: str = Field(default="trace/matrix.csv")


class RequirementSpec(BaseModel):
    """Requirement specification with test criteria."""
    id: str = Field(description="REQ-### identifier")
    title: str
    description: str
    acceptance_criteria: List[str]
    nfr_links: List[str] = Field(default_factory=list, description="Related NFR IDs")
    contracts: Dict[str, str] = Field(default_factory=dict, description="API/Schema contract references")
    priority: int = Field(default=1, ge=1, le=5)
    increment: str = Field(description="PRD increment this belongs to (MVP, R1, R2)")


class NonFunctionalRequirement(BaseModel):
    """Non-functional requirement with measurable criteria."""
    id: str = Field(description="NFR-### identifier")
    title: str
    description: str
    category: str = Field(description="performance|security|usability|reliability|maintainability")
    threshold: str = Field(description="Measurable threshold (e.g., '≤300ms p95', '≥99.9% uptime')")
    test_strategy: str = Field(description="How this NFR will be verified")
    related_reqs: List[str] = Field(default_factory=list, description="Related REQ IDs")


class FeatureRequirementSpec(BaseModel):
    """Feature-level requirement specification."""
    id: str = Field(description="FRS-FEAT-### identifier")
    title: str
    description: str
    parent_prd: str = Field(description="Parent PRD increment")
    user_stories: List[str]
    acceptance_criteria: List[str]
    edge_cases: List[str] = Field(default_factory=list)
    nfr_slice: List[str] = Field(default_factory=list, description="NFR IDs that apply to this feature")
    success_metrics: List[str] = Field(default_factory=list)


class TraceMatrixEntry(BaseModel):
    """Single entry in the traceability matrix."""
    req_id: str
    code_artifacts: List[str] = Field(description="Code artifact IDs implementing this requirement")
    test_artifacts: List[str] = Field(description="Test artifact IDs verifying this requirement")
    schema_artifacts: List[str] = Field(description="Schema artifact IDs defining contracts")
    status: str = Field(description="green|yellow|red based on completeness")
    coverage_percent: float = Field(ge=0.0, le=100.0)
    last_verified: datetime = Field(default_factory=datetime.now)


class TraceMatrix(BaseModel):
    """Complete traceability matrix for requirements to implementation."""
    entries: List[TraceMatrixEntry]
    increment: str = Field(description="PRD increment this matrix covers")
    generated_at: datetime = Field(default_factory=datetime.now)
    coverage_threshold: float = Field(default=80.0, description="Required coverage threshold")
    
    def get_orphaned_requirements(self) -> List[str]:
        """Find requirements with no implementing code."""
        return [entry.req_id for entry in self.entries if not entry.code_artifacts]
    
    def get_untested_code(self) -> List[str]:
        """Find code artifacts with no test coverage."""
        untested = []
        for entry in self.entries:
            for code_id in entry.code_artifacts:
                if not entry.test_artifacts:
                    untested.append(code_id)
        return untested
    
    def get_coverage_gaps(self) -> List[TraceMatrixEntry]:
        """Find entries below coverage threshold."""
        return [entry for entry in self.entries if entry.coverage_percent < self.coverage_threshold]


class CodeGenConfig(BaseModel):
    """Configuration for spec-to-code generation."""
    target_language: str = Field(description="typescript|python|java|go")
    output_directory: str
    template_directory: str
    preserve_manual_edits: bool = Field(default=True)
    generate_tests: bool = Field(default=True)
    generate_schemas: bool = Field(default=True)
    id_prefix_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
            "SVC": "services",
            "MOD": "modules", 
            "TEST-U": "tests/unit",
            "TEST-I": "tests/integration",
            "TEST-E": "tests/e2e"
        }
    )


class DriftDetectionResult(BaseModel):
    """Result of spec-to-code drift detection."""
    orphaned_code: List[str] = Field(description="Code artifacts with no spec reference")
    missing_implementations: List[str] = Field(description="Specs with no implementing code")
    outdated_artifacts: List[str] = Field(description="Code older than spec version")
    contract_violations: List[str] = Field(description="Schema/API contract mismatches")
    drift_score: float = Field(ge=0.0, le=1.0, description="Overall drift level (0=aligned, 1=major drift)")


class RepoStructureMapping(BaseModel):
    """Mapping between logical artifacts and physical file structure."""
    artifact_to_path: Dict[str, str] = Field(description="Artifact ID to file path mapping")
    path_to_artifact: Dict[str, str] = Field(description="File path to artifact ID mapping")
    directory_conventions: Dict[ArtifactType, str] = Field(
        default_factory=lambda: {
            ArtifactType.SERVICE: "src/services",
            ArtifactType.MODULE: "src/modules",
            ArtifactType.CLASS: "src/classes",
            ArtifactType.SCHEMA: "spec/schemas",
            ArtifactType.TEST: "tests",
            ArtifactType.REQUIREMENT: "spec/requirements",
            ArtifactType.NFR: "spec/nfr",
            ArtifactType.FEATURE_SPEC: "spec/features"
        }
    )
    
    def get_artifact_path(self, artifact_id: str, artifact_type: ArtifactType) -> str:
        """Generate file path for artifact based on ID and type."""
        if artifact_id in self.artifact_to_path:
            return self.artifact_to_path[artifact_id]
        
        base_dir = self.directory_conventions.get(artifact_type, "src")
        
        # Generate path based on artifact ID patterns
        if artifact_id.startswith("SVC-"):
            return f"{base_dir}/{artifact_id.lower()}.ts"
        elif artifact_id.startswith("TEST-U-"):
            return f"tests/unit/{artifact_id.lower()}.spec.ts"
        elif artifact_id.startswith("TEST-I-"):
            return f"tests/integration/{artifact_id.lower()}.spec.ts"
        elif artifact_id.startswith("REQ-"):
            return f"spec/requirements/{artifact_id}.yaml"
        elif artifact_id.startswith("NFR-"):
            return f"spec/nfr/{artifact_id}.yaml"
        elif artifact_id.startswith("FRS-FEAT-"):
            return f"spec/features/{artifact_id}.yaml"
        else:
            return f"{base_dir}/{artifact_id.lower()}"


class ProvenanceHeader(BaseModel):
    """Standard provenance header for generated files."""
    artifact_id: str
    implements: List[str] = Field(description="REQ/NFR/FRS IDs this artifact implements")
    contracts: List[str] = Field(description="Schema/API contract references")
    verified_by: List[str] = Field(description="Test artifact IDs that verify this")
    generated_by: str = Field(description="Tool and version that generated this")
    generated_at: datetime = Field(default_factory=datetime.now)
    manual_edits_allowed: bool = Field(default=True)
    
    def to_comment_block(self, comment_style: str = "//") -> str:
        """Generate comment block for file header."""
        lines = [
            f"{comment_style} {self.artifact_id}",
            f"{comment_style} Implements: {', '.join(self.implements)}",
            f"{comment_style} Contracts: {', '.join(self.contracts)}",
            f"{comment_style} VerifiedBy: {', '.join(self.verified_by)}",
            f"{comment_style} Generated: {self.generated_by}",
            f"{comment_style} Timestamp: {self.generated_at.isoformat()}",
        ]
        
        if not self.manual_edits_allowed:
            lines.append(f"{comment_style} WARNING: Auto-generated file - manual edits will be overwritten")
        
        return "\n".join(lines)


class CodeArtifactGraphBuilder:
    """Builds and maintains the code artifact graph from repository structure."""
    
    def __init__(self, repo_root: str):
        self.repo_root = repo_root
        self.structure_mapping = RepoStructureMapping()
    
    def scan_repository(self) -> CodeArtifactGraph:
        """Scan repository and build artifact graph."""
        artifacts = []
        relationships = []
        
        # Scan different artifact types
        artifacts.extend(self._scan_source_files())
        artifacts.extend(self._scan_test_files())
        artifacts.extend(self._scan_schema_files())
        artifacts.extend(self._scan_spec_files())
        
        # Build relationships from file analysis
        relationships.extend(self._analyze_dependencies(artifacts))
        relationships.extend(self._analyze_test_relationships(artifacts))
        relationships.extend(self._analyze_contract_relationships(artifacts))
        
        return CodeArtifactGraph(
            artifacts=artifacts,
            relationships=relationships,
            repo_root=self.repo_root
        )
    
    def _scan_source_files(self) -> List[CodeArtifact]:
        """Scan source code files and extract artifacts."""
        # Implementation would scan src/ directory
        # Parse file headers for provenance data
        # Extract class/service definitions
        return []  # Placeholder
    
    def _scan_test_files(self) -> List[CodeArtifact]:
        """Scan test files and extract test artifacts."""
        # Implementation would scan tests/ directory
        # Parse test descriptions and trace IDs
        return []  # Placeholder
    
    def _scan_schema_files(self) -> List[CodeArtifact]:
        """Scan schema and API specification files."""
        # Implementation would scan spec/schemas/ and api/ directories
        return []  # Placeholder
    
    def _scan_spec_files(self) -> List[CodeArtifact]:
        """Scan requirement and feature specification files."""
        # Implementation would scan spec/requirements/ and spec/features/
        return []  # Placeholder
    
    def _analyze_dependencies(self, artifacts: List[CodeArtifact]) -> List[CodeRelationship]:
        """Analyze code dependencies between artifacts."""
        # Implementation would parse import statements, etc.
        return []  # Placeholder
    
    def _analyze_test_relationships(self, artifacts: List[CodeArtifact]) -> List[CodeRelationship]:
        """Analyze test-to-code verification relationships."""
        # Implementation would parse test files for what they verify
        return []  # Placeholder
    
    def _analyze_contract_relationships(self, artifacts: List[CodeArtifact]) -> List[CodeRelationship]:
        """Analyze schema/API contract relationships."""
        # Implementation would parse OpenAPI specs, JSON schemas
        return []  # Placeholder


class TraceMatrixBuilder:
    """Builds and maintains traceability matrix between specs and implementation."""
    
    def __init__(self, code_graph: CodeArtifactGraph):
        self.code_graph = code_graph
    
    def build_trace_matrix(self, increment: str = "MVP") -> TraceMatrix:
        """Build complete traceability matrix for given increment."""
        entries = []
        
        # Find all requirements for this increment
        req_artifacts = [
            a for a in self.code_graph.artifacts 
            if a.type == ArtifactType.REQUIREMENT
        ]
        
        for req_artifact in req_artifacts:
            entry = self._build_matrix_entry(req_artifact)
            entries.append(entry)
        
        return TraceMatrix(
            entries=entries,
            increment=increment
        )
    
    def _build_matrix_entry(self, req_artifact: CodeArtifact) -> TraceMatrixEntry:
        """Build single matrix entry for requirement."""
        req_id = req_artifact.id
        
        # Find implementing code artifacts
        code_artifacts = self._find_implementing_artifacts(req_id)
        
        # Find verifying test artifacts
        test_artifacts = self._find_verifying_tests(req_id, code_artifacts)
        
        # Find related schema artifacts
        schema_artifacts = self._find_related_schemas(req_id)
        
        # Calculate overall status and coverage
        status = self._calculate_entry_status(code_artifacts, test_artifacts)
        coverage = self._calculate_entry_coverage(req_id, code_artifacts, test_artifacts)
        
        return TraceMatrixEntry(
            req_id=req_id,
            code_artifacts=code_artifacts,
            test_artifacts=test_artifacts,
            schema_artifacts=schema_artifacts,
            status=status,
            coverage_percent=coverage
        )
    
    def _find_implementing_artifacts(self, req_id: str) -> List[str]:
        """Find code artifacts that implement given requirement."""
        implementing = []
        
        for artifact in self.code_graph.artifacts:
            if (artifact.type in [ArtifactType.SERVICE, ArtifactType.CLASS, ArtifactType.MODULE] and
                req_id in artifact.meta.trace_ids):
                implementing.append(artifact.id)
        
        return implementing
    
    def _find_verifying_tests(self, req_id: str, code_artifacts: List[str]) -> List[str]:
        """Find test artifacts that verify given requirement or its implementing code."""
        verifying = []
        
        for artifact in self.code_graph.artifacts:
            if artifact.type == ArtifactType.TEST:
                # Direct requirement verification
                if req_id in artifact.meta.trace_ids:
                    verifying.append(artifact.id)
                # Indirect verification through code artifacts
                elif any(code_id in artifact.meta.trace_ids for code_id in code_artifacts):
                    verifying.append(artifact.id)
        
        return verifying
    
    def _find_related_schemas(self, req_id: str) -> List[str]:
        """Find schema artifacts related to requirement."""
        related = []
        
        for artifact in self.code_graph.artifacts:
            if (artifact.type == ArtifactType.SCHEMA and
                req_id in artifact.meta.trace_ids):
                related.append(artifact.id)
        
        return related
    
    def _calculate_entry_status(self, code_artifacts: List[str], test_artifacts: List[str]) -> str:
        """Calculate status for matrix entry."""
        if not code_artifacts:
            return "red"  # No implementation
        elif not test_artifacts:
            return "yellow"  # Implemented but not tested
        else:
            return "green"  # Implemented and tested
    
    def _calculate_entry_coverage(self, req_id: str, code_artifacts: List[str], 
                                test_artifacts: List[str]) -> float:
        """Calculate test coverage for matrix entry."""
        if not code_artifacts or not test_artifacts:
            return 0.0
        
        # Simplified coverage calculation
        # Real implementation would aggregate actual test coverage data
        return 85.0  # Placeholder


class DriftDetector:
    """Detects drift between specifications and implementation."""
    
    def __init__(self, code_graph: CodeArtifactGraph, trace_matrix: TraceMatrix):
        self.code_graph = code_graph
        self.trace_matrix = trace_matrix
    
    def detect_drift(self) -> DriftDetectionResult:
        """Detect various types of spec-to-code drift."""
        
        orphaned_code = self._find_orphaned_code()
        missing_implementations = self._find_missing_implementations()
        outdated_artifacts = self._find_outdated_artifacts()
        contract_violations = self._find_contract_violations()
        
        # Calculate overall drift score
        total_artifacts = len(self.code_graph.artifacts)
        drift_count = len(orphaned_code) + len(missing_implementations) + len(outdated_artifacts)
        drift_score = drift_count / max(1, total_artifacts)
        
        return DriftDetectionResult(
            orphaned_code=orphaned_code,
            missing_implementations=missing_implementations,
            outdated_artifacts=outdated_artifacts,
            contract_violations=contract_violations,
            drift_score=min(1.0, drift_score)
        )
    
    def _find_orphaned_code(self) -> List[str]:
        """Find code artifacts with no traceability to specs."""
        orphaned = []
        
        for artifact in self.code_graph.artifacts:
            if (artifact.type in [ArtifactType.SERVICE, ArtifactType.CLASS, ArtifactType.MODULE] and
                not artifact.meta.trace_ids and
                not artifact.meta.generated):
                orphaned.append(artifact.id)
        
        return orphaned
    
    def _find_missing_implementations(self) -> List[str]:
        """Find requirements with no implementing code."""
        return self.trace_matrix.get_orphaned_requirements()
    
    def _find_outdated_artifacts(self) -> List[str]:
        """Find artifacts older than their source specs."""
        # Implementation would compare file timestamps
        return []  # Placeholder
    
    def _find_contract_violations(self) -> List[str]:
        """Find schema/API contract violations."""
        # Implementation would run contract tests
        return []  # Placeholder


class ProvenanceTracker:
    """Tracks provenance and lineage of code artifacts."""
    
    def __init__(self, code_graph: CodeArtifactGraph):
        self.code_graph = code_graph
    
    def trace_artifact_lineage(self, artifact_id: str) -> Dict[str, Any]:
        """Trace complete lineage of an artifact back to originating specs."""
        artifact = next((a for a in self.code_graph.artifacts if a.id == artifact_id), None)
        if not artifact:
            return {"error": f"Artifact {artifact_id} not found"}
        
        lineage = {
            "artifact": artifact.dict(),
            "implements": [],
            "generated_from": [],
            "verified_by": [],
            "contracts": [],
            "upstream_trace": []
        }
        
        # Find implementing relationships
        for rel in self.code_graph.relationships:
            if rel.source_id == artifact_id:
                if rel.type == RelationType.IMPLEMENTS:
                    lineage["implements"].append(rel.target_id)
                elif rel.type == RelationType.GENERATED_FROM:
                    lineage["generated_from"].append(rel.target_id)
                elif rel.type == RelationType.CONTRACTS:
                    lineage["contracts"].append(rel.target_id)
            elif rel.target_id == artifact_id and rel.type == RelationType.VERIFIED_BY:
                lineage["verified_by"].append(rel.source_id)
        
        # Trace upstream to original requirements
        lineage["upstream_trace"] = self._trace_upstream_requirements(artifact.meta.trace_ids)
        
        return lineage
    
    def _trace_upstream_requirements(self, trace_ids: List[str]) -> List[Dict[str, str]]:
        """Trace requirement IDs back to their originating documents."""
        upstream = []
        
        for trace_id in trace_ids:
            if trace_id.startswith("REQ-"):
                upstream.append({"type": "requirement", "id": trace_id, "document": "PRD"})
            elif trace_id.startswith("NFR-"):
                upstream.append({"type": "nfr", "id": trace_id, "document": "ARCHITECTURE"})
            elif trace_id.startswith("FRS-FEAT-"):
                upstream.append({"type": "feature_spec", "id": trace_id, "document": "PRD"})
        
        return upstream


class RepositoryStructure(BaseModel):
    """Repository structure for code artifact organization."""
    root_path: str
    src_directories: List[str] = Field(default_factory=list)
    test_directories: List[str] = Field(default_factory=list)
    spec_directories: List[str] = Field(default_factory=list)
    artifact_patterns: Dict[str, str] = Field(default_factory=dict)
    naming_conventions: Dict[str, str] = Field(default_factory=dict)


class DriftDetection(BaseModel):
    """Drift detection between artifacts and requirements."""
    artifact_id: str
    drift_type: DriftType
    severity: str
    description: str
    detected_at: str
    affected_requirements: List[str] = Field(default_factory=list)


class TraceabilityLink(BaseModel):
    """Link between artifacts and requirements for traceability."""
    source_id: str
    target_id: str
    link_type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    created_at: str
    validated_at: Optional[str] = None


class TraceabilityMatrix(BaseModel):
    """Complete traceability matrix for requirements coverage."""
    requirements_to_code: Dict[str, List[str]] = Field(default_factory=dict)
    code_to_requirements: Dict[str, List[str]] = Field(default_factory=dict)
    test_coverage: Dict[str, List[str]] = Field(default_factory=dict)
    orphaned_code: List[str] = Field(default_factory=list)
    orphaned_requirements: List[str] = Field(default_factory=list)
    coverage_percentage: float = Field(default=0.0, ge=0.0, le=1.0)