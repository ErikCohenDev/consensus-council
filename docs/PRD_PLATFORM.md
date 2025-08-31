# PRD_PLATFORM.md — Idea Operating System Platform

**Owner:** Erik Cohen  
**Date:** 2025-08-30  
**Status:** Draft  
**Version:** Platform (Phase 2)  
**Links:** [Vision](./VISION.md) | [PRD_MVP](./PRD_MVP.md) | [PRD_Provenance](./PRD_PROVENANCE.md)

## Goals

**G1:** Transform ideas into production-ready software with complete traceability  
**G2:** Support multiple development paradigms (YC, McKinsey, Lean, Design Thinking)  
**G3:** Automated context expansion through research APIs

## Use Cases

**UC1:** Founder selects YC paradigm, answers questions, gets market research context  
**UC2:** Product manager generates hierarchical PRDs from idea graph  
**UC3:** Team collaborates on paradigm-specific questions with AI assistance  
**UC4:** Research API enriches context with competitors, market size, regulations

## Functional Requirements

| ID | Requirement | Priority | Acceptance |
|----|-------------|----------|------------|
| R-PLAT-001 | Paradigm selection engine (YC, McKinsey, Lean, Design Thinking) | Must | Framework selection with paradigm-specific questions |
| R-PLAT-002 | Interactive idea capture with entity extraction | Must | Problem, ICP, Assumptions, Constraints extracted from text |
| R-PLAT-003 | Research API integration for context expansion | Must | Market, competitor, industry data auto-filled |
| R-PLAT-004 | Entity graph visualization with ReactFlow | Must | Interactive graph showing relationships between entities |
| R-PLAT-005 | Question generation based on paradigm gaps | Must | Auto-generate follow-up questions from template |
| R-PLAT-006 | Human-AI collaboration on strategic questions | Must | LLM suggests, human refines, context preserved |
| R-PLAT-007 | Document generation from enriched graph | Must | Vision → PRD → Architecture from same graph data |
| R-PLAT-008 | Multi-paradigm comparison mode | Should | Compare YC vs McKinsey approach side-by-side |

## Research API Integration

**Endpoints:**
- Market size and TAM/SAM/SOM data
- Competitor analysis and positioning  
- Industry regulations and compliance requirements
- Technology trends and benchmarks

**Data Sources:**
- Public market research reports
- Competitor websites and documentation
- Regulatory databases  
- Industry analysis platforms

## Paradigm Templates

### YC Framework
- Problem validation questions
- Customer development focus
- Market-first approach
- Ramen profitability metrics

### McKinsey Framework  
- MECE problem decomposition
- Hypothesis-driven structure
- 80/20 analysis approach
- Executive summary format

### Lean Startup
- Value hypothesis definition
- Growth hypothesis validation
- Build-measure-learn loops
- Pivot/persevere decisions

### Design Thinking
- Empathy mapping
- User journey analysis
- Prototype testing approach
- Human-centered design

## Success Metrics

- **Paradigm Coverage**: All 4 frameworks supported
- **Context Enrichment**: ≥5 research sources per idea
- **Question Quality**: ≥80% user approval on generated questions  
- **Framework Adoption**: Users complete full paradigm flow ≥70%
