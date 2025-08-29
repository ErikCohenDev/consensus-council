# IMPLEMENTATION_PLAN.md — LLM Council Audit & Consensus Platform

**Owner (Eng Lead/PM):** Erik Cohen
**Date:** 2025-08-29
**Status:** Draft
**Links:** [PRD](./PRD.md) • [Architecture](./ARCHITECTURE.md)

## 0) Milestones & Status

- M1: Core CLI + council members + multi-model LLM integration — In progress
- M2: Council debate system + consensus + alignment validation — In progress
- M3: Research agent + gated document pipeline + tests — Planned
- M4: Web UI (Vite + React + TS) + real-time updates — Initial scaffold complete

## 1) Implementation Summary (current)

**Core Infrastructure**

- CLI with audit, pipeline, research-context, council-debate commands
- Document loading and stage mapping (Research → Market → Vision → PRD → Architecture → Implementation)
- Template engine with YAML configuration and model assignments
- Cache system with hash-based cost optimization

**Council Member System**

- CouncilMember objects with personalities, debate styles, and model assignments
- Multi-round debate orchestration with peer response handling
- Consensus emergence detection and disagreement analysis
- Question generation for alignment resolution

**Multi-Model Ensemble via LiteLLM**

- OpenAI (GPT-4o, GPT-4o-mini) for PM and UX roles
- Anthropic (Claude-3.5-Sonnet, Claude-Haiku) for Security and Cost
- Google (Gemini-1.5-Pro) for Data/Eval analysis
- OpenRouter (Grok) for Infrastructure perspective
- UniversalModelProvider with provider-agnostic interface

**Advanced Features**

- ResearchAgent with Tavily integration for internet context
- Cross-document alignment validation with backlog generation
- Structured artifact outputs (audit.md, consensus*<DOC>.md, decision*<STAGE>.md)
- Cost controls achieving ≤$2/run target

## 2) Architecture Completeness

**File Structure:**

```
src/llm_council/
├── cli.py                 # ✅ CLI commands with council-debate support
├── orchestrator.py        # ✅ Original auditor orchestration (maintained for compatibility)
├── council_members.py     # ✅ NEW: Council debate system
├── multi_model.py        # ✅ NEW: Multi-model ensemble via LiteLLM
├── research_agent.py     # ✅ NEW: Tavily research integration
├── consensus.py          # ✅ Consensus engine with trimmed mean
├── alignment.py          # ✅ Cross-document alignment validation
├── pipeline.py           # ✅ Multi-stage pipeline orchestration
├── templates.py          # ✅ YAML template loading and validation
└── schemas.py            # ✅ Pydantic models for structured outputs

tests/                     # tests evolving
├── test_council_members.py   # ✅ NEW: Council debate functionality
├── test_multi_model.py       # ✅ NEW: Multi-model ensemble tests
├── test_orchestrator.py      # ✅ Core orchestration
├── test_consensus.py         # ✅ Consensus algorithms
├── test_alignment.py         # ✅ Alignment validation
└── test_cli.py              # ✅ CLI integration tests
```

### Frontend/UI Tasks

| ID       | Task                                                     | PRD Link     | Est. | Status |
|----------|----------------------------------------------------------|--------------|------|--------|
| FE-001   | Vite + React + TS scaffold, path aliases                 | N/A          | 0.5d | Done   |
| FE-002   | Shared types/schemas wiring                              | NFR (Types)  | 0.5d | Done   |
| FE-003   | WebSocket service (reconnect, queue, heartbeat, Zod)     | NFR (UI)     | 1d   | Done   |
| FE-004   | Zustand store (connection/pipeline/council/notifications)| NFR (UI)     | 0.5d | Done   |
| FE-005   | Hook: `useWebSocketConnection`                           | NFR (UI)     | 0.5d | Done   |
| FE-006   | Layout + pages (Dashboard, Audit, Council, Pipeline)     | NFR (UI)     | 1d   | Done   |
| FE-007   | Council debate visualization (rounds, consensus)         | R-PRD-015    | 1.5d | Todo   |
| FE-008   | Error handling, toasts, logging                          | NFR (Reliab) | 0.5d | Todo   |
| FE-009   | WS/Hook unit + integration tests                         | Quality      | 1d   | Todo   |
| FE-010   | CI wiring for frontend tests/coverage                    | Quality      | 0.5d | Todo   |

