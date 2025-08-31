"""Systems Engineering models for layered artifact generation."""

from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Stage(str, Enum):
    """Development stage classification."""
    MVP = "mvp"
    V1 = "v1" 
    V2 = "v2"
    BACKLOG = "backlog"
    CUT = "cut"


# Alias for backward compatibility
SEStage = Stage


class Status(str, Enum):
    """Entity development status."""
    IDEATED = "ideated"
    VALIDATED = "validated"
    IMPLEMENTED = "implemented"


class ArtifactLayer(str, Enum):
    """Document artifact layers."""
    VISION = "vision"
    PRD = "prd"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    MVP_SCOPED = "mvp_scoped"


class CostData(BaseModel):
    """Cost structure for entities."""
    one_time: float = Field(..., ge=0.0, description="One-time implementation cost")
    monthly: float = Field(..., ge=0.0, description="Ongoing monthly cost")
    effort_points: Optional[float] = Field(None, ge=0.0, description="Development effort estimate")


class ValueMetrics(BaseModel):
    """Value scoring components (Reach × Frequency × Pain × WTP × Fit)."""
    reach: float = Field(..., ge=0.0, le=1.0, description="Market reach potential")
    frequency: float = Field(..., ge=0.0, le=1.0, description="Usage frequency")
    pain: float = Field(..., ge=0.0, le=1.0, description="Problem severity")
    willingness_to_pay: float = Field(..., ge=0.0, le=1.0, description="WTP intensity")
    product_fit: float = Field(..., ge=0.0, le=1.0, description="Solution-problem fit")
    
    @property
    def total_value(self) -> float:
        """Calculate total value score."""
        return self.reach * self.frequency * self.pain * self.willingness_to_pay * self.product_fit


class RiskMetrics(BaseModel):
    """Risk scoring components (Severity × Likelihood × Exposure × Confidence)."""
    severity: float = Field(..., ge=0.0, le=1.0, description="Impact if risk materializes")
    likelihood: float = Field(..., ge=0.0, le=1.0, description="Probability of occurrence")
    exposure: float = Field(..., ge=0.0, le=1.0, description="Exposure to risk")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment")
    
    @property
    def total_risk(self) -> float:
        """Calculate total risk score."""
        return self.severity * self.likelihood * self.exposure * (1 - self.confidence)


class WSJFMetrics(BaseModel):
    """Weighted Shortest Job First prioritization metrics."""
    business_value: float = Field(..., ge=0.0, le=10.0, description="Business value score")
    time_criticality: float = Field(..., ge=0.0, le=10.0, description="Time sensitivity")
    risk_reduction: float = Field(..., ge=0.0, le=10.0, description="Risk mitigation value")
    effort: float = Field(..., gt=0.0, description="Implementation effort estimate")
    
    @property
    def wsjf_score(self) -> float:
        """Calculate WSJF prioritization score."""
        return (self.business_value + self.time_criticality + self.risk_reduction) / self.effort


class SEEntityMeta(BaseModel):
    """Systems Engineering metadata for entities."""
    value_metrics: Optional[ValueMetrics] = None
    risk_metrics: Optional[RiskMetrics] = None
    cost_data: Optional[CostData] = None
    wsjf_metrics: Optional[WSJFMetrics] = None
    stage: Stage = Stage.MVP
    status: Status = Status.IDEATED
    layer: ArtifactLayer = ArtifactLayer.VISION
    
    def payoff_score(self, alpha: float = 1.0, beta: float = 1.0) -> float:
        """Calculate entity payoff: Value - α·Risk - β·Cost."""
        value = self.value_metrics.total_value if self.value_metrics else 0.0
        risk = self.risk_metrics.total_risk if self.risk_metrics else 0.0
        cost = (self.cost_data.one_time + self.cost_data.monthly * 12) if self.cost_data else 0.0
        
        return value - (alpha * risk) - (beta * cost)


class SEEntity(BaseModel):
    """Enhanced entity with systems engineering metadata."""
    id: str
    label: str
    type: str
    description: str
    importance: float = Field(..., ge=0.0, le=1.0)
    certainty: float = Field(..., ge=0.0, le=1.0)
    se_meta: SEEntityMeta = Field(default_factory=SEEntityMeta)


class SERelationship(BaseModel):
    """Enhanced relationship with systems engineering context."""
    id: str
    source_id: str
    target_id: str
    type: str
    label: str
    strength: float = Field(..., ge=0.0, le=1.0)
    description: str
    propagation_factor: float = Field(default=1.0, ge=0.0, le=1.0, description="How much value/risk propagates through this edge")


class SEContextGraph(BaseModel):
    """Systems engineering context graph with layered projections."""
    entities: List[SEEntity]
    relationships: List[SERelationship]
    central_entity_id: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    budget_constraint: Optional[float] = None
    risk_threshold: Optional[float] = None
    target_layer: ArtifactLayer = ArtifactLayer.VISION


class MVPCutResult(BaseModel):
    """Result of MVP scoping optimization."""
    selected_entities: List[str] = Field(description="Entity IDs included in MVP")
    deferred_entities: List[str] = Field(description="Entity IDs deferred to later versions")
    total_value: float = Field(description="Total value of MVP scope")
    total_risk: float = Field(description="Total risk of MVP scope")
    total_cost: float = Field(description="Total cost of MVP scope")
    feasibility_score: float = Field(..., ge=0.0, le=1.0, description="Overall feasibility")


