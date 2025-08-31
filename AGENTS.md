# AGENTS.md - LLM Council Audit & Consensus Platform

## Build/Test/Lint Commands

**Python:**
- `PYTHONPATH=src pytest tests/` - Run all backend tests (90 passing, 85% coverage)
- `PYTHONPATH=src pytest tests/test_schemas.py` - Run single test file
- `black .` - Format Python code (88 char line length)
- `mypy .` - Type checking

**Frontend:**
- `cd frontend && npm run dev` - Start development server
- `cd frontend && npm run build` - Build for production
- `cd frontend && npm run test` - Run Vitest tests
- `cd frontend && npm run check:fix` - Lint/format with Biome (tabs, 100 chars, single quotes)
- `cd frontend && npm run type-check` - TypeScript type checking

## Architecture

**Core:** FastAPI backend (`src/llm_council/ui_server.py`) + React frontend with WebSocket real-time updates  
**CLI:** `python audit.py ./docs --stage vision --interactive` for LLM council audits  
**Services:** Entity extraction, research expansion, consensus engine with trimmed mean algorithm  
**Templates:** YAML-based auditor configurations in `config/templates/`  
**Storage:** Local filesystem, no cloud dependencies

## Code Style & Conventions

**Python:** Black formatting, Pydantic models, async/await, relative imports (`..interfaces`), type hints  
**TypeScript:** Biome (tabs, single quotes, semicolons as-needed), strict TypeScript, path aliases (`@/`, `@shared/`)  
**Imports:** stdlib → third-party → local, `from __future__ import annotations`  
**Error Handling:** Structured exceptions with Pydantic validation, WebSocket error propagation
