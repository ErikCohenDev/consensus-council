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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI

from .constants import DOCUMENT_STAGE_MAPPING
from .constants.ui_server import (
    DEFAULT_HOST, DEFAULT_PORT, DEFAULT_DOCS_PATH, 
    ALLOWED_ORIGINS, API_MESSAGES, DEFAULT_COUNCIL_MEMBERS, ENV_VARS
)
from .constants.websocket import WS_MESSAGE_TYPES, WS_CLOSE_CODES
from .models.ui_models import (
    UIConfig, DocumentStatus, CouncilMemberStatus, DebateRoundStatus,
    ResearchProgress, PipelineProgress, ApiResponse, StartAuditRequest,
    RegisterProjectRequest, GenerateGraphRequest
)
from .models.idea_models import (
    IdeaInput, ContextGraphData, ResearchExpansionRequest, 
    ReactFlowGraph, ExpandedContextData, EntityData, RelationshipData, ResearchInsightData
)
from .services.websocket_manager import ConnectionManager
from .services.model_catalog import ModelCatalogService
from .services.entity_extractor import EntityExtractor
from .services.research_expander import ResearchExpander
from .council_members import Council, CouncilMember
from .observability import get_tracer, setup_tracing
from .graph_service import GraphService
from .orchestrator import AuditorWorker




# Global instances
app = FastAPI(title="LLM Council UI", description="Visual interface for LLM Council platform")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                "note": API_MESSAGES["REQUESTED_AUDIT_NOT_ACTIVE"],
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
                "type": WS_MESSAGE_TYPES["STATUS_UPDATE"],
                "audit_id": current_audit_id,
                "project_id": current_project_id,
                "status": current_pipeline_status.model_dump(),
            }
        )
        # Import AuditCommand only when needed to avoid circular imports
        try:
            from .cli import AuditCommand
        except ImportError:
            from cli import AuditCommand

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
                "type": WS_MESSAGE_TYPES["ERROR"],
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
            status_code=400, detail=API_MESSAGES["UNKNOWN_PROJECT"]
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
        data["note"] = API_MESSAGES["REQUESTED_RUN_NOT_ACTIVE"]
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


@app.post("/api/ideas/extract-context")
async def extract_idea_context(idea: IdeaInput):
    """Extract entities and relationships from an idea to create context graph."""
    
    api_key = os.getenv(ENV_VARS["OPENAI_API_KEY"])
    if not api_key:
        raise HTTPException(status_code=500, detail=API_MESSAGES["OPENAI_KEY_MISSING"])

    client = AsyncOpenAI(api_key=api_key)
    
    worker = AuditorWorker(
        role="entity_extractor",
        stage="context_extraction", 
        client=client,
        model="gpt-4o",
    )
    
    extractor = EntityExtractor(worker)
    
    try:
        context_graph = await extractor.extract_context_graph(
            idea.text, 
            additional_context=""
        )
        
        # Convert to API response format
        graph_data = ContextGraphData(
            entities=[
                EntityData(
                    id=e.id, label=e.label, type=e.type, description=e.description,
                    importance=e.importance, certainty=e.certainty
                ) for e in context_graph.entities
            ],
            relationships=[
                RelationshipData(
                    id=r.id, source_id=r.source_id, target_id=r.target_id,
                    type=r.type, label=r.label, strength=r.strength, description=r.description
                ) for r in context_graph.relationships
            ],
            central_entity_id=context_graph.central_entity_id,
            confidence_score=context_graph.confidence_score
        )
        
        # Convert to ReactFlow format
        reactflow_data = extractor.to_reactflow_format(context_graph)
        
        return ApiResponse(success=True, data={
            "graph": graph_data.model_dump(),
            "reactflow": reactflow_data,
            "project_name": idea.project_name or "New Project"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context extraction failed: {str(e)}")


@app.post("/api/ideas/expand-research") 
async def expand_with_research(req: ResearchExpansionRequest):
    """Expand context graph with targeted research insights."""
    
    api_key = os.getenv(ENV_VARS["OPENAI_API_KEY"])
    if not api_key:
        raise HTTPException(status_code=500, detail=API_MESSAGES["OPENAI_KEY_MISSING"])

    client = AsyncOpenAI(api_key=api_key)
    
    auditor_worker = AuditorWorker(
        role="research_expander",
        stage="research_expansion",
        client=client, 
        model="gpt-4o",
    )
    
    # Initialize research agent (simplified for MVP)
    from .research_agent import ResearchAgent
    research_agent = ResearchAgent()
    
    expander = ResearchExpander(auditor_worker, research_agent)
    
    try:
        # Convert request data to internal format
        from .services.entity_extractor import ContextGraph, Entity, Relationship
        
        original_graph = ContextGraph(
            entities=[
                Entity(
                    id=e.id, label=e.label, type=e.type, description=e.description,
                    importance=e.importance, certainty=e.certainty
                ) for e in req.graph.entities
            ],
            relationships=[
                Relationship(
                    id=r.id, source_id=r.source_id, target_id=r.target_id, type=r.type,
                    label=r.label, strength=r.strength, description=r.description
                ) for r in req.graph.relationships
            ],
            central_entity_id=req.graph.central_entity_id,
            confidence_score=req.graph.confidence_score
        )
        
        expanded = await expander.expand_context(original_graph, req.focus_areas)
        
        # Convert back to API format
        expanded_data = ExpandedContextData(
            original_graph=req.graph,
            insights=[
                ResearchInsightData(
                    entity_id=i.entity_id, insight_type=i.insight_type, title=i.title,
                    content=i.content, sources=i.sources, relevance_score=i.relevance_score
                ) for i in expanded.insights
            ],
            new_entities=[
                EntityData(
                    id=e.id, label=e.label, type=e.type, description=e.description,
                    importance=e.importance, certainty=e.certainty
                ) for e in expanded.new_entities
            ],
            new_relationships=[
                RelationshipData(
                    id=r.id, source_id=r.source_id, target_id=r.target_id, type=r.type,
                    label=r.label, strength=r.strength, description=r.description
                ) for r in expanded.new_relationships
            ],
            expansion_confidence=expanded.expansion_confidence
        )
        
        return ApiResponse(success=True, data={"expanded_context": expanded_data.model_dump()})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research expansion failed: {str(e)}")


@app.post("/api/context/graph")
async def generate_graph(req: GenerateGraphRequest):
    """Legacy endpoint - starts the process of generating and broadcasting graph data for a document."""

    api_key = os.getenv(ENV_VARS["OPENAI_API_KEY"])
    if not api_key:
        raise HTTPException(status_code=500, detail=API_MESSAGES["OPENAI_KEY_MISSING"])

    client = AsyncOpenAI(api_key=api_key)

    worker = AuditorWorker(
        role="graph_generator",
        stage="context_graph",
        client=client,
        model="gpt-4o",
    )

    graph_service = GraphService(worker)

    async def stream_graph_data():
        async for item in graph_service.generate_graph_from_document(req.document, req.context):
            message = {
                **item,
                "projectId": req.projectId,
                "auditId": req.auditId,
            }
            await connection_manager.send_update(message)

    asyncio.create_task(stream_graph_data())

    return ApiResponse(success=True, data={"message": API_MESSAGES["GRAPH_GENERATION_STARTED"]})


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
                    "type": WS_MESSAGE_TYPES["STATUS_UPDATE"],
                    "audit_id": current_audit_id,
                    "project_id": current_project_id,
                    "status": current_pipeline_status.model_dump(),
                }
            )
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                message = await websocket.receive_text()
                # Handle heartbeat/ping messages
                try:
                    msg_data = json.loads(message)
                    if msg_data.get("type") in [WS_MESSAGE_TYPES["PING"], WS_MESSAGE_TYPES["HEARTBEAT"]]:
                        response_type = (
                            WS_MESSAGE_TYPES["PONG"] if msg_data.get("type") == WS_MESSAGE_TYPES["PING"] 
                            else WS_MESSAGE_TYPES["HEARTBEAT_ACK"]
                        )
                        await websocket.send_text(json.dumps({
                            "type": response_type,
                            "timestamp": time.time()
                        }))
                except (json.JSONDecodeError, KeyError):
                    # Ignore malformed messages
                    pass
            except Exception:
                # Keep connection alive even if message processing fails
                pass
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


