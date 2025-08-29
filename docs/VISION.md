# VISION.md — LLM Council Audit & Consensus Platform (MVP)

**Owner:** Erik Cohen
**Date:** 2025-08-29  
**Status:** Draft

## 1) One-liner

Generate concise, evidence-anchored audits of product docs (Vision → PRD → Architecture → Implementation Plan) using an ensemble of LLM “auditors,” then gate promotion via consensus and alignment checks—so MVPs stay small, shippable, and defensible.

## 2) Problem & JTBD

- _Problem:_ Doc reviews are slow, inconsistent, and prone to scope creep. Important risks (security, eval, scalability, cost) are missed; feedback lacks traceability.
- _JTBD:_ “As a founder/PM/lead, I want fast, multi-perspective audits with actionable fixes and clear go/no-go gates.”

## 3) Target users

- **Founder/PM**: wants clear Top Risks + Quick Wins to shape MVP.
- **Senior engineer**: wants line-anchored, testable fixes.
- **Stakeholders**: want one readable `audit.md` and a pass/fail gate.

## 4) Value & differentiation

- **Multi-model ensemble council**: Different LLMs (OpenAI, Claude, Gemini, Grok) per auditor role to maximize perspective diversity and reduce single-model bias
- **Cross-model consensus**: Models can learn from each other's insights through disagreement analysis and perspective synthesis  
- **Role-based specialization** with **rubric** (simplicity, concision, actionability, readability, options/tradeoffs, evidence/specificity)
- **Consensus math** + **alignment back-prop**: only advance when docs align across all models
- Small, automatable CLI; caching; cost caps; research agent integration

## 5) MVP scope (IMPLEMENTED ✅)

**✅ In MVP:**

- **Council Debate System**: CouncilMember objects with personalities, debate styles, and multi-round discussion
- **Multi-Model Ensemble**: OpenAI + Anthropic + Google + OpenRouter (Grok) via LiteLLM for maximum perspective diversity
- **Research Agent**: Tavily integration for internet context gathering in vision stage  
- **Complete Document Pipeline**: Research Brief → Market Scan → Vision → PRD → Architecture → Implementation Plan
- **Cross-Document Alignment**: Validation with backlog generation for misaligned transitions
- **Structured Outputs**: `audit.md`, `consensus_<DOC>.md`, `decision_<STAGE>.md`, `alignment_backlog_<DOC>.md`
- **Cost Controls**: Caching system achieving ≤$2/run target with parallel execution

**🔮 Future (v2):** Advanced council moderation, learning from feedback, real-time debate UI, cross-repo integration

## 6) Success metrics (initial targets)

- p95 end-to-end runtime ≤ **5 min** for ≤ **30 pages** total.
- Default run cost ≤ **$2** with caching on.
- JSON validity ≥ **99%**; gate decisions deterministic.

## 7) Constraints & assumptions

- Python CLI; OpenAI (swap-able); optional LangGraph spine later.
- Docs are markdown; no PII expected.
- Local file outputs, no DB required.

## 8) Cross-cutting notes (brief)

- **Security/Privacy:** keys via env; local artifacts; no PII expected.
- **Usability:** one command, clear outputs; readable `audit.md`.
- **Maintainability:** small modules; YAML config; tests.
- **Scalability:** parallel auditors; chunking if needed.
- **Viability/Cost:** caching + max call caps; small default council.
- **Evaluation/Obs:** per-auditor JSON; counters for cost/time.

## 9) Risks & open questions

- Model drift → enforce JSON schema, retries.
- Duplicate findings → simple dedupe + rank.
- Thin alignment heuristics → expand after MVP.

### Gate checklist (Vision → PRD)

- [ ] Quantified success metrics set.
- [ ] MVP scope explicit (3–5 bullets).
- [ ] Research step included.
- [ ] 0 **CRITICAL**, ≤2 **HIGH** open issues.
