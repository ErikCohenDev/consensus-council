# Docs Index — LLM Council Audit & Consensus Platform

This folder contains the minimal documents to go from idea → plan → implementation.

## 📋 Document Workflow (Sequential Gates)

**Research Phase:**

- **[RESEARCH_BRIEF.md](./docs/RESEARCH_BRIEF.md)** — Problem validation, hypothesis, research methodology
- **[MARKET_SCAN.md](./docs/MARKET_SCAN.md)** — Competitive analysis, market opportunity, BUILD/BUY/PARTNER decision

**Design Phase:**

- **[VISION.md](./docs/VISION.md)** — Why this matters, who it serves, MVP scope and success
- **[PRD.md](./docs/PRD.md)** — Requirements (with `R-PRD-###` IDs), acceptance criteria, NFRs, eval plan
- **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** — Design to satisfy the PRD (components, data, interfaces, SLOs, security, diagrams)

**Implementation Phase:**

- **[IMPLEMENTATION_PLAN.md](./docs/IMPLEMENTATION_PLAN.md)** — Task breakdown with `T-###`, TDD-ready, owners/estimates, traceability back to PRD
- **[AUDITOR_SCHEMA.md](./docs/AUDITOR_SCHEMA.md)** — LLM council structure, rubric, consensus algorithm, quality gates
- **[HUMAN_REVIEW_INTERFACE.md](./docs/HUMAN_REVIEW_INTERFACE.md)** — Human-in-the-loop design for strategic decisions and consensus deadlocks

## 🚪 Quality Gates

Each document must pass consensus from our LLM council (PM, Infrastructure, Data/Eval, Security, UX, Cost auditors) before proceeding. **Strategic documents require human review**, while technical documents can auto-approve with high consensus:

- **Research Brief → Market Scan:** Problem validated, research plan approved _(human review)_
- **Market Scan → Vision:** BUILD decision justified, market opportunity clear _(human review)_
- **Vision → PRD:** Success metrics quantified, MVP scope realistic _(human review)_
- **PRD → Architecture:** All requirements mapped, no critical gaps _(human review)_
- **Architecture → Implementation:** Design complete, tasks traceable _(auto-approve if consensus)_

**Human Review Triggers:**

- Strategic documents (Research, Market, Vision, PRD)
- Low consensus between auditors (stdev > 1.0)
- Blocking issues detected
- Consensus deadlock after 3 attempts

## 🛠️ Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**

   ```bash
   export OPENAI_API_KEY="your-key-here"
   # Optional: export ANTHROPIC_API_KEY="your-key-here"
   ```

3. **Initialize your project documents:**

   ```bash
   python scripts/init_docs.py --project "Your Project" --owner "Your Name"
   # Or run interactively: python scripts/init_docs.py
   ```

4. **Run the LLM council audit (when implemented):**

   ```bash
   # Interactive mode (human review for strategic docs)
   python audit.py ./docs --stage vision --interactive

   # Auto mode (skip human review, fail on disagreement)
   python audit.py ./docs --stage architecture --auto-approve

   # Full pipeline with human checkpoints
   python audit.py ./docs --full-pipeline --interactive
   ```

> Keep each file brief. If a section is not applicable, write **N/A (why)** rather than leaving it blank.
> Use markdown features (tables, task lists, code blocks) for clarity.
