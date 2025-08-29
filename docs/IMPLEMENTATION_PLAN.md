# IMPLEMENTATION_PLAN.md — LLM Council Audit & Consensus Platform

**Owner (Eng Lead/PM):** Erik Cohen 
**Date:** 2025-08-29  
**Status:** Draft  
**Links:** [PRD](./PRD.md) • [Architecture](./ARCHITECTURE.md)

## 0) Milestones & Timeline
- **M1**: Core CLI + role auditors + schema validation + `audit.md`.  
- **M2**: Consensus + gates + alignment backlog + `consensus_<DOC>.md` + `decision_<STAGE>.md`.  
- **M3**: Research pre-gate (`RESEARCH_BRIEF.md`, `MARKET_SCAN.md`) + examples + smoke tests.

## 1) Workstreams & Tasks (traceable)
> IDs `T-###`; link each to PRD requirements.

| Task ID | Title                                     | Owner | Linked Req(s) | Estimate | Status |
| ------: | ----------------------------------------- | ----- | ------------- | -------: | ------ |
|   T-001 | CLI skeleton + arg parsing                |       | R-PRD-001     |       1d | Todo   |
|   T-002 | Doc loader + line numbering               |       | R-PRD-001     |       1d | Todo   |
|   T-003 | Auditor prompt + fan-out executor         |       | R-PRD-002     |       2d | Todo   |
|   T-004 | JSON schema validation + retry            |       | R-PRD-009     |       1d | Todo   |
|   T-005 | Dedupe/rank + `audit.md` synthesis        |       | R-PRD-003     |       1d | Todo   |
|   T-006 | Cache (hash by model+prompt+content)      |       | R-PRD-007     |       1d | Todo   |
|   T-007 | Consensus engine + report writer          |       | R-PRD-004     |       2d | Todo   |
|   T-008 | Gate evaluator + thresholds + `decision`  |       | R-PRD-005     |       1d | Todo   |
|   T-009 | Alignment analyzer + backlog generator    |       | R-PRD-006     |       2d | Todo   |
|   T-010 | Research pre-gate support + smoke tests   |       | R-PRD-010     |       2d | Todo   |
|   T-011 | Human review interface + interactive CLI  |       | R-PRD-011     |       3d | Todo   |
|   T-012 | Consensus deadlock detection + escalation |       | R-PRD-012     |       1d | Todo   |

## 2) Quality & Evaluation Gates
- **Offline**: schema validity ≥99%; consensus repeatable; gate verdict stable with identical inputs.  
- **Online**: 80% of human spot-checks judge Top Risks useful.  
- **DoD**: docs updated; tests passing; examples packaged; `--max-calls` guard working.

## 3) Security & Privacy Tasks
- Env-based secrets; redact logs; document no-PII expectation.  
- Optional: artifact retention policy.

## 4) Observability Tasks
- Token/time counters; write per-node summaries; simple logs.

## 5) Performance & Scalability Tasks
- Parallelism config; chunking; cache effectiveness metric.

## 6) Readiness & Runbooks
- README updates; usage examples; troubleshooting (“bad JSON” fixes).  
- Release notes; version tag.

## 7) Risks, Dependencies, Open Items
- Model or API changes; add fallback prompts/tests.

## 8) Traceability Matrix
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
