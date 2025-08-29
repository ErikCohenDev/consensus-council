# TRACEABILITY_MATRIX.md — PRD ↔ Architecture ↔ Tests ↔ Tasks

Owner: PM/Eng • Status: Draft

| PRD ID    | Architecture Components                  | Tests (existing/planned)            | Tasks (IDs)             | Status |
| --------- | ---------------------------------------- | ----------------------------------- | ----------------------- | ------ |
| R-PRD-001 | CLI (`cli.py`), document loader          | `tests/test_cli.py`                 | T-BE-001 Loader         | ✅      |
| R-PRD-002 | Orchestrator workers + Template engine   | Orchestrator tests (planned)        | T-BE-002 Orchestrator   | ⏳      |
| R-PRD-003 | Report writer (artifacts)                | Integration test (planned)          | T-BE-003 Artifacts      | ⏳      |
| R-PRD-004 | Consensus engine (`consensus.py`)        | Consensus tests (planned)           | T-BE-004 Consensus      | ⏳      |
| R-PRD-005 | Gate evaluator (decision files)          | Integration test (planned)          | T-BE-005 Gate Evaluator | ⏳      |
| R-PRD-006 | Alignment validator (`alignment.py`)     | `tests/test_alignment.py`           | T-BE-006 Alignment      | ✅      |
| R-PRD-007 | Cache (`cache.py`)                       | Cache tests (planned)               | T-BE-007 Cache          | ⏳      |
| R-PRD-008 | Call caps (orchestrator)                 | Orchestrator tests (planned)        | T-BE-008 Cap Guard      | ⏳      |
| R-PRD-009 | Schema validation (`schemas.py`)         | `tests/test_schemas.py`             | T-BE-009 Schemas        | ✅      |
| R-PRD-010 | Research agent (`research_agent.py`)     | Research tests (planned)            | T-BE-010 Research       | ⏳      |
| R-PRD-011 | Human review interface (CLI/UI flow)     | CLI flow test (planned)             | T-BE-011 Human Review   | ⏳      |
| R-PRD-012 | Deadlock detection (debate/orchestrator) | Debate/orchestrator tests (planned) | T-BE-012 Deadlock       | ⏳      |
| R-PRD-013 | Multi‑model ensemble (`multi_model.py`)  | Ensemble tests (planned)            | T-BE-013 Ensemble       | ⏳      |
| R-PRD-014 | Perspective analysis (ensemble/council)  | Analysis tests (planned)            | T-BE-014 Perspective    | ⏳      |
| R-PRD-015 | Council debate (`council_members.py`)    | `tests/test_council_members.py`     | T-BE-015 Council Debate | ✅      |

Frontend additions (supporting observability, not PRD‑blocking):

| FE ID  | Component                                   | Tests (planned)                          | Status |
| ------ | ------------------------------------------- | ---------------------------------------- | ------ |
| FE-001 | Vite + React + TS setup                     | N/A                                      | ✅      |
| FE-002 | Shared types/schemas wiring                 | Type-check in build                      | ✅      |
| FE-003 | WebSocket service normalization             | Unit tests (normalize, reconnect, queue) | ⏳      |
| FE-004 | Zustand app store                           | Store unit tests                         | ⏳      |
| FE-005 | Pages (Dashboard, Audit, Council, Pipeline) | Smoke/snapshot tests                     | ⏳      |
| FE-006 | Hook: `useWebSocketConnection`              | Integration test with mocked WS          | ⏳      |

Legend: ✅ done • ⏳ planned • ❌ missing
