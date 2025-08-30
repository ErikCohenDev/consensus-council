"""Web UI server for LLM Council platform.

Provides a FastAPI-based web interface for visualizing:
- Document pipeline progress
- Council member debates in real-time
- Research agent activities
- Consensus building and alignment validation
- Cost tracking and performance monitoring
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .constants import DOCUMENT_STAGE_MAPPING
from .council_members import Council, CouncilMember
from .observability import get_tracer, setup_tracing


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


class ConnectionManager:
    """Manages WebSocket connections for real-time updates with optional scoping."""

    def __init__(self):
        # Each item: { "ws": WebSocket, "filters": {"projectId": str|None, "runId": str|None} }
        self.active_connections: List[Dict[str, Any]] = []

    async def connect(
        self, websocket: WebSocket, filters: Optional[Dict[str, Optional[str]]] = None
    ):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(
            {"ws": websocket, "filters": filters or {"projectId": None, "runId": None}}
        )

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        self.active_connections = [
            c for c in self.active_connections if c.get("ws") is not websocket
        ]

    async def send_update(self, message: Dict[str, Any]):
        """Send update to all connected clients, honoring optional project/run filters."""
        msg_proj = message.get("project_id") or message.get("projectId")
        msg_run = (
            message.get("run_id") or message.get("runId") or message.get("audit_id")
        )
        disconnected: List[Dict[str, Any]] = []
        for entry in self.active_connections:
            ws = entry["ws"]
            flt = entry.get("filters") or {}
            f_proj = flt.get("projectId")
            f_run = flt.get("runId")
            # deliver if no filters, or filters match message
            deliver = True
            if f_proj and msg_proj and f_proj != msg_proj:
                deliver = False
            if f_run and msg_run and f_run != msg_run:
                deliver = False
            if not deliver:
                continue
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                disconnected.append(entry)

        # Clean up disconnected clients
        for entry in disconnected:
            try:
                self.active_connections.remove(entry)
            except ValueError:
                pass


# Global instances
app = FastAPI(title="LLM Council UI", description="Visual interface for LLM Council platform")
setup_tracing("llm-council-backend")
tracer = get_tracer("llm_council.ui_server")
connection_manager = ConnectionManager()
current_pipeline_status = PipelineProgress(
    documents=[],
    council_members=[],
    current_debate_round=None,
    research_progress=[],
    total_cost_usd=0.0,
    execution_time=0.0,
    overall_status="idle",
)

# Prefer serving built Vite frontend if available
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

# Audit tracking (simple in-memory for MVP)
current_audit_id: Optional[str] = None
audit_history: List[Dict[str, Any]] = []  # each: {"audit_id", "success", "execution_time", "total_cost"}
current_project_id: Optional[str] = None
projects_registry: Dict[str, str] = {}  # projectId -> docsPath


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


def _pipeline_to_camel(p: PipelineProgress) -> Dict[str, Any]:
    """Convert pipeline progress to camelCase for UI."""

    def dt_to_ts(dt: Optional[datetime]):
        return int(dt.timestamp()) if isinstance(dt, datetime) else None

    return {
        "documents": [
            {
                "name": d.name,
                "stage": d.stage,
                "exists": d.exists,
                "wordCount": d.word_count,
                "lastModified": dt_to_ts(d.last_modified),
                "auditStatus": d.audit_status,
                "consensusScore": d.consensus_score,
                "alignmentIssues": d.alignment_issues,
            }
            for d in p.documents
        ],
        "councilMembers": [
            {
                "role": m.role,
                "provider": m.model_provider,
                "model": m.model_name,
                "currentStatus": m.current_activity,
                "insightsContributed": m.insights_contributed,
                "agreementsMade": m.agreements_made,
                "questionsAsked": m.questions_asked,
                "expertiseAreas": [],
                "personality": "balanced",
                "debateStyle": "collaborative",
                "memberId": f"{m.role}-{m.model_name}",
            }
            for m in p.council_members
        ],
        "currentDebateRound": (
            {
                "roundNumber": p.current_debate_round.round_number,
                "participants": p.current_debate_round.participants,
                "initialReviews": {},
                "peerResponses": {},
                "emergingConsensus": p.current_debate_round.consensus_points,
                "disagreements": p.current_debate_round.disagreements,
                "questionsRaised": p.current_debate_round.questions_raised,
                "durationSeconds": p.current_debate_round.duration_seconds,
                "status": p.current_debate_round.status,
            }
            if p.current_debate_round
            else None
        ),
        "researchProgress": [
            {
                "stage": r.stage,
                "queriesExecuted": r.queries_executed,
                "sourcesFound": r.sources_found,
                "contextAdded": r.context_added,
                "durationSeconds": r.duration_seconds,
                "status": r.status,
            }
            for r in p.research_progress
        ],
        "totalCostUsd": p.total_cost_usd,
        "executionTime": p.execution_time,
        "overallStatus": p.overall_status,
    }


def _metrics_summary() -> Dict[str, Any]:
    """Get a summary of audit metrics."""
    if not audit_history:
        return {"totalAudits": 0, "totalCost": 0.0, "avgDuration": 0.0, "successRate": 0.0}
    total_cost = sum(item.get("total_cost", 0.0) for item in audit_history)
    durations = [
        item.get("execution_time", 0.0)
        for item in audit_history
        if item.get("execution_time")
    ]
    successes = sum(1 for item in audit_history if item.get("success"))
    return {
        "totalAudits": len(audit_history),
        "totalCost": total_cost,
        "avgDuration": (mean(durations) if durations else 0.0),
        "successRate": (successes / len(audit_history)) if audit_history else 0.0,
    }


@app.get("/")
async def index():
    """Serve Vite build if present; otherwise show setup instructions."""
    if FRONTEND_DIST.exists():
        index_html = FRONTEND_DIST / "index.html"
        if index_html.exists():
            return FileResponse(index_html)
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>LLM Council UI</title>
            <style>
                body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; padding: 2rem; }
                code { background: #f3f4f6; padding: 0.2rem 0.4rem; border-radius: 4px; }
            </style>
        </head>
        <body>
            <h1>Frontend not built</h1>
            <p>
                Run <code>npm run dev</code> in <code>frontend/</code> for development, or
                <code>npm run build</code> to produce a production build. The server will automatically
                serve <code>frontend/dist</code> when it exists.
            </p>
        </body>
        </html>
        """
    )


