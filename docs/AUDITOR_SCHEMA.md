# AUDITOR_SCHEMA.md — LLM Council Audit & Consensus Platform

**Owner (Eng/Arch):** Erik Cohen 
**Date:** 2025-08-29  
**Status:** Draft  
**Links:** [Architecture](./ARCHITECTURE.md) • [Implementation Plan](./IMPLEMENTATION_PLAN.md)

## 1) Overview

This document defines the schema and rubric for the LLM Council audit system. Each auditor provides structured feedback based on their specialized perspective, enabling consensus-based decision making and quality gates.

## 2) Audit Rubric Dimensions

All auditors evaluate documents across these core dimensions (1-5 scale):

### Core Quality Dimensions
| Dimension                | Description               | Poor (1-2)         | Good (3-4)         | Excellent (5)          |
| ------------------------ | ------------------------- | ------------------ | ------------------ | ---------------------- |
| **Simplicity**           | Clear, easy to understand | Complex, confusing | Mostly clear       | Crystal clear          |
| **Conciseness**          | No unnecessary content    | Verbose, redundant | Appropriate length | Perfectly concise      |
| **Actionability**        | Specific, implementable   | Vague, theoretical | Mostly actionable  | Immediately actionable |
| **Readability**          | Good flow and structure   | Poor structure     | Readable           | Excellent flow         |
| **Options/Tradeoffs**    | Considers alternatives    | No alternatives    | Some options       | Full analysis          |
| **Evidence/Specificity** | Concrete, detailed        | Generic, abstract  | Some details       | Rich evidence          |

### Pass/Fail Thresholds
- **PASS:** Average score ≥ 3.8/5 AND no dimension < 3.0
- **FAIL:** Average score < 3.8/5 OR any dimension < 3.0

## 3) Auditor Role Definitions

### 3.1) Product Manager (PM) Auditor
**Focus:** Business value, user needs, market fit, requirements clarity

**Specialized Evaluation Criteria:**
- Market opportunity validation
- User story completeness  
- Business metrics alignment
- Scope appropriateness for MVP
- Competitive differentiation clarity

**Key Questions:**
- Are user needs clearly articulated?
- Is the MVP scope realistic and valuable?
- Are success metrics quantified?
- Is market opportunity validated?

### 3.2) Infrastructure Auditor  
**Focus:** Scalability, reliability, performance, operations

**Specialized Evaluation Criteria:**
- Scalability considerations
- Reliability/availability planning
- Performance requirements
- Operational complexity
- Infrastructure cost implications

**Key Questions:**
- Can this scale to expected load?
- Are SLOs realistic and measurable?
- Is operational burden reasonable?
- Are failure modes considered?

### 3.3) Data/Evaluation Auditor
**Focus:** Data quality, analytics, measurement, AI/ML considerations

**Specialized Evaluation Criteria:**
- Data requirements clarity
- Evaluation methodology
- Quality metrics definition
- AI/ML feasibility
- Privacy/governance considerations

**Key Questions:**
- How will we measure success?
- Are data requirements feasible?
- Is the evaluation approach sound?
- Are privacy implications addressed?

### 3.4) Security Auditor
**Focus:** Security, privacy, compliance, risk assessment

**Specialized Evaluation Criteria:**
- Threat model completeness
- Security controls adequacy
- Privacy protection measures
- Compliance requirements
- Risk assessment quality

**Key Questions:**
- What are the security risks?
- Are privacy controls sufficient?
- Do we meet compliance requirements?
- Is the risk assessment comprehensive?

### 3.5) User Experience (UX) Auditor
**Focus:** Usability, accessibility, user journey, design considerations

**Specialized Evaluation Criteria:**
- User journey clarity
- Usability considerations
- Accessibility requirements
- Design system alignment
- User feedback mechanisms

**Key Questions:**
- Is the user experience intuitive?
- Are accessibility needs addressed?
- Is the user journey well-defined?
- How will we gather user feedback?

