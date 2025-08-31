# PRD_MVP.md — Core LLM Council System

**Owner:** Erik Cohen  
**Date:** 2025-08-30  
**Status:** Draft  
**Version:** MVP (Phase 1)  
**Links:** [Vision](./VISION.md) | [PRD_Platform](./PRD_PLATFORM.md)

## Goals

**G1:** Generate audit + consensus verdict from documents in ≤5 min  
**G2:** Multi-LLM council with human-in-loop for strategic decisions  
**G3:** Keep operational costs ≤$2/run with caching

## Use Cases

**UC1:** Founder runs council audit on Vision → PRD → Architecture → Implementation Plan  
**UC2:** Product team uses interactive debate mode for strategic decisions  
**UC3:** Engineering lead gates document promotion through CLI/Web UI

## Functional Requirements

| ID | Requirement | Priority | Acceptance |
|----|-------------|----------|------------|
| R-MVP-001 | CLI accepts markdown docs and produces audit outputs | Must | `python audit.py ./docs` works without manual prompts |
| R-MVP-002 | Multi-model council (PM→GPT-4o, Security→Claude, etc.) | Must | Each auditor returns valid JSON with diverse perspectives |
| R-MVP-003 | Consensus engine with weighted rubric | Must | Weighted score ≥ threshold & approvals ≥ 2/3 for PASS |
| R-MVP-004 | Human review for strategic docs and low consensus | Must | Interactive prompts when consensus fails or variance high |
| R-MVP-005 | Alignment validation across documents | Must | Detect upstream mismatches, generate backlog with fixes |
| R-MVP-006 | Web UI for real-time visualization | Should | Dashboard shows council debates and consensus status |
| R-MVP-007 | Caching by (model, prompt, content hash) | Should | Re-run unchanged inputs costs ≤10% of first run |

## Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|---------|
| NFR-MVP-001 | Performance: audit completion time | ≤5 min p95 |
| NFR-MVP-002 | Cost: operational expense per run | ≤$2.00 |
| NFR-MVP-003 | Reliability: valid JSON artifacts | ≥99% |
| NFR-MVP-004 | Usability: CLI success rate | ≥95% first-time users |

## API Endpoints

```
POST /api/projects/{project}/runs
GET  /api/projects/{project}/runs/{runId} 
GET  /api/templates
POST /api/audits (legacy)
```

## Success Metrics

- **Time to Value**: Idea → validated documents ≤15 min
- **Decision Quality**: Human override rate ≤20%  
- **Cost Efficiency**: ≤$2/run average
- **User Satisfaction**: ≥4.5/5 rating
