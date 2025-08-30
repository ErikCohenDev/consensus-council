"""Data models for idea processing and context graph generation."""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class IdeaInput(BaseModel):
    """User's initial idea input."""
    text: str = Field(..., min_length=10, max_length=2000)
    project_name: Optional[str] = None
    focus_areas: Optional[List[str]] = None  # Areas user wants to emphasize


class EntityData(BaseModel):
    """Entity in the context graph."""
    id: str
    label: str
    type: str  # "core_idea", "feature", "user_group", "problem", "solution", "risk", "dependency"
    description: str
    importance: float = Field(..., ge=0.0, le=1.0)
    certainty: float = Field(..., ge=0.0, le=1.0)


class RelationshipData(BaseModel):
    """Relationship between entities."""
    id: str
    source_id: str
    target_id: str
    type: str  # "enables", "requires", "conflicts", "contains", "targets", "solves"
    label: str
    strength: float = Field(..., ge=0.0, le=1.0)
    description: str


class ContextGraphData(BaseModel):
    """Complete context graph data."""
    entities: List[EntityData]
    relationships: List[RelationshipData]
    central_entity_id: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class ResearchExpansionRequest(BaseModel):
    """Request to expand context with research."""
    graph: ContextGraphData
    focus_areas: Optional[List[str]] = None
    max_insights: int = Field(default=10, ge=1, le=20)


class ResearchInsightData(BaseModel):
    """Research insight for context expansion."""
    entity_id: str
    insight_type: str
    title: str
    content: str
    sources: List[str] = Field(default_factory=list)
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class ExpandedContextData(BaseModel):
    """Context graph with research insights."""
    original_graph: ContextGraphData
    insights: List[ResearchInsightData]
    new_entities: List[EntityData]
    new_relationships: List[RelationshipData]
    expansion_confidence: float = Field(..., ge=0.0, le=1.0)


class ReactFlowGraph(BaseModel):
    """ReactFlow-formatted graph data."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    central_entity: str
    confidence: float