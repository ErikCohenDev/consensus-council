"""Minimal API tests for Projects/Runs routes.

Verifies that the new RESTful endpoints exist and return the expected
ApiResponse envelope and basic data shapes without asserting deep semantics.
"""
from fastapi.testclient import TestClient

from llm_council.ui_server import app


def test_healthz():
    client = TestClient(app)
    r = client.get("/api/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True


def test_projects_runs_flow_minimal(tmp_path):
    client = TestClient(app)

    # Register a project with a temporary docs path
    proj = tmp_path / "docs"
    proj.mkdir()
    res = client.post("/api/projects", json={"docsPath": str(proj)})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    project_id = body["data"]["projectId"]
    assert isinstance(project_id, str)

    # Start a run
    res = client.post(f"/api/projects/{project_id}/runs", json={"stage": "vision", "model": "gpt-4o"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    run_id = body["data"]["auditId"]
    assert isinstance(run_id, str)

    # Get snapshot (may be mid-run)
    res = client.get(f"/api/projects/{project_id}/runs/{run_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "pipeline" in body["data"]
    assert "metrics" in body["data"]
