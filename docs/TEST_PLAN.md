# TEST_PLAN.md — LLM Council Audit & Consensus Platform

Owner: QA/Eng • Status: Draft

## Objectives

- Ensure PRD requirements (R-PRD-###) are verifiably tested.
- Maintain high confidence via automated unit, integration, and workflow tests.
- Gate merges with coverage thresholds and critical-path assertions.

## Test Types

- Unit (Python): consensus math, orchestrator retries/caching, council debate state, alignment scoring, schema validation.
- Integration (Python): CLI happy-paths, stage orchestration, artifact generation, error handling.
- Contract/Schema: Validate structured outputs and WebSocket payloads with Zod/Pydantic schemas.
- Frontend Unit: Zustand store selectors/actions, WebSocket service (reconnect, queue, heartbeat), hooks, simple components.
- Frontend Integration: Simulated WS event flow updates UI state (status_update, document_audit_started/completed, audit_completed, error).

## Coverage Targets

- Backend overall ≥ 85% lines; consensus/alignment/orchestrator ≥ 90%.
- Frontend overall ≥ 80% lines; WebSocket service/hook ≥ 90%.

## CI Commands

- Backend: `pytest --maxfail=1 --disable-warnings -q --cov=src/llm_council --cov-report=term-missing`.
- Frontend: `cd frontend && npm run test:coverage` (Vitest + jsdom).

## Critical Test Cases (Mapping)

- R-PRD-001 CLI ingest + outputs → `tests/test_cli.py::TestCLICommands`.
- R-PRD-004 Consensus thresholds deterministic → `tests/test_alignment.py` and consensus tests.
- R-PRD-006 Alignment backlog generated on mismatch → `tests/test_alignment.py`.
- R-PRD-009 Schema validation + retry → `tests/test_schemas.py`.
- R-PRD-011 Human review triggers (stubbed) → CLI flag/flow unit test (TODO).
- R-PRD-015 Council multi‑round debate → `tests/test_council_members.py`.

Frontend (planned):

- FE-WS-001 Normalize backend WS events → unit test for `normalizeToNotification` (status_update, audit_started/completed, error).
- FE-WS-002 Reconnect with backoff + heartbeat → unit test with mocked WebSocket.
- FE-WS-003 Hook updates store on events → integration test for `useWebSocketConnection`.
- FE-UI-001 Pages render from store without WS → snapshot/smoke tests (Dashboard/Council/Audit).

## Traceability

See `docs/TRACEABILITY_MATRIX.md` for PRD ↔ Architecture ↔ Tests ↔ Tasks mapping.