### 3.6) Cost Auditor  
**Focus:** Resource requirements, cost optimization, ROI analysis

**Specialized Evaluation Criteria:**
- Cost estimation accuracy
- Resource requirements
- ROI/business case strength
- Cost optimization opportunities
- Budget risk assessment

**Key Questions:**
- Are cost estimates realistic?
- Is ROI clearly demonstrated?
- Are there cost optimization opportunities?
- What are the budget risks?

## 4) Output Schema Definition

### 4.1) Individual Auditor Response Schema

```json
{
  "auditor_role": "string (pm|infrastructure|data_eval|security|ux|cost)",
  "document_analyzed": "string (vision|prd|architecture|implementation_plan)",
  "audit_timestamp": "ISO 8601 timestamp",
  "scores_detailed": {
    "simplicity": {
      "score": "number (1-5)",
      "pass": "boolean",
      "justification": "string (min 50 chars)",
      "improvements": ["string array of specific suggestions"]
    },
    "conciseness": {
      "score": "number (1-5)", 
      "pass": "boolean",
      "justification": "string (min 50 chars)",
      "improvements": ["string array of specific suggestions"]
    },
    "actionability": {
      "score": "number (1-5)",
      "pass": "boolean", 
      "justification": "string (min 50 chars)",
      "improvements": ["string array of specific suggestions"]
    },
    "readability": {
      "score": "number (1-5)",
      "pass": "boolean",
      "justification": "string (min 50 chars)", 
      "improvements": ["string array of specific suggestions"]
    },
    "options_tradeoffs": {
      "score": "number (1-5)",
      "pass": "boolean",
      "justification": "string (min 50 chars)",
      "improvements": ["string array of specific suggestions"]
    },
    "evidence_specificity": {
      "score": "number (1-5)",
      "pass": "boolean",
      "justification": "string (min 50 chars)",
      "improvements": ["string array of specific suggestions"]
    }
  },
  "overall_assessment": {
    "average_score": "number (calculated from scores)",
    "overall_pass": "boolean (avg >= 3.8 AND all dimensions >= 3.0)",
    "summary": "string (100-200 chars)",
    "top_strengths": ["string array (max 3)"],
    "top_risks": ["string array (max 3)"],
    "quick_wins": ["string array (max 3)"]
  },
  "blocking_issues": [
    {
      "severity": "string (critical|high|medium|low)",
      "category": "string (technical|business|legal|security|ux)",
      "description": "string (specific issue)",
      "impact": "string (what happens if not fixed)",
      "suggested_resolution": "string (how to fix)",
      "line_reference": "string (optional: line number or section)"
    }
  ],
  "alignment_feedback": {
    "upstream_consistency": {
      "score": "number (1-5)",
      "issues": ["string array of specific misalignments"],
      "suggestions": ["string array of alignment improvements"]
    },
    "internal_consistency": {
      "score": "number (1-5)", 
      "issues": ["string array of internal contradictions"],
      "suggestions": ["string array of consistency improvements"]
    }
  },
  "role_specific_insights": {
    // Dynamic object based on auditor role
    // PM: market_analysis, user_feedback, competitive_insights
    // Security: threat_analysis, compliance_gaps, risk_mitigation
    // etc.
  },
  "confidence_level": "number (1-5, how confident in this assessment)"
}
```

### 4.2) Consensus Engine Schema

