"""Data models for UI server endpoints and WebSocket communication."""

from __future__ import annotations
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UIConfig(BaseModel):
    """Configuration for UI server."""
    host: str = "127.0.0.1"
    port: int = 8000
    docs_path: str = "./docs"
    auto_refresh: bool = True
    debug: bool = False


class DocumentStatus(BaseModel):
    """Status of a single document in the pipeline."""
    name: str
    stage: str
    exists: bool
    word_count: int
    last_modified: Optional[datetime]
    audit_status: str  # "pending", "in_progress", "completed", "failed"
    consensus_score: Optional[float]
    alignment_issues: int


class CouncilMemberStatus(BaseModel):
    """Status of a council member during debate."""
    role: str
    model_provider: str
    model_name: str
    current_activity: str  # "idle", "reviewing", "responding", "debating"
    insights_contributed: int
    agreements_made: int
    questions_asked: int


class DebateRoundStatus(BaseModel):
    """Status of a single debate round."""
    round_number: int
    participants: List[str]
    consensus_points: List[str]
    disagreements: List[str]
    questions_raised: List[str]
    duration_seconds: float
    status: str  # "in_progress", "completed"


class ResearchProgress(BaseModel):
    """Progress of research agent activities."""
    stage: str
    queries_executed: List[str]
    sources_found: int
    context_added: bool
    duration_seconds: float
    status: str  # "searching", "processing", "completed", "failed"


class PipelineProgress(BaseModel):
    """Overall pipeline progress and status."""
    documents: List[DocumentStatus]
    council_members: List[CouncilMemberStatus]
    current_debate_round: Optional[DebateRoundStatus]
    research_progress: List[ResearchProgress]
    total_cost_usd: float
    execution_time: float
    overall_status: str  # "initializing", "running", "completed", "failed"


class ApiResponse(BaseModel):
    """API response model."""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class StartAuditRequest(BaseModel):
    """Request model for starting an audit."""
    docsPath: Optional[str] = None
    stage: Optional[str] = None
    model: Optional[str] = "gpt-4o"


class RegisterProjectRequest(BaseModel):
    """Request model for registering a project."""
    docsPath: str
    projectId: Optional[str] = None


class GenerateGraphRequest(BaseModel):
    """Request model for generating context graphs."""
    document: str
    context: str
    projectId: Optional[str] = None
    auditId: Optional[str] = None