### Backend Tasks (selected)

| ID       | Task                                         | PRD Link   | Est. | Status |
|----------|----------------------------------------------|------------|------|--------|
| T-BE-001 | Document loader + stage mapping               | R-PRD-001  | 0.5d | Done   |
| T-BE-002 | Orchestrator workers + retry/timeout         | R-PRD-002  | 1.5d | WIP    |
| T-BE-003 | Artifact generation (audit/consensus/decision)| R-PRD-003/4/5 | 1.5d | WIP    |
| T-BE-004 | Consensus engine thresholds                   | R-PRD-004  | 1d   | WIP    |
| T-BE-006 | Alignment validator + backlog                 | R-PRD-006  | 1d   | Done   |
| T-BE-009 | Schema validation + retries                   | R-PRD-009  | 1d   | Done   |
| T-BE-010 | Research agent integration                    | R-PRD-010  | 1d   | Planned|
| T-BE-011 | Human review CLI flow                         | R-PRD-011  | 1d   | Planned|
| T-BE-012 | Deadlock detection                            | R-PRD-012  | 0.5d | Planned|

## 3) Quality & Evaluation Gates

- **Offline**: schema validity ≥99%; consensus repeatable; gate verdict stable with identical inputs.
- **Online**: 80% of human spot-checks judge Top Risks useful.
- **DoD**: docs updated; tests passing; examples packaged; `--max-calls` guard working.

## 4) Security & Privacy Tasks

- Env-based secrets; redact logs; document no-PII expectation.
- Optional: artifact retention policy.

## 5) Observability Tasks

- Token/time counters; write per-node summaries; simple logs.

## 6) Performance & Scalability Tasks

- Parallelism config; chunking; cache effectiveness metric.

## 7) Readiness & Runbooks

- README updates; usage examples; troubleshooting (“bad JSON” fixes).
- Release notes; version tag.

## 8) Risks, Dependencies, Open Items

- Model or API changes; add fallback prompts/tests.

## 9) Traceability & Tests

See `docs/TRACEABILITY_MATRIX.md` and `docs/TEST_PLAN.md`.

| Requirement | Architecture Component(s)     | Task(s)      | Status |
| ----------- | ----------------------------- | ------------ | ------ |
| R-PRD-001   | Orchestrator, Loader          | T-001, T-002 | Todo   |
| R-PRD-002   | Auditor Workers               | T-003        | Todo   |
| R-PRD-003   | Synthesis                     | T-005        | Todo   |
| R-PRD-004   | Consensus Engine              | T-007        | Todo   |
| R-PRD-005   | Gate Evaluator                | T-008        | Todo   |
| R-PRD-006   | Alignment Analyzer            | T-009        | Todo   |
| R-PRD-007   | Cache                         | T-006        | Todo   |
| R-PRD-009   | Schema Validator              | T-004        | Todo   |
| R-PRD-010   | Research Pre-Gate             | T-010        | Todo   |
| R-PRD-011   | Human Review Interface        | T-011        | Todo   |
| R-PRD-012   | Consensus Deadlock Resolution | T-012        | Todo   |

### Gate checklist (Implementation → Launch)

- [ ] All `R-PRD-###` mapped to tasks; matrix has **no gaps**.
- [ ] Schema validity ≥99%; consensus/gate stable; alignment backlog exercised.
- [ ] p95 runtime ≤ 5 min on sample corpus; default run ≤ $2 with cache on.
- [ ] 0 **CRITICAL**, 0 **HIGH** outstanding.
