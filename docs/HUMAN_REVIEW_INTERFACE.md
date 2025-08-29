# Human Review Interface Specification

## Overview
The human review interface is triggered when:
1. Strategic documents (Research, Market Scan, Vision, PRD) are being audited
2. LLM auditors have significant disagreement (stdev > threshold)  
3. Blocking issues are detected
4. Strategic tradeoffs are identified
5. After max consensus attempts without resolution

## Interface Flow

### 1. Review Trigger Display
```
🚨 Human Review Required

Stage: Vision Document
Trigger: Strategic document + Low consensus (stdev: 1.3)

Auditor Disagreement Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Simplicity:     PM(4.0) UX(3.0) Cost(4.5) → stdev: 0.8
• Actionability:  PM(3.0) UX(4.5) Cost(2.5) → stdev: 1.0  
• MVP Scope:      PM(5.0) UX(2.0) Cost(4.0) → stdev: 1.5 ⚠️

Key Disagreements:
• UX Auditor flagged "MVP scope too ambitious for 6 months"  
• PM Auditor scored high on "market opportunity clarity"
• Cost Auditor concerned about "infrastructure complexity"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2. Detailed Auditor Perspectives  
```
📋 Detailed Auditor Feedback

PM Auditor (Overall: 4.0/5):
✅ Strengths:
  • Clear value proposition for target users
  • Well-defined success metrics
  • Strong competitive differentiation

⚠️  Concerns:
  • Consider market timing risks
  • Validate user research depth

UX Auditor (Overall: 3.2/5):  
✅ Strengths:
  • User journey well mapped
  • Accessibility considerations included

🚨 Major Concerns:
  • MVP scope includes 8 features - recommend 3-4 max
  • User testing plan insufficient for timeline
  • Mobile experience not clearly defined

Cost Auditor (Overall: 3.8/5):
✅ Strengths:
  • Business model clearly defined
  • Revenue projections realistic

⚠️  Concerns:
  • Infrastructure costs may exceed budget
  • Customer acquisition costs not validated
```

### 3. Context Injection Prompts
```
🤔 Help Resolve Disagreement

The auditors disagree about MVP scope complexity. 

Current MVP includes:
• User auth & profiles
• Content creation tools  
• Social sharing features
• Analytics dashboard
• Payment processing
• Mobile app
• Admin panel
• Integration APIs

Questions for you:
1. What's the most critical user problem this solves? 
2. What's the minimum feature set for user validation?
3. What timeline/budget constraints should auditors consider?
4. Are there technical constraints they should know about?

Your context will help auditors re-evaluate with this information.
```

### 4. Human Decision Interface
```
🎯 Your Decision

Based on auditor feedback and your additional context, how should we proceed?

Options:
[1] APPROVE - Pass to next stage with current document
[2] REVISE - Make changes and re-audit  
[3] ADD CONTEXT - Provide more information for auditors to reconsider
[4] OVERRIDE - Pass despite auditor concerns (requires justification)
[5] ABORT - Stop the audit process

Enter choice [1-5]: _

If REVISE selected:
📝 What changes will you make?
□ Reduce MVP scope (remove features)
□ Clarify timeline/budget constraints  
□ Add user research validation
□ Define mobile experience approach
□ Other: ________________

If ADD CONTEXT selected:
💬 Additional context for auditors:
_____________________________________________
_____________________________________________
```

### 5. Decision Recording
```
✅ Human Review Decision Recorded

Stage: Vision Document
Decision: REVISE  
Rationale: Reduce MVP scope based on UX auditor feedback
Changes planned:
  • Remove mobile app from MVP (Phase 2)
  • Remove integration APIs (Phase 2) 
  • Focus on core content creation + sharing
  • Add user testing milestones

Re-audit scheduled with updated document.
```

## CLI Implementation

```bash
# Interactive mode (default for strategic docs)
python audit.py ./docs --stage vision --interactive

# Force automated mode (skip human review)  
python audit.py ./docs --stage vision --auto-approve

# Show what would trigger human review without running
python audit.py ./docs --stage vision --dry-run --show-triggers
```

## Integration Points

### With Consensus Engine
- Consensus engine detects low agreement or strategic triggers
- Passes control to HumanReviewInterface 
- Receives decision and optional context
- Re-runs consensus with human input if needed

### With Template System
- Templates define which stages require human review
- Templates specify key decision points per stage
- Templates provide context prompts tailored to project type

### With Audit Artifacts
- Human decisions recorded in `human_review_<STAGE>.md`
- Context injections logged for auditor re-evaluation
- Decision rationale included in final `decision_<STAGE>.md`

## Error Handling
- Timeout after 30 minutes of inactivity
- Save partial state for resume later
- Clear exit codes for automation integration
- Graceful degradation if human unavailable (log for later review)

## Future Enhancements (v2)
- Web interface for remote review
- Multi-reviewer workflows (PM + Eng Lead approval)
- Template-based decision trees
- Integration with project management tools
