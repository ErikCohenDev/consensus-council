# ARCHITECTURE.md — LLM Council Audit & Consensus Platform

**Owner (Eng/Arch):** Erik Cohen 
**Date:** 2025-08-29  
**Status:** Draft  
**Links:** [Vision](./VISION.md) • [PRD](./PRD.md)

## 0) Context & Constraints
- Small CLI; local files; deterministic gates; low cost; parallel fan-out.
- **Framework Strategy:** Start with lightweight custom orchestration + OpenAI structured outputs for MVP. Migrate to CrewAI for v2 when agent coordination complexity increases.
- **Template-Driven:** Project types (Software MVP, AI/ML, Hardware, etc.) have pre-configured auditor questions and scoring weights.
- **Human-in-the-Loop:** Strategic documents (Vision, PRD) and consensus deadlocks require human review and context injection.

## 1) High-Level Overview

- Components: CLI Orchestrator, Template Engine, Auditor Workers, Schema Validator, Dedupe/Ranker, Consensus Engine, Human Review Interface, Gate Evaluator, Alignment Analyzer, Cache/Artifacts.

```mermaid
flowchart LR
  U[User CLI] -->|docs/ + template| ORCH[Orchestrator]
  ORCH -->|load template| TMPL[Template Engine]
  TMPL -->|configure auditors| ORCH
  ORCH -->|fan-out| AUD1[Auditor: PM]
  ORCH --> AUD2[Auditor: Infra]
  ORCH --> AUD3[Auditor: Data/Eval]
  ORCH --> AUD4[Auditor: Security]
  ORCH --> AUD5[Auditor: UX]
  ORCH --> AUD6[Auditor: Cost]
  AUD1 & AUD2 & AUD3 & AUD4 & AUD5 & AUD6 --> VAL[Schema Validator]
  VAL --> ART[(Artifacts JSON)]
  ART --> CONS[Consensus Engine]
  CONS -->|Low Agreement or Strategic Doc| HUMAN[Human Review]
  CONS -->|High Agreement| GATE[Gate Evaluator]
  HUMAN -->|Add Context + Decision| GATE
  GATE -->|PASS| NEXT[Next Stage]
  GATE -->|FAIL or ALIGN MISMATCH| ALIGN[Alignment Backlog]
  ORCH --> CACHE[(Cache)]
  TMPL --> CONFIG[(Template Config)]
```

## 2) Data & Models

**Multi-Model Ensemble Strategy:**
- **Primary Models:** OpenAI GPT-4o, Anthropic Claude-3.5-Sonnet, Google Gemini-1.5-Pro
- **Specialized Providers:** OpenRouter (access to Grok, other models), Tavily (research context)
- **Model Assignment:** Different models per auditor role to maximize perspective diversity
- **Consensus Method:** Cross-model disagreement analysis with perspective synthesis

**Configuration:**
- Templates: YAML configs per project type with model assignments per role
- Artifacts: per-model-auditor JSON, `audit.md`, `consensus_<DOC>.md`, `decision_<STAGE>.md`, `alignment_backlog_<DOC>.md`
- Cache key: `(provider, model, template_hash, prompt_hash, content_hash)` - now includes provider

## 3) Interfaces & Contracts

- CLI: `audit.py <docs_dir> [--template] [--stage] [--ensemble] [--research-context] [--interactive]`
- Template Config: YAML defining auditor questions, model assignments per role, weights, and human review triggers
- Auditor Schema: `scores_detailed{criterion→{score,pass,justification,improvements}}`, `blocking_issues[]`, `model_perspective{unique_insights,model_bias_flags}`
- Multi-Model Response: Each auditor includes `model_provider` and `perspective_confidence` for diversity analysis
- Human Review Interface: Interactive prompts with cross-model disagreement analysis and perspective synthesis
- Exit codes: 0 success, 1 gate fail, 2 human review required, 3 model ensemble failure

## 4) Scaling & Performance
- Parallel auditor calls (configurable N).  
- Chunking when doc tokens > threshold.  
- Caching to minimize repeated calls.

## 5) Reliability & Operations
- Retries on JSON invalidity; graceful stop on `--max-calls`.  
- Idempotent runs; deterministic consensus thresholds from YAML.

## 6) Security & Privacy
- Secrets via env; redact logs; local filesystem only; no PII expected.  
- Audit log: write decision files with thresholds + counts.

## 7) Observability
- Token/time counters; counts in summary; artifacts persisted.

## 8) Cost & Viability
- Unit economics: #auditors × tokens; mitigations: cache, chunking, fewer roles.

## 9) Testing Strategy
- Unit: schema validators, consensus math.  
- Integration: full run on sample docs.  
- Golden tests: known inputs → fixed gate verdict.

## 10) Migration/Backfills
- None (MVP).

## 11) Decision Log (ADRs)

- ADR-001: Use CLI + files (not web) for MVP.  
- ADR-002: Trimmed weighted mean consensus (vs. majority/plurality).
- ADR-003: Start with custom orchestration + OpenAI structured outputs vs. LLM framework (CrewAI/LangGraph) for MVP to minimize complexity and maximize speed to market. Migrate to CrewAI for v2.
- ADR-004: Template-driven configuration over hardcoded questions to enable rapid new project type creation.
- ADR-005: Human-in-the-loop required for strategic documents (Vision/PRD) and consensus deadlocks. Automated decisions only for technical implementation docs.

### Gate checklist (Architecture → Implementation)
- [ ] Diagram + component boundaries defined.  
- [ ] Data flow, cache key, contracts documented.  
- [ ] Security/observability/cost strategies documented.  
- [ ] 0 **CRITICAL**, ≤4 **HIGH** open issues.
