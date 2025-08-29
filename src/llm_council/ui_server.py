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
from pydantic import BaseModel

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

    async def connect(self, websocket: WebSocket):
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


@app.get("/")
async def index():
    """Serve the main UI page."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LLM Council Platform</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
        <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .debug-border { border: 1px solid #e5e7eb; }
            .status-pending { background-color: #fef3c7; color: #d97706; }
            .status-in-progress { background-color: #dbeafe; color: #2563eb; }
            .status-completed { background-color: #d1fae5; color: #059669; }
            .status-failed { background-color: #fee2e2; color: #dc2626; }
            .council-member {
                transition: all 0.3s ease;
                border-left: 4px solid #e5e7eb;
            }
            .council-member.active { border-left-color: #2563eb; }
            .council-member.speaking { border-left-color: #059669; }
            .council-member.questioning { border-left-color: #d97706; }
        </style>
    </head>
    <body class="bg-gray-50">
        <div id="root"></div>
        <script type="text/babel" src="/static/ui.js"></script>
    </body>
    </html>
    """)


@app.get("/api/status")
async def get_status():
    """Get current pipeline status."""
    return current_pipeline_status


@app.post("/api/start_audit")
async def start_audit(docs_path: str, stage: Optional[str] = None, model: str = "gpt-4o"):
    """Start an audit process."""
    try:
        # Update status
        current_pipeline_status.overall_status = "initializing"
        await connection_manager.send_update({
            "type": "status_update",
            "status": asdict(current_pipeline_status)
        })

        # Initialize audit command
        audit_cmd = AuditCommand(
            docs_path=Path(docs_path),
            stage=stage,
            model=model
        )

        # Start audit in background
        asyncio.create_task(run_audit_with_ui_updates(audit_cmd))

        return {"message": "Audit started", "status": "initializing"}

    except Exception as e:
        current_pipeline_status.overall_status = "failed"
        await connection_manager.send_update({
            "type": "error",
            "message": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await connection_manager.connect(websocket)
    try:
        # Send initial status
        await websocket.send_text(json.dumps({
            "type": "status_update",
            "status": asdict(current_pipeline_status)
        }))

        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


async def run_audit_with_ui_updates(audit_cmd: AuditCommand):
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
            "members": [asdict(member) for member in current_pipeline_status.council_members]
        })

        # Run audit for each document
        for doc_status in current_pipeline_status.documents:
            if not doc_status.exists:
                continue

            doc_status.audit_status = "in_progress"
            await connection_manager.send_update({
                "type": "document_audit_started",
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
            "status": asdict(current_pipeline_status)
        })

    except Exception as e:
        current_pipeline_status.overall_status = "failed"
        await connection_manager.send_update({
            "type": "error",
            "message": str(e)
        })


# Mount static files for the React UI
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path), html=True), name="static")


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
