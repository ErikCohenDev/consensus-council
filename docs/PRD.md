# PRD.md — LLM Council Audit & Consensus Platform

**Owner (PM):** Erik Cohen
**Date:** 2025-08-29  
**Status:** Draft  
**Links:** [Vision](./VISION.md)

## 1) Goals & Non-Goals

**Goals**

- G1: Generate an audit + gate verdict from 4 docs in ≤ 5 min p95.
- G2: Enforce consensus rubric + approvals + alignment before promoting.
- G3: Keep MVP operational costs ≤ $2/run (default council, cached).

**Non-Goals**

- Full project management and multi-repo automation (vNext).

Note: A minimal Web UI for real-time visualization is provided for developer ergonomics. The CLI remains the primary interface for MVP requirements.

## 2) Personas & Primary Use Cases

- Founder/PM runs audits during doc iteration; wants Top Risks + Quick Wins.
- Eng lead gates promotion (Vision→PRD→Architecture→Impl Plan) via CLI.

## 3) Functional Requirements (IDs `R-PRD-###`)

| ID        | Requirement (must/should)                                                                   | Rationale                              | Priority | Acceptance Criteria (testable)                                                  | Metric/Target |
| --------- | ------------------------------------------------------------------------------------------- | -------------------------------------- | -------- | ------------------------------------------------------------------------------- | ------------- |
| R-PRD-001 | CLI accepts 4 markdown docs (Vision/PRD/Arch/Impl Plan)                                     | Single-step usage                      | M        | `python audit.py ./docs` produces outputs without manual prompts                | ✅ no errors   |
| R-PRD-002 | Run N role auditors in parallel with diverse models (PM→GPT-4o, Security→Claude, Data→Gemini) | Multi-perspective + model diversity    | M        | Each auditor returns valid JSON with model_provider field                       | ≥99% valid    |
| R-PRD-003 | Produce `audit.md` with Executive Summary, Top Risks, Quick Wins, Per-Doc findings          | Readability                            | M        | Sections present; >= 5 unique findings on typical drafts                        | ≥5 findings   |
| R-PRD-004 | Consensus: weighted rubric + approvals; output `consensus_<DOC>.md`                         | Deterministic promotion                | M        | Weighted ≥ threshold & approvals ≥ 2/3 for PASS                                 | pass logic ok |
| R-PRD-005 | Gate evaluation writes `decision_<STAGE>.md`                                                | Traceability                           | M        | PASS/FAIL + reasons + thresholds shown                                          | file exists   |
| R-PRD-006 | Alignment check: upstream mismatch → fail with backlog file                                 | Coherence                              | M        | If mismatch>0 then `alignment_backlog_<DOC>.md` with concrete proposed edits    | file exists   |
| R-PRD-007 | Caching by (model, prompt, content hash)                                                    | Cost control                           | S        | Re-run unchanged inputs → ≤10% cost of first run                                | ≤10% cost     |
| R-PRD-008 | Max call cap (`--max-calls`)                                                                | Guardrail                              | M        | Exceeding cap stops fan-out gracefully                                          | works         |
| R-PRD-009 | JSON schema validation + retry on violation                                                 | Robustness                             | M        | ≥99% valid artifacts across runs                                                | ≥99% valid    |
| R-PRD-010 | Research pre-gate: `RESEARCH_BRIEF.md` + `MARKET_SCAN.md` → must PASS before Vision         | Avoid building wrong thing             | M        | ≥5 credible sources; ≥3 alternatives; explicit Build/Buy/Partner/Defer decision | pass logic ok |
| R-PRD-011 | Human review interface for strategic docs (Research, Market, Vision, PRD) and low consensus | Human judgment for strategic decisions | M        | Interactive prompts with disagreement summary and context injection             | UI exists     |
| R-PRD-012 | Consensus deadlock resolution: max 3 attempts before human escalation                       | Prevent infinite audit loops           | M        | After 3 consensus attempts, trigger human review with full context              | escalation ok |
| R-PRD-013 | Multi-model ensemble: assign different LLMs to auditor roles for perspective diversity      | Maximize insight variety + reduce bias | S        | PM→OpenAI, Security→Claude, Data→Gemini, etc. with cross-model consensus        | model diversity |
| R-PRD-014 | Model perspective analysis: detect unique insights and bias patterns per provider           | Optimize model selection + learning    | S        | Track which models find which types of issues; diversity scoring ≥0.7           | insight tracking |
| R-PRD-015 | Council debate system: enable multi-round discussion between council members               | Enable sophisticated consensus building | S        | Council members can respond to peers, ask questions, build consensus over rounds | debate functionality |