```json
{
  "consensus_analysis": {
    "document": "string",
    "analysis_timestamp": "ISO 8601 timestamp",
    "participating_auditors": ["string array of roles"],
    "consensus_scores": {
      "simplicity": {
        "weighted_average": "number",
        "agreement_level": "number (0-1, variance measure)",
        "passing_votes": "number",
        "total_votes": "number"
      }
      // ... for each dimension
    },
    "overall_consensus": {
      "weighted_average": "number (trimmed mean of all dimensions)",
      "pass_threshold": "number (from config)",
      "approval_threshold": "number (from config)", 
      "consensus_pass": "boolean",
      "approval_pass": "boolean",
      "final_decision": "string (PASS|FAIL)"
    },
    "disagreement_analysis": [
      {
        "dimension": "string",
        "variance": "number",
        "outlier_auditors": ["string array"],
        "requires_review": "boolean"
      }
    ]
  },
  "consolidated_findings": {
    "top_risks": [
      {
        "risk": "string",
        "severity": "string",
        "supporting_auditors": ["string array"],
        "frequency": "number (how many auditors mentioned)"
      }
    ],
    "quick_wins": [
      {
        "improvement": "string", 
        "effort": "string (low|medium|high)",
        "supporting_auditors": ["string array"],
        "frequency": "number"
      }
    ],
    "blocking_issues": [
      {
        "issue": "consolidated blocking issue object",
        "supporting_auditors": ["string array"],
        "resolution_required": "boolean"
      }
    ]
  },
  "alignment_summary": {
    "upstream_alignment_score": "number (1-5)",
    "internal_alignment_score": "number (1-5)",
    "major_misalignments": ["string array"],
    "alignment_pass": "boolean",
    "backlog_items_generated": "number"
  }
}
```

## 5) Consensus Algorithm

### 5.1) Scoring Method
1. **Trimmed Mean:** Remove top and bottom 10% of scores, calculate mean
2. **Weight Adjustment:** Equal weight for all auditors (MVP), future: role-based weights
3. **Threshold Gates:** Both consensus score AND approval percentage must pass

### 5.2) Agreement Measurement  
- **High Agreement:** Standard deviation ≤ 0.5
- **Medium Agreement:** Standard deviation 0.5-1.0  
- **Low Agreement:** Standard deviation > 1.0
- **Review Required:** Low agreement on critical dimensions

### 5.3) Tie-Breaking
- If exactly at threshold: require human review
- If blocking issues exist: automatic FAIL regardless of scores
- If alignment fails: automatic FAIL with backlog generation

## 6) Quality Gates Configuration

```yaml
# config/quality_gates.yaml
consensus_thresholds:
  vision_to_prd: 
    score_threshold: 3.8
    approval_threshold: 0.67
    alignment_threshold: 4.0
  prd_to_architecture:
    score_threshold: 4.0  
    approval_threshold: 0.67
    alignment_threshold: 4.2
  architecture_to_implementation:
    score_threshold: 4.0
    approval_threshold: 0.75
    alignment_threshold: 4.5

auditor_config:
  roles: ["pm", "infrastructure", "data_eval", "security", "ux", "cost"]
  parallel_execution: true
  timeout_seconds: 60
  max_retries: 3
  
blocking_severity_gates:
  critical: 0  # No critical issues allowed
  high: 2     # Max 2 high severity issues  
  medium: 5   # Max 5 medium severity issues
```

## 7) Validation Rules

### 7.1) Schema Validation
- All required fields present
- Score values within 1-5 range
- Boolean fields are actual booleans
- Arrays contain expected types
- Timestamps in valid ISO format

### 7.2) Content Validation  
- Justification minimum length (50 chars)
- At least 1 improvement suggestion per dimension
- Blocking issues have all required fields
- Role-specific insights match auditor type

### 7.3) Logic Validation
- Pass/fail consistent with scores
- Average score calculation correct
- Alignment scores within reasonable bounds
- Confidence levels justified by content quality

### Gate checklist (Schema → Implementation)
- [ ] All 6 auditor roles defined with specific criteria
- [ ] JSON schema complete and validated
- [ ] Consensus algorithm mathematically sound
- [ ] Quality gates configurable via YAML
- [ ] Validation rules comprehensive
- [ ] 0 **CRITICAL**, ≤2 **HIGH** schema issues
