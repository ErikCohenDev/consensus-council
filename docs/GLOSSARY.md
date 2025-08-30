# GLOSSARY & DATA MODEL — LLM Council

Purpose: Shared terminology and data model for the council, audit pipeline, UI events, and APIs. This document is source‑of‑truth for names used in code, docs, and UI.

## Domain Glossary (Concepts)

- Council: Group of specialized auditors (roles) that review a document stage and debate toward a decision.
- Council Member: A role+model assignment with live status and contribution counters.
- Debate Session: Multi‑round conversation among members for one document stage; ends with consensus or failure.
- Debate Round: One round’s participants and outcomes (emerging consensus, disagreements, questions).
- Audit: Per‑stage evaluation producing per‑role Auditor Responses and (if possible) a Consensus Result.
- Consensus: Deterministic aggregation (weighted average + approvals) producing PASS/FAIL with agreement level.
- Alignment: Cross‑stage coherence check; misalignment generates an alignment backlog.
- Human Review: Manual intervention path for strategic stages or low agreement cases.
- Pipeline: The overall, multi‑stage progress state (documents + council + research + totals).

## Documents & Stages

- DocumentStage: research_brief → market_scan → vision → prd → architecture → implementation_plan
  shared/types/core.ts:12
- DocumentInfo: presence, counts, status, consensusScore, alignmentIssues
  shared/types/core.ts:18

## Council & Debate

- CouncilMemberInfo: role, provider, model, expertiseAreas, personality, debateStyle, counters, currentStatus
  shared/types/core.ts:84
- DebateRound: participants, initialReviews, peerResponses, emergingConsensus, disagreements, questionsRaised, durationSeconds, status
  shared/types/core.ts:98
- DebateSession: sessionId, documentStage, participants, rounds, finalConsensus, unresolvedIssues, consensusScore, totalDuration, status
  shared/types/core.ts:110

## Audits & Consensus

- AuditorResponse: overallAssessment (summary, topRisks, quickWins, overallPass), scoresDetailed, blockingIssues, confidenceLevel
  shared/types/core.ts:36
- ConsensusResult: finalDecision (PASS/FAIL), weightedAverage, agreementLevel, individualScores, approvalCount, criticalIssues
  shared/types/core.ts:74

## Pipeline Snapshot

- PipelineProgress: documents, councilMembers, currentDebateRound, researchProgress, totalCostUsd, executionTime, overallStatus
  shared/types/core.ts:143
- ResearchProgress: stage, queriesExecuted, sourcesFound, contextAdded, durationSeconds, status
  shared/types/core.ts:125

## Events & Real‑Time Messages

- NotificationMessage (UI bus):
  type: status_update | audit_started | audit_completed | debate_started | debate_round_completed | consensus_reached | error_occurred | system_alert
  shared/types/core.ts:164
- WebSocketMessage (raw): type, data, timestamp
  shared/types/core.ts:171
- System/Audit/Debate Events (backend internal): SystemEvent, AuditEvent, DebateEvent
  shared/types/core.ts:226, shared/types/core.ts:233, shared/types/core.ts:243

Message flow:
- Backend audits and debates emit updates → WS `/ws` broadcasts NotificationMessages (now include `audit_id`).
- Frontend normalizes messages and updates the Zustand store; UI renders PipelineProgress and Council state.

## HTTP API (Projects & Runs)

- POST `/api/projects` → register a project (accepts `docsPath` or initial docs) [planned]
- POST `/api/projects/{projectId}/runs` → start a pipeline run (preferred)
  Body: StartAuditRequest { stage?, model? } – docsPath is provided when creating the project
  shared/types/core.ts:185
- GET `/api/projects/{projectId}/runs/{runId}` → latest snapshot
  Returns { pipeline: PipelineProgress, metrics }
  shared/types/core.ts:191 (GetStatusResponse shape)
- GET `/api/projects/{projectId}/runs/latest` → most recent snapshot [planned]
- GET `/api/templates` → list available templates (alias of config/templates)
- GET `/api/quality-gates` → quality gates YAML (if present)
- GET `/api/healthz` → basic health check

Compatibility:
- Legacy aliases remain during migration: `POST /api/audits`, `GET /api/audits/{auditId}`. Prefer Projects/Runs routes in new clients.

Notes:
- WS messages include `audit_id` to correlate snapshots and events.
- Pipeline snapshots are serialized to camelCase for UI compatibility.

## Configuration & Gates

- Templates: `config/templates/*.yaml` – stages, human_review_policy, optional auditor questions & weights.
  Loader: src/llm_council/config_loader.py:1
- Quality Gates: `config/quality_gates.yaml` – consensus thresholds, blocking severity, algorithm config.
  Exposed at: GET `/api/config/quality-gates`

## Artifacts & Outputs

- audit.md — Executive summary, top risks, quick wins.
- consensus_<DOC>.md — Deterministic consensus result per doc.
- decision_<STAGE>.md — Gate verdict with thresholds.
- alignment_backlog_<DOC>.md — Proposed edits to resolve misalignment.

## Errors & Metrics (Observability)

- AppError / ValidationError / NetworkError – unified error envelopes
  shared/types/core.ts:254
- PerformanceMetrics / SystemHealth – observability model
  shared/types/core.ts:276, shared/types/core.ts:285

## Relationships (at a glance)

1) Document (by Stage) → Audit → AuditorResponses → ConsensusResult
2) Stages chained by Alignment → Decision artifacts per stage
3) Council & Debate drive consensus (multi‑round)
4) PipelineProgress aggregates (1)–(3) for UI
5) WS events stream state; API snapshots serve UI/automation
6) Templates + Quality Gates define behavior; Human Review can override/escalate

## Diagram (Flow Overview)

```mermaid
flowchart LR
  subgraph UI[Web UI]
    W[React App (Vite)]
  end

  subgraph API[FastAPI Server]
    P1[POST /api/projects\nRegister Project]
    R1[POST /api/projects/{projectId}/runs\nStart Run]
    R2[GET /api/projects/{projectId}/runs/{runId}\nSnapshot]
    C1[GET /api/templates]
    C2[GET /api/quality-gates]
    WS[/WS /ws?projectId&runId\nNotification stream/]
  end

  subgraph CORE[Core Pipeline]
    ORCH[AuditorOrchestrator]
    COUNCIL[Council & Debate]
    CONS[Consensus Engine]
    ALIGN[Alignment Validator]
  end

  subgraph MODELS[LLM Providers]
    OAI[OpenAI]
    CLAUDE[Anthropic]
    GEM[Google]
    OR[OpenRouter]
  end

  W -- register project --> P1
  W -- start run --> R1
  W -- poll snapshot --> R2
  W -- read templates --> C1
  W -- read gates --> C2
  API <-- stream events --> W
  WS -. status_update / audit_* .- W

  R1 --> ORCH
  ORCH --> COUNCIL
  COUNCIL --> MODELS
  MODELS --> COUNCIL
  COUNCIL --> CONS
  CONS --> ALIGN
  ALIGN --> ORCH
  ORCH --> R2
  ORCH --> WS
```

Legend:
- WS events carry `runId` (and may include `audit_id` during migration) and types like `status_update`, `document_audit_started/completed`, `audit_completed`, `error_occurred`.
- Snapshots (`GET /api/projects/{projectId}/runs/{runId}`) return `pipeline` (camelCase) and `metrics`.