async def run_audit_with_ui_updates(
    audit_cmd, audit_id: str, project_id: Optional[str]
):
    """Run audit with real-time UI updates."""
    start_time = time.perf_counter()
    # Optional time-budget guardrail (seconds)
    max_seconds = float(os.getenv(ENV_VARS["AUDIT_MAX_SECONDS"], "0") or 0)

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
                "type": WS_MESSAGE_TYPES["STATUS_UPDATE"],
                "audit_id": audit_id,
                "project_id": project_id,
                "status": current_pipeline_status.model_dump(),
            }
        )

        # Initialize council members
        council = Council()
        for member_config in DEFAULT_COUNCIL_MEMBERS:
            council.add_member(
                CouncilMember(
                    member_config["role"],
                    member_config["provider"], 
                    member_config["model"],
                    member_config["expertise"]
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
                "type": WS_MESSAGE_TYPES["COUNCIL_INITIALIZED"],
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
                raise TimeoutError(f"{API_MESSAGES['AUDIT_TIME_BUDGET_EXCEEDED']} ({max_seconds}s)")

            doc_status.audit_status = "in_progress"
            await connection_manager.send_update(
                {
                    "type": WS_MESSAGE_TYPES["DOCUMENT_AUDIT_STARTED"],
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
                    "type": WS_MESSAGE_TYPES["DOCUMENT_AUDIT_COMPLETED"],
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
                "type": WS_MESSAGE_TYPES["AUDIT_COMPLETED"],
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
                "type": WS_MESSAGE_TYPES["ERROR"],
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

@app.get("/api/models")
async def get_models():
    """Return a curated list of supported LLM models with their pricing."""
    return ModelCatalogService.get_models()


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


def run_ui_server(config: UIConfig = UIConfig(
    host=DEFAULT_HOST,
    port=DEFAULT_PORT, 
    docs_path=DEFAULT_DOCS_PATH
)):
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


# Example of how to update status from another module
async def example_update_from_elsewhere():
    """Example of how to push updates to the UI from other parts of the application."""
    await asyncio.sleep(5)
    current_pipeline_status.overall_status = "running"
    await connection_manager.send_update(
        {
            "type": "status_update",
            "audit_id": current_audit_id,
            "project_id": current_project_id,
            "status": current_pipeline_status.model_dump(),
        }
    )
