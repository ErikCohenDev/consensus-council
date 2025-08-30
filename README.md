# LLM Council Audit & Consensus Platform

From idea → plan → implementation.

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
 - **[GLOSSARY.md](./docs/GLOSSARY.md)** — Shared terminology, data model, and flow diagram

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

4. **Run the LLM council audit:**

   ```bash
   # Required: choose a stage to audit (e.g., vision, prd, architecture)
   python audit.py ./docs --stage vision --interactive

   # Enable research context (Vision stage):
   python audit.py ./docs --stage vision --interactive --research-context

   # Enable council debate mode (multi-round discussion between roles):
   python audit.py ./docs --stage prd --council-debate

   # Use a specific template and model:
   python audit.py ./docs --stage architecture \
     --template config/templates/software_mvp.yaml \
     --model gpt-4o
   ```

> Keep each file brief. If a section is not applicable, write **N/A (why)** rather than leaving it blank.
> Use markdown features (tables, task lists, code blocks) for clarity.

## 🌐 Web UI

Two ways to run the UI:

- Development (recommended):
  - Backend: `python -m src.llm_council.ui_server`
  - Frontend: `cd frontend && npm install && npm run dev` (Vite dev server at `http://localhost:3000`, proxying `/api` and `/ws` to `http://localhost:8000`)

- Production-like:
  - Build: `cd frontend && npm install && npm run build`
  - Start backend: `python -m src.llm_council.ui_server`
  - The server serves `frontend/dist` automatically at `/` and assets at `/assets`.

If `frontend/dist` is missing, the server shows a short message with setup instructions at `/`.

## 🔌 HTTP API (Projects & Runs)

- Start a run (preferred resource model):

  curl -X POST http://localhost:8000/api/projects/my-project/runs \
    -H 'Content-Type: application/json' \
    -d '{"stage":"vision","model":"gpt-4o"}'

  Response:
  { "success": true, "data": { "runId": "...", "startedAt": 172495... }, "timestamp": ... }

- Get run snapshot:

  curl http://localhost:8000/api/projects/my-project/runs/<runId>

  Response data matches shared schema (camelCase):
  { "pipeline": { "documents": [...], "overallStatus": "running", ... }, "metrics": { ... } }

- Legacy aliases (still supported during migration):
  - `POST /api/audits` (body includes `docsPath`)
  - `GET /api/audits/{auditId}`

- Config:
  - `GET /api/templates` → list available templates
  - `GET /api/quality-gates` → returns `config/quality_gates.yaml` (if present)

## ✅ Testing & Coverage

- Backend (pytest):
  - `pytest --maxfail=1 --disable-warnings -q`
  - With coverage: `pytest --cov=src/llm_council --cov-report=term-missing`

- Frontend (Vitest):
  - `cd frontend && npm run test`
  - With coverage/UI: `npm run test:coverage` or `npm run test:ui`

Targets: backend ≥85%, frontend ≥80%. See `docs/TEST_PLAN.md` and `docs/TRACEABILITY_MATRIX.md`.