@app.get("/api/healthz")
async def healthz():
    """Health check endpoint."""
    return {"ok": True, "timestamp": time.time()}


@app.get("/api/audits/{audit_id}")
async def get_audit(audit_id: str):
    """Get the status of a specific audit."""
    if current_audit_id != audit_id:
        # For MVP: if ID doesn't match, return latest snapshot with a note
        return ApiResponse(
            success=True,
            data={
                "pipeline": _pipeline_to_camel(current_pipeline_status),
                "metrics": _metrics_summary(),
                "note": "Requested audit not active; returning current snapshot.",
            },
        )
    return ApiResponse(
        success=True,
        data={
            "pipeline": _pipeline_to_camel(current_pipeline_status),
            "metrics": _metrics_summary(),
        },
    )


@app.post("/api/audits")
async def create_audit(req: StartAuditRequest):
    """Create a new audit run."""
    global current_audit_id  # pylint: disable=global-statement
    global current_project_id  # pylint: disable=global-statement
    try:
        current_audit_id = uuid.uuid4().hex
        # Assign default project id derived from docsPath if provided
        if req.docsPath:
            current_project_id = _derive_project_id(req.docsPath)
            projects_registry[current_project_id] = req.docsPath
        # Update status
        current_pipeline_status.overall_status = "initializing"
        await connection_manager.send_update(
            {
                "type": "status_update",
                "audit_id": current_audit_id,
                "project_id": current_project_id,
                "status": current_pipeline_status.model_dump(),
            }
        )
        # Import AuditCommand only when needed to avoid circular imports
        from .cli import AuditCommand
        
        # Initialize audit command
        audit_cmd = AuditCommand(
            docs_path=Path(req.docsPath or "./docs"),
            stage=req.stage,
            model=req.model or "gpt-4o",
        )
        # Start audit in background
        asyncio.create_task(
            run_audit_with_ui_updates(audit_cmd, current_audit_id, current_project_id)
        )
        return ApiResponse(
            success=True,
            data={
                "auditId": current_audit_id,
                "projectId": current_project_id,
                "startedAt": time.time(),
            },
        )
    except Exception as e:
        current_pipeline_status.overall_status = "failed"
        await connection_manager.send_update(
            {
                "type": "error",
                "message": str(e),
                "audit_id": current_audit_id,
                "project_id": current_project_id,
            }
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


# Back-compat for older clients
@app.post("/api/start_audit")
async def start_audit_legacy(docs_path: str, stage: Optional[str] = None, model: str = "gpt-4o"):
    """Legacy endpoint to start an audit."""
    return await create_audit(StartAuditRequest(docsPath=docs_path, stage=stage, model=model))


def _derive_project_id(docs_path: str) -> str:
    """Create a simple project id from a docs path (folder name, slugified)."""
    name = Path(docs_path).name or "project"
    slug = "".join(ch if ch.isalnum() else "-" for ch in name).strip("-").lower() or "project"
    return slug


@app.post("/api/projects")
async def register_project(req: RegisterProjectRequest):
    """Register a project with a docsPath; returns projectId."""
    pid = req.projectId or _derive_project_id(req.docsPath)
    projects_registry[pid] = req.docsPath
    return ApiResponse(success=True, data={"projectId": pid})


@app.post("/api/projects/{project_id}/runs")
async def start_project_run(project_id: str, req: StartAuditRequest):
    """Start a run for a registered project."""
    docs = projects_registry.get(project_id) or req.docsPath
    if not docs:
        raise HTTPException(
            status_code=400, detail="Unknown project; provide docsPath or register project first"
        )
    # Use legacy creator under the hood but set current project id
    global current_project_id  # pylint: disable=global-statement
    current_project_id = project_id
    return await create_audit(
        StartAuditRequest(docsPath=str(docs), stage=req.stage, model=req.model)
    )


@app.get("/api/projects/{project_id}/runs/{run_id}")
async def get_project_run(project_id: str, run_id: str):
    """Get the status of a specific project run."""
    # MVP: return current snapshot if ids don't match, with note
    data = {
        "pipeline": _pipeline_to_camel(current_pipeline_status),
        "metrics": _metrics_summary(),
    }
    if current_project_id != project_id or current_audit_id != run_id:
        data["note"] = "Requested run not active; returning current snapshot."
    return ApiResponse(success=True, data=data)


@app.get("/api/projects/{project_id}/runs/latest")
async def get_latest_run(_project_id: str):
    """Get the latest run for a project."""
    return ApiResponse(
        success=True,
        data={
            "pipeline": _pipeline_to_camel(current_pipeline_status),
            "metrics": _metrics_summary(),
        },
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    # Optional scoping by projectId/runId
    qp = websocket.query_params
    filters = {"projectId": qp.get("projectId"), "runId": qp.get("runId")}
    await connection_manager.connect(websocket, filters)
    try:
        # Send initial status
        await websocket.send_text(
            json.dumps(
                {
                    "type": "status_update",
                    "audit_id": current_audit_id,
                    "project_id": current_project_id,
                    "status": current_pipeline_status.model_dump(),
                }
            )
        )

        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


async def run_audit_with_ui_updates(
    audit_cmd: AuditCommand, audit_id: str, project_id: Optional[str]
):
    """Run audit with real-time UI updates."""
    start_time = time.perf_counter()
    # Optional time-budget guardrail (seconds)
    max_seconds = float(os.getenv("AUDIT_MAX_SECONDS", "0") or 0)

    try:
        with tracer.start_as_current_span(
            "audit.run",
            attributes={
                "audit.id": audit_id,
                "project.id": project_id or "",
                "audit.stage": audit_cmd.stage or "",
                "audit.model": audit_cmd.model,
                "docs.path": str(audit_cmd.docs_path),
            },
        ):
            # Load documents
            documents = audit_cmd.load_documents()

        # Update document status
        current_pipeline_status.documents = []
        for filename, stage in DOCUMENT_STAGE_MAPPING.items():
            doc_path = audit_cmd.docs_path / filename
            exists = doc_path.exists()
            word_count = len(documents.get(stage, "").split()) if exists else 0

            doc_status = DocumentStatus(
                name=filename,
                stage=stage,
                exists=exists,
                word_count=word_count,
                last_modified=datetime.fromtimestamp(doc_path.stat().st_mtime)
                if exists
                else None,
                audit_status="pending" if exists else "skipped",
                consensus_score=None,
                alignment_issues=0,
            )
            current_pipeline_status.documents.append(doc_status)

        current_pipeline_status.overall_status = "running"
        await connection_manager.send_update(
            {
                "type": "status_update",
                "audit_id": audit_id,
                "project_id": project_id,
                "status": current_pipeline_status.model_dump(),
            }
        )

        # Initialize council members
        council = Council()
        council.add_member(
            CouncilMember("pm", "openai", "gpt-4o", ["business_logic", "user_needs"])
        )
        council.add_member(
            CouncilMember(
                "security",
                "anthropic",
                "claude-3-5-sonnet-20241022",
                ["threat_modeling", "compliance"],
            )
        )
        council.add_member(
            CouncilMember(
                "data_eval", "google", "gemini-1.5-pro", ["analytics", "evaluation"]
            )
        )
        council.add_member(
            CouncilMember(
                "infrastructure",
                "openrouter",
                "x-ai/grok-2-1212",
                ["scalability", "architecture"],
            )
        )

        # Update council member status
        current_pipeline_status.council_members = [
            CouncilMemberStatus(
                role=member.role,
                model_provider=member.model_provider,
                model_name=member.model_name,
                current_activity="idle",
                insights_contributed=0,
                agreements_made=0,
                questions_asked=0,
            )
            for member in council.members
        ]

        await connection_manager.send_update(
            {
                "type": "council_initialized",
                "audit_id": audit_id,
                "project_id": project_id,
                "members": [
                    member.model_dump() for member in current_pipeline_status.council_members
                ],
            }
        )

        # Run audit for each document
        for doc_status in current_pipeline_status.documents:
            if not doc_status.exists:
                continue
            # Enforce optional time budget between documents
            if max_seconds and (time.perf_counter() - start_time) > max_seconds:
                raise TimeoutError(f"Audit time budget exceeded ({max_seconds}s)")

            doc_status.audit_status = "in_progress"
            await connection_manager.send_update(
                {
                    "type": "document_audit_started",
                    "audit_id": audit_id,
                    "project_id": project_id,
                    "document": doc_status.model_dump(),
                }
            )

            # Simulate council debate (simplified for UI demo)
            document_content = documents[doc_status.stage]
            with tracer.start_as_current_span(
                "audit.debate",
                attributes={
                    "audit.id": audit_id,
                    "project.id": project_id or "",
                    "document.stage": doc_status.stage,
                    "document.name": doc_status.name,
                },
            ):
                debate_result = await council.conduct_debate(
                    document_content, doc_status.stage, max_rounds=2
                )

            # Update with results
            doc_status.audit_status = "completed"
            doc_status.consensus_score = debate_result.consensus_score

            await connection_manager.send_update(
                {
                    "type": "document_audit_completed",
                    "audit_id": audit_id,
                    "project_id": project_id,
                    "document": doc_status.model_dump(),
                    "debate_result": {
                        "consensus_score": debate_result.consensus_score,
                        "rounds": debate_result.total_rounds,
                        "insights": len(debate_result.final_consensus),
                    },
                }
            )

        # Final status update
        current_pipeline_status.overall_status = "completed"
        current_pipeline_status.execution_time = time.perf_counter() - start_time

        await connection_manager.send_update(
            {
                "type": "audit_completed",
                "audit_id": audit_id,
                "project_id": project_id,
                "status": current_pipeline_status.model_dump(),
            }
        )
        # Record in history
        audit_history.append(
            {
                "audit_id": audit_id,
                "success": True,
                "execution_time": current_pipeline_status.execution_time,
                "total_cost": current_pipeline_status.total_cost_usd,
            }
        )

    except Exception as e:
        current_pipeline_status.overall_status = "failed"
        await connection_manager.send_update(
            {
                "type": "error",
                "audit_id": audit_id,
                "project_id": project_id,
                "message": str(e),
            }
        )
        audit_history.append(
            {
                "audit_id": audit_id,
                "success": False,
                "execution_time": time.perf_counter() - start_time,
                "total_cost": current_pipeline_status.total_cost_usd,
            }
        )


@app.get("/api/config/templates")
async def list_templates_config():
    """List available template files in config/templates."""
    templates_dir = Path(__file__).resolve().parent.parent.parent / "config" / "templates"
    items = []
    if templates_dir.exists():
        for f in templates_dir.glob("*.yaml"):
            if f.name == "registry.yaml":
                continue
            items.append({"name": f.stem, "file": str(f), "basename": f.name})
    return ApiResponse(success=True, data={"templates": items})


@app.get("/api/config/quality-gates")
async def get_quality_gates_config():
    """Get the quality gates configuration."""
    qg_path = Path(__file__).resolve().parent.parent.parent / "config" / "quality_gates.yaml"
    raw = {}
    if qg_path.exists():
        try:
            with qg_path.open("r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            raw = {}
    return ApiResponse(success=True, data={"qualityGates": raw})


# Aliases without /config prefix
@app.get("/api/templates")
async def list_templates():
    """List available template files."""
    return await list_templates_config()


@app.get("/api/quality-gates")
async def get_quality_gates():
    """Get the quality gates configuration."""
    return await get_quality_gates_config()


# If Vite build exists, serve its assets at /assets
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir), html=False), name="assets")


def run_ui_server(config: UIConfig = UIConfig()):
    """Run the UI server."""
    uvicorn.run(
        "llm_council.ui_server:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info" if config.debug else "warning",
    )


if __name__ == "__main__":
    run_ui_server()
