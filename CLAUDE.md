# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **LLM Council Audit & Consensus Platform** - a CLI tool that uses multiple LLM "auditors" (PM, Infrastructure, Data/Eval, Security, UX, Cost) to review and validate project documents through quality gates. The system enforces consensus-based document promotion from Research Brief → Market Scan → Vision → PRD → Architecture → Implementation Plan.

## Core Architecture

The platform uses a **template-driven orchestration system** with parallel LLM auditor execution:

- **CLI Orchestrator**: Main entry point (`audit.py`) - ✅ IMPLEMENTED
- **Template Engine**: YAML-based project templates defining auditor questions and scoring weights
- **Auditor Workers**: Parallel execution of specialized LLM auditors (6 roles)
- **Consensus Engine**: Trimmed mean algorithm with configurable thresholds
- **Human Review Interface**: Strategic decisions and deadlock resolution
- **Gate Evaluator**: Pass/fail decisions based on consensus + blocking issues

## Development Commands

### Setup and Dependencies

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your-key-here"
# Optional: export ANTHROPIC_API_KEY="your-key-here"
```

### Project Initialization

```bash
# Initialize project documents (interactive template selection)
python scripts/init_docs.py

# Initialize with specific parameters
python scripts/init_docs.py --project "Your Project" --owner "Your Name" --template software_mvp

# List available project templates
python scripts/init_docs.py --list-templates

# Force overwrite existing docs
python scripts/init_docs.py --force
```

### Testing (when implemented)

```bash
# Unit tests
pytest

# Integration tests with async support
pytest -v tests/

# Code formatting
black .

# Type checking
mypy .
```

### Audit Commands (✅ IMPLEMENTED)

```bash
# Interactive mode (human review for strategic docs)
python audit.py ./docs --stage vision --interactive

# Auto mode (skip human review, fail on disagreement)
python audit.py ./docs --stage architecture --auto-approve

# Full pipeline with human checkpoints
python audit.py ./docs --full-pipeline --interactive

# Custom template and model
python audit.py ./docs --template ai_ml_project --model claude-3-5-sonnet

# With cost controls
python audit.py ./docs --max-calls 30 --model gpt-4o
```

## Key Configuration Files

- **`config/quality_gates.yaml`**: Consensus thresholds, auditor configuration, human review triggers
- **`config/templates/`**: Project-type specific auditor questions and scoring weights
- **`project_config.yaml`**: Generated project configuration (copied from selected template)

## Document Workflow and Quality Gates

The system enforces a sequential document workflow with quality gates:

1. **Research Brief** → Market Scan (human review required)
2. **Market Scan** → Vision (human review required)
3. **Vision** → PRD (human review required)
4. **PRD** → Architecture (human review required)
5. **Architecture** → Implementation Plan (auto-approve if consensus)

**Human Review Triggers:**

- Strategic documents (Research, Market, Vision, PRD)
- Low consensus (std dev > 1.0)
- Critical/high severity blocking issues
- Consensus deadlock after 3 attempts

## Template System

Templates define auditor behavior per project type:

- **`software_mvp.yaml`**: Standard software product development
- **`ai_ml_project.yaml`**: Machine learning/AI projects
- **`hardware_product.yaml`**: Hardware product development
- **`research_project.yaml`**: Research and academic projects
- **`service_business.yaml`**: Service-based business models

Each template specifies:

- Stage-specific auditor questions and focus areas
- Human review requirements by stage
- Scoring weight adjustments per auditor role
- Key decision points requiring human judgment

## Consensus Algorithm

Uses **trimmed mean** approach:

- Remove top/bottom 10% scores to reduce outlier impact
- Weighted scoring based on template configuration
- Minimum approval threshold (typically 67%)
- Alignment scoring to detect upstream document mismatches

## Cost Controls

- Caching by `(model, template_hash, prompt_hash, content_hash)`
- Configurable token limits per auditor (4000 default)
- Max total calls per run (50 default)
- Target: ≤$2/run for typical document set

## Security and Privacy

- API keys from environment variables only
- Local filesystem storage (no cloud dependencies)
- Secret redaction in logs
- No PII expected in document content
- Audit trail in decision files

## File Structure

```
docs/                    # Project documentation (sequential workflow)
├── RESEARCH_BRIEF.md    # Problem validation, methodology
├── MARKET_SCAN.md       # Competitive analysis, build/buy decisions
├── VISION.md            # Product vision, MVP scope, success metrics
├── PRD.md               # Requirements with R-PRD-### IDs
├── ARCHITECTURE.md      # Technical design, components, diagrams
├── IMPLEMENTATION_PLAN.md # Task breakdown with T-### IDs
├── AUDITOR_SCHEMA.md    # LLM council structure and rubrics
└── HUMAN_REVIEW_INTERFACE.md # Human-in-the-loop design

config/
├── quality_gates.yaml  # Consensus thresholds, blocking severity
└── templates/          # Project-type specific configurations

scripts/
└── init_docs.py        # Project initialization utility
```

## Development Notes

- **MVP Focus**: CLI + local files + OpenAI structured outputs
- **v2 Migration Path**: CrewAI/LangGraph when agent coordination complexity increases
- **Performance Target**: ≤5 min p95 for 4 documents, ≤30 pages total
- **Idempotent Runs**: Same inputs should produce deterministic results
- **Exit Codes**: 0=success, 1=gate fail, 2=human review required

## Implementation Status (83% Complete - 67 Tests Passing)

### ✅ **COMPLETED COMPONENTS:**
- **JSON Schema**: ✅ Complete Pydantic models with validation (`schemas.py`)
- **Template Engine**: ✅ YAML configuration loading with fallbacks (`templates.py`)  
- **CLI Interface**: ✅ Full audit.py implementation with all options (`cli.py`)
- **Consensus Engine**: ✅ Trimmed mean algorithm with agreement detection (`consensus.py`)
- **Orchestrator**: ✅ Async parallel execution with retry logic (`orchestrator.py`)

### 🟡 **REMAINING GAPS:**
- **Artifact Generation**: File output naming needs standardization (`audit.md`, `decision_<STAGE>.md`)
- **Caching System**: Hash-based caching for cost optimization (≤$2/run target)
- **Alignment Validation**: Cross-document consistency checking
- **Human Review UI**: Interactive prompts for strategic decisions

## ADRs (Architectural Decision Records)

- **ADR-001**: CLI + files (not web) for MVP simplicity
- **ADR-002**: Trimmed weighted mean consensus vs majority/plurality
- **ADR-003**: Custom orchestration + OpenAI vs LLM frameworks for MVP speed
- **ADR-004**: Template-driven configuration vs hardcoded questions
- **ADR-005**: Human-in-the-loop required for strategic documents and deadlocks