## 4) Non-Functional Requirements (NFRs)

- **Performance/SLOs:** p95 end-to-end ≤ **5 min** @ ≤ **30 pages**; per-auditor timeout ≤ **60s** avg.
- **Reliability:** CLI exit code 0 on success, non-zero on FAIL; idempotent re-runs.
- **Security/Privacy:** API keys from env; local storage; no PII expected; redact secrets from logs.
- **Compliance:** best-effort OWASP LLM prompts; audit log of decisions.
- **Accessibility:** outputs skimmable markdown; headings/TOC.
- **Observability:** print token/time counters; write JSON artifacts; basic error logs.
- **Data:** artifacts stored locally; configurable retention.

## 5) Evaluation & Quality

- **Offline:** JSON validity rate, dedupe quality, consensus repeatability on same inputs.
- **Online:** human spot-checks of Top Risks relevance (≥80% judged useful).
- **Promotion thresholds:** default consensus ≥ **3.8/5**, approvals ≥ **67%**, no CRITICAL.

## 6) Dependencies & Risks

- OpenAI (swap-able); Python 3.10+; optional LangGraph later.
- Risk: schema drift → validation + retries.

## 7) MVP Delivery Strategy & Scope Control

### M1: Core Foundation (Week 1-2) - **Absolute Basic Value**
**Goal:** Single command that produces readable audit output
- ✅ Basic CLI that ingests markdown docs (`audit.py ./docs`)
- ✅ Single auditor execution with structured JSON output
- ✅ Simple audit report generation (`audit.md`)
- ✅ Pass/fail decision logic with clear thresholds
- **Value Delivered:** Manual review replacement for single perspective

### M2: Multi-LLM Council (Week 3-4) - **Core Differentiation**  
**Goal:** Multi-perspective consensus that beats single AI
- ✅ Parallel execution of 6 specialized auditors (PM, Infra, Data, Security, UX, Cost)
- ✅ Consensus engine with trimmed mean algorithm and disagreement detection
- ✅ Structured artifact generation (`consensus_<DOC>.md`, `decision_<STAGE>.md`)
- ✅ Cost controls and caching for ≤$2 per run
- **Value Delivered:** Multi-perspective analysis superior to single AI or human reviewer

### M3: Document Pipeline (Week 5-6) - **Workflow Integration**
**Goal:** Gated promotion across document lifecycle  
- ✅ Full Vision → PRD → Architecture → Implementation workflow
- ✅ Cross-document alignment validation with backlog generation
- ✅ Quality gates with automated promotion decisions
- 🔄 Human review interface for strategic decisions and deadlock resolution
- **Value Delivered:** End-to-end document workflow with quality enforcement

### Future Iterations (Post-MVP) - **Advanced Capabilities**
**Captured for v2 to prevent scope creep:**
- Research agent for internet context gathering in vision stage
- Iterative LLM-to-LLM refinement loops with concrete question generation
- Advanced revision strategies for automatic document improvement
- Rich Web UI and real-time collaboration features
- Multi-repo integration and PR automation
- Advanced analytics and learning from feedback patterns

### Gate checklist (PRD → Architecture)

- [ ] All `R-PRD-###` have acceptance criteria & metric/target.
- [ ] NFRs include explicit SLOs + security notes.
- [ ] Eval plan set; thresholds defined.
- [ ] 0 **CRITICAL**, ≤3 **HIGH** open issues.
