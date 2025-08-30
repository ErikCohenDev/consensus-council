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
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import uuid
from statistics import mean

from .orchestrator import AuditorOrchestrator
from .council_members import Council, CouncilMember, DebateResult
from .alignment import AlignmentValidator
from .research_agent import ResearchAgent
from .pipeline import PipelineOrchestrator
from .cli import AuditCommand, DOCUMENT_STAGE_MAPPING


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
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connsect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_update(self, message: Dict[str, Any]):
        """Send update to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)


# Global instances
app = FastAPI(title="LLM Council UI", description="Visual interface for LLM Council platform")
connection_manager = ConnectionManager()
current_pipeline_status = PipelineProgress(
    documents=[],
    council_members=[],
    current_debate_round=None,
    research_progress=[],
    total_cost_usd=0.0,
    execution_time=0.0,
    overall_status="idle"
)

# Prefer serving built Vite frontend if available
FRONTEND_DIST = (Path(__file__).resolve().parent.parent.parent / "frontend" / "dist")

# Audit tracking (simple in-memory for MVP)
current_audit_id: Optional[str] = None
audit_history: List[Dict[str, Any]] = []  # each: {"audit_id", "success", "execution_time", "total_cost"}

class ApiResponse(BaseModel):
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: time.time())

class StartAuditRequest(BaseModel):
    docsPath: str
    stage: Optional[str] = None
    model: Optional[str] = "gpt-4o"

def _pipeline_to_camel(p: PipelineProgress) -> Dict[str, Any]:
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
    if not audit_history:
        return {"totalAudits": 0, "totalCost": 0.0, "avgDuration": 0.0, "successRate": 0.0}
    total_cost = sum(item.get("total_cost", 0.0) for item in audit_history)
    durations = [item.get("execution_time", 0.0) for item in audit_history if item.get("execution_time")]
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
    return {"ok": True, "timestamp": time.time()}


@app.get("/api/audits/{audit_id}")
async def get_audit(audit_id: str):
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
    return ApiResponse(success=True, data={"pipeline": _pipeline_to_camel(current_pipeline_status), "metrics": _metrics_summary()})


@app.post("/api/audits")
async def create_audit(req: StartAuditRequest):
    """Create a new audit run."""
    global current_audit_id
    try:
        current_audit_id = uuid.uuid4().hex
        # Update status
        current_pipeline_status.overall_status = "initializing"
        await connection_manager.send_update({
            "type": "status_update",
            "audit_id": current_audit_id,
            "status": asdict(current_pipeline_status),
        })
        # Initialize audit command
        audit_cmd = AuditCommand(
            docs_path=Path(req.docsPath),
            stage=req.stage,
            model=req.model or "gpt-4o",
        )
        # Start audit in background
        asyncio.create_task(run_audit_with_ui_updates(audit_cmd, current_audit_id))
        return ApiResponse(success=True, data={"auditId": current_audit_id, "startedAt": time.time()})
    except Exception as e:
        current_pipeline_status.overall_status = "failed"
        await connection_manager.send_update({"type": "error", "message": str(e), "audit_id": current_audit_id})
        raise HTTPException(status_code=500, detail=str(e))


# Back-compat for older clients
@app.post("/api/start_audit")
async def start_audit_legacy(docs_path: str, stage: Optional[str] = None, model: str = "gpt-4o"):
    return await create_audit(StartAuditRequest(docsPath=docs_path, stage=stage, model=model))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await connection_manager.connect(websocket)
    try:
        # Send initial status
        await websocket.send_text(json.dumps({
            "type": "status_update",
            "audit_id": current_audit_id,
            "status": asdict(current_pipeline_status)
        }))

        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


async def run_audit_with_ui_updates(audit_cmd: AuditCommand, audit_id: str):
    """Run audit with real-time UI updates."""
    start_time = time.perf_counter()

    try:
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
                last_modified=datetime.fromtimestamp(doc_path.stat().st_mtime) if exists else None,
                audit_status="pending" if exists else "skipped",
                consensus_score=None,
                alignment_issues=0
            )
            current_pipeline_status.documents.append(doc_status)

        current_pipeline_status.overall_status = "running"
        await connection_manager.send_update({
            "type": "status_update",
            "audit_id": audit_id,
            "status": asdict(current_pipeline_status)
        })

        # Initialize council members
        council = Council()
        council.add_member(CouncilMember("pm", "openai", "gpt-4o", ["business_logic", "user_needs"]))
        council.add_member(CouncilMember("security", "anthropic", "claude-3-5-sonnet-20241022", ["threat_modeling", "compliance"]))
        council.add_member(CouncilMember("data_eval", "google", "gemini-1.5-pro", ["analytics", "evaluation"]))
        council.add_member(CouncilMember("infrastructure", "openrouter", "x-ai/grok-2-1212", ["scalability", "architecture"]))

        # Update council member status
        current_pipeline_status.council_members = [
            CouncilMemberStatus(
                role=member.role,
                model_provider=member.model_provider,
                model_name=member.model_name,
                current_activity="idle",
                insights_contributed=0,
                agreements_made=0,
                questions_asked=0
            ) for member in council.members
        ]

        await connection_manager.send_update({
            "type": "council_initialized",
            "audit_id": audit_id,
            "members": [asdict(member) for member in current_pipeline_status.council_members]
        })

        # Run audit for each document
        for doc_status in current_pipeline_status.documents:
            if not doc_status.exists:
                continue

            doc_status.audit_status = "in_progress"
            await connection_manager.send_update({
                "type": "document_audit_started",
                "audit_id": audit_id,
                "document": asdict(doc_status)
            })

            # Simulate council debate (simplified for UI demo)
            document_content = documents[doc_status.stage]
            debate_result = await council.conduct_debate(document_content, doc_status.stage, max_rounds=2)

            # Update with results
            doc_status.audit_status = "completed"
            doc_status.consensus_score = debate_result.consensus_score

            await connection_manager.send_update({
                "type": "document_audit_completed",
                "audit_id": audit_id,
                "document": asdict(doc_status),
                "debate_result": {
                    "consensus_score": debate_result.consensus_score,
                    "rounds": debate_result.total_rounds,
                    "insights": len(debate_result.final_consensus)
                }
            })

        # Final status update
        current_pipeline_status.overall_status = "completed"
        current_pipeline_status.execution_time = time.perf_counter() - start_time

        await connection_manager.send_update({
            "type": "audit_completed",
            "audit_id": audit_id,
            "status": asdict(current_pipeline_status)
        })
        # Record in history
        audit_history.append({
            "audit_id": audit_id,
            "success": True,
            "execution_time": current_pipeline_status.execution_time,
            "total_cost": current_pipeline_status.total_cost_usd,
        })

    except Exception as e:
        current_pipeline_status.overall_status = "failed"
        await connection_manager.send_update({
            "type": "error",
            "audit_id": audit_id,
            "message": str(e)
        })
        audit_history.append({
            "audit_id": audit_id,
            "success": False,
            "execution_time": time.perf_counter() - start_time,
            "total_cost": current_pipeline_status.total_cost_usd,
        })

@app.get("/api/config/templates")
async def list_templates():
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
async def get_quality_gates():
    qg = Path(__file__).resolve().parent.parent.parent / "config" / "quality_gates.yaml"
    if qg.exists():
        try:
            import yaml
            with qg.open("r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
        except Exception:
            raw = {}
    else:
        raw = {}
    return ApiResponse(success=True, data={"qualityGates": raw})


# If Vite build exists, serve its assets at /assets
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir), html=False), name="assets")


def run_ui_server(config: UIConfig = UIConfig()):
    """Run the UI server."""
    import uvicorn
    uvicorn.run(
        "llm_council.ui_server:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info" if config.debug else "warning"
    )


if __name__ == "__main__":
    run_ui_server()
