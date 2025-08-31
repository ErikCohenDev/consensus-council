# PRD_PROVENANCE.md — Complete Provenance & Traceability System

**Owner:** Erik Cohen  
**Date:** 2025-08-30  
**Status:** Draft  
**Version:** Provenance (Phase 3)  
**Links:** [Vision](./VISION.md) | [PRD_MVP](./PRD_MVP.md) | [PRD_Platform](./PRD_PLATFORM.md)

## Goals

**G1:** Complete bidirectional traceability from vision to code functions  
**G2:** Zero orphan code - every artifact traces to requirements  
**G3:** Change impact analysis across documents, specs, and code  
**G4:** Runtime observability proving requirement satisfaction

## Use Cases

**UC1:** Developer changes function → sees impact on PRD, architecture, tests  
**UC2:** Product manager updates requirement → affected code/tests highlighted  
**UC3:** CI gates prevent merging code without requirement traceability  
**UC4:** Production telemetry proves requirements are satisfied at runtime

## Functional Requirements

| ID | Requirement | Priority | Acceptance |
|----|-------------|----------|------------|
| R-PROV-001 | Spec generation from PRDs (REQ-*.yaml, NFR-*.yaml) | Must | Machine-readable specs link to document requirements |
| R-PROV-002 | Code artifact graph (services → modules → classes → functions) | Must | Complete dependency mapping with metadata |
| R-PROV-003 | Provenance headers in all generated code | Must | IMPLEMENTS/VERIFIED_BY tags link to requirement IDs |
| R-PROV-004 | Traceability matrix auto-generation | Must | REQ_ID \| Code \| Tests \| Coverage matrix updated on changes |
| R-PROV-005 | Change impact analysis | Must | Show upstream (docs) and downstream (tests) effects |
| R-PROV-006 | CI gates for orphan code prevention | Must | Fail build if code lacks requirement tags |
| R-PROV-007 | Test layer tagging (unit/integration/E2E/NFR) | Must | Tests tagged with requirement and coverage data |
| R-PROV-008 | Runtime telemetry with requirement tagging | Should | Services emit metrics tagged with REQ/Component IDs |
| R-PROV-009 | Neo4j graph database integration | Should | Store and query artifact relationships |

## Spec & Schema Layer

**File Structure:**
```
/spec/
  requirements/REQ-*.yaml
  nfr/NFR-*.yaml  
  api/openapi.yaml
  schemas/*.json
```

**Provenance Headers:**
```
/*
 * SVC-101 IngestService
 * Implements: REQ-012, constrained by NFR-003
 * Contracts: openapi.yaml#/paths/~1upload
 * VerifiedBy: TEST-U-045, TEST-I-017
 * Generated: codegen@0.3 from REQ-012.yaml
 */
```

## Traceability Matrix

Auto-generated CSV/graph showing complete requirements coverage:

| REQ_ID | FRS | Code | Tests | Schema | Coverage | Status |
|--------|-----|------|-------|--------|----------|---------|
| REQ-012 | FRS-FEAT-101 | SVC-101__ingest.ts | TEST-U-045;TEST-I-017 | doc_v1.json | 92% | GREEN |

## CI/CD Gates

1. **No orphan code**: Every file must have REQ/NFR/FRS tag
2. **Test coverage**: Every requirement has ≥1 unit test, E2E tests for user journeys  
3. **Spec alignment**: Code matches OpenAPI/schema contracts
4. **Matrix completeness**: Traceability matrix has no gaps
5. **Change propagation**: Updates flow through all affected artifacts

## Neo4j Graph Schema

**Node Types:**
- :Idea, :PRD, :Requirement, :NFR, :Component, :Service, :Class, :File, :Test, :Schema

**Relationships:**  
- (:Service)-[:IMPLEMENTS]->(:Requirement)
- (:Test)-[:VERIFIES]->(:Service)  
- (:Requirement)-[:TRACES_TO]->(:PRD)
- (:Service)-[:EXPOSES]->(:Schema)

## Change Impact Analysis

**When code changes:**
- Show affected requirements (upstream)
- Show affected tests (downstream)  
- Show affected documentation
- Show affected schemas/contracts

**When requirements change:**
- Show implementing code files
- Show verification tests
- Show dependent components

## Success Metrics

- **Traceability Coverage**: 100% of code traces to requirements
- **Change Detection**: Impact analysis accuracy ≥95%
- **CI Gate Effectiveness**: Zero orphan code in production
- **Runtime Validation**: ≥90% of NFRs proven by telemetry