class ArtifactProjection(BaseModel):
    """Filtered graph projection for specific artifact layer."""
    layer: ArtifactLayer
    entities: List[SEEntity]
    relationships: List[SERelationship]
    focus_areas: List[str] = Field(description="Key focus areas for this layer")
    decisions: List[str] = Field(description="Key decisions made at this layer")
    traceability: Dict[str, List[str]] = Field(description="Mapping to upstream entities")


class SEPipelineState(BaseModel):
    """Complete state of systems engineering pipeline."""
    base_graph: SEContextGraph
    layer_projections: Dict[ArtifactLayer, ArtifactProjection]
    mvp_cut: Optional[MVPCutResult] = None
    current_layer: ArtifactLayer = ArtifactLayer.VISION
    pipeline_confidence: float = Field(..., ge=0.0, le=1.0)


class ComponentDecomposition(BaseModel):
    """Functional to physical component decomposition."""
    component_id: str
    name: str
    function: str
    interfaces: List[str] = Field(description="Interface definitions")
    nfr_constraints: Dict[str, Any] = Field(description="Non-functional requirements")
    dependencies: List[str] = Field(description="Component dependencies")
    estimated_effort: float = Field(..., ge=0.0)
    assigned_entities: List[str] = Field(description="Graph entities this component implements")


class ImplementationTask(BaseModel):
    """Granular implementation task with WSJF scoring."""
    task_id: str
    title: str
    description: str
    component_id: str
    wsjf_metrics: WSJFMetrics
    dependencies: List[str] = Field(description="Task dependencies")
    estimated_hours: float = Field(..., ge=0.0)
    assigned_to: Optional[str] = None
    sprint_target: Optional[str] = None


class ResourceAllocation(BaseModel):
    """Resource allocation plan."""
    components: List[ComponentDecomposition]
    tasks: List[ImplementationTask]
    sprints: Dict[str, List[str]] = Field(description="Sprint to task mapping")
    team_allocation: Dict[str, List[str]] = Field(description="Team member to task mapping")
    critical_path: List[str] = Field(description="Critical path task sequence")


class Feature(BaseModel):
    """Feature definition for MVP optimization."""
    id: str
    name: str
    description: str
    value: float = Field(..., ge=0.0, le=1.0, description="Business value score")
    cost: float = Field(..., ge=0.0, description="Implementation cost estimate") 
    effort: float = Field(..., ge=0.0, description="Development effort in story points")
    dependencies: List[str] = Field(default_factory=list, description="Feature dependencies")
    stage: Stage = Field(default=Stage.BACKLOG)
    
    @property
    def value_density(self) -> float:
        """Calculate value per unit cost."""
        if self.cost == 0:
            return float('inf')
        return self.value / self.cost


class ResourceConstraints(BaseModel):
    """Resource constraints for MVP optimization."""
    max_cost: Optional[float] = Field(None, ge=0.0, description="Maximum budget constraint")
    max_effort: Optional[float] = Field(None, ge=0.0, description="Maximum effort constraint") 
    timeline_weeks: Optional[int] = Field(None, ge=1, description="Timeline constraint in weeks")
    must_have_features: List[str] = Field(default_factory=list, description="Required feature IDs")
    team_size: Optional[int] = Field(None, ge=1, description="Available team size")


class SystemsEntity(BaseModel):
    """Systems engineering entity with SE metadata."""
    id: str
    label: str
    type: str
    stage: Stage
    status: Status
    layer: ArtifactLayer
    se_meta: SEEntityMeta
    importance: float = Field(..., ge=0.0, le=1.0)
    certainty: float = Field(..., ge=0.0, le=1.0)
    paradigm_id: Optional[str] = None
    provenance_chain: Dict[str, Any] = Field(default_factory=dict)


class ArchitecturalComponent(BaseModel):
    """Architectural component definition."""
    component_id: str
    name: str
    type: str
    interfaces: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    implements_requirements: List[str] = Field(default_factory=list)
    nfr_constraints: Dict[str, Any] = Field(default_factory=dict)
    estimated_effort: float = Field(default=0.0, ge=0.0)


class ParadigmFramework(BaseModel):
    """Paradigm framework definition."""
    framework_id: str
    name: str
    description: str
    question_sets: Dict[str, List[str]] = Field(default_factory=dict)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    layer_focus: List[ArtifactLayer] = Field(default_factory=list)


class QuestionType(str, Enum):
    """Type of paradigm question based on human vs LLM capability."""
    HUMAN_ONLY = "human_only"
    HUMAN_REQUIRED = "human_required" 
    HUMAN_PREFERRED = "human_preferred"
    HYBRID = "hybrid"
    LLM_PREFERRED = "llm_preferred"


class ParadigmQuestion(BaseModel):
    """Question designed to surface human context and validate assumptions."""
    id: str
    text: str
    layer: ArtifactLayer
    question_type: QuestionType
    weight: float = Field(..., description="Impact on consensus scoring")
    rationale: str = Field(..., description="Why this question needs human input")
    research_triggers: List[str] = Field(default_factory=list, description="What research to auto-trigger")
    entity_tags: List[str] = Field(default_factory=list, description="Which entities this question relates to")