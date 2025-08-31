# Directory Structure & File Naming Conventions
## Complete Paradigm-to-Code Pipeline

This document defines the standardized directory structure and file naming conventions for the complete idea-to-code pipeline with absolute provenance tracking.

## Project Root Structure

```
my_project/
├── paradigm/                          # Paradigm Selection & Initial Context
│   ├── paradigm_selection.yaml        # YC/McKinsey/Lean framework choice + rationale
│   ├── initial_entities.json          # Core entities: Problem, ICP, Assumptions, Constraints
│   └── context_questions.yaml         # Framework-specific questions + human answers
│
├── context/                           # Research & Context Expansion
│   ├── research_sources.json          # Market/industry/competition data sources
│   ├── entity_graph.json             # Complete entity-relationship graph
│   └── expansion_log.md               # Research expansion decisions + evidence
│
├── docs/                              # Document Generation Layer
│   ├── VISION.md                      # Problem framing, ICP, outcomes, value creation
│   ├── PRD.md                         # Parent PRD for increment (MVP/R1/R2)
│   ├── sub_prds/                      # Feature-specific PRDs
│   │   ├── FRS-AUTH-001.md           # Authentication feature PRD
│   │   ├── FRS-USER-002.md           # User management feature PRD
│   │   └── FRS-DATA-003.md           # Data storage feature PRD
│   ├── ARCHITECTURE.md                # High-level C4 + ADRs + risk controls
│   └── IMPLEMENTATION_PLAN.md         # Task breakdown (WBS) tied to PRD/Architecture
│
├── specs/                             # Machine-Readable Contracts Layer
│   ├── requirements/                  # Functional requirements
│   │   ├── REQ-AUTH-001.yaml         # Authentication requirements
│   │   ├── REQ-USER-002.yaml         # User management requirements
│   │   └── REQ-DATA-003.yaml         # Data requirements
│   ├── nfrs/                         # Non-functional requirements
│   │   ├── NFR-PERF-001.yaml         # Performance requirements
│   │   ├── NFR-SEC-002.yaml          # Security requirements
│   │   └── NFR-SCALE-003.yaml        # Scalability requirements
│   ├── interfaces/                   # API contracts
│   │   ├── api_auth.openapi.yaml     # Authentication API spec
│   │   ├── api_users.openapi.yaml    # User management API spec
│   │   └── api_data.graphql          # Data query API spec
│   └── schemas/                      # Data contracts
│       ├── user.json-schema          # User data schema
│       ├── auth_token.proto          # Authentication token schema
│       └── api_response.json-schema  # Standard API response schema
│
├── src/                              # Code Artifact Graph Layer
│   ├── services/                     # Business logic services
│   │   ├── auth_service.py           # IMPLEMENTS: REQ-AUTH-001, FRS-AUTH-001
│   │   ├── user_service.py           # IMPLEMENTS: REQ-USER-002, FRS-USER-002
│   │   └── data_service.py           # IMPLEMENTS: REQ-DATA-003, FRS-DATA-003
│   ├── models/                       # Data models
│   │   ├── user_model.py             # IMPLEMENTS: user.json-schema
│   │   ├── auth_model.py             # IMPLEMENTS: auth_token.proto
│   │   └── api_models.py             # IMPLEMENTS: api_response.json-schema
│   ├── controllers/                  # API endpoints
│   │   ├── auth_controller.py        # IMPLEMENTS: api_auth.openapi.yaml
│   │   ├── user_controller.py        # IMPLEMENTS: api_users.openapi.yaml
│   │   └── data_controller.py        # IMPLEMENTS: api_data.graphql
│   └── utils/                        # Shared utilities
│       ├── validation.py             # IMPLEMENTS: multiple schemas
│       └── common.py                 # IMPLEMENTS: cross-cutting concerns
│
├── tests/                            # Test Layer with Complete Tagging
│   ├── unit/                         # Unit tests (REQ-tagged)
│   │   ├── test_auth_service.py      # VERIFIES: REQ-AUTH-001, auth_service.py
│   │   ├── test_user_service.py      # VERIFIES: REQ-USER-002, user_service.py
│   │   └── test_data_service.py      # VERIFIES: REQ-DATA-003, data_service.py
│   ├── integration/                  # Integration tests (interface-tagged)
│   │   ├── test_auth_api.py          # VERIFIES: api_auth.openapi.yaml
│   │   ├── test_user_api.py          # VERIFIES: api_users.openapi.yaml
│   │   └── test_data_api.py          # VERIFIES: api_data.graphql
│   ├── e2e/                         # End-to-end tests (use-case-tagged)
│   │   ├── test_user_registration.py # VERIFIES: UC-001 (user signup flow)
│   │   ├── test_user_login.py        # VERIFIES: UC-002 (user login flow)
│   │   └── test_data_crud.py         # VERIFIES: UC-003 (data management flow)
│   └── nfr/                         # Non-functional requirement tests
│       ├── test_performance.py       # VERIFIES: NFR-PERF-001
│       ├── test_security.py          # VERIFIES: NFR-SEC-002
│       └── test_scalability.py       # VERIFIES: NFR-SCALE-003
│
├── traceability/                     # Traceability & Provenance Layer
│   ├── matrix.csv                    # Auto-generated REQ_ID|FRS|Code|Tests|Schema|Coverage|Status
│   ├── impact_graph.json            # Dependency graph for impact analysis
│   ├── provenance_log.json          # Complete audit trail of all changes
│   └── orphan_detection.json        # Report of orphaned code/tests/requirements
│
├── governance/                       # Governance & Audit Layer
│   ├── council_debates/             # Council decision transcripts
│   │   ├── vision_debate_001.json   # Vision stage council discussion
│   │   ├── prd_debate_002.json      # PRD stage council discussion
│   │   └── arch_debate_003.json     # Architecture stage council discussion
│   ├── human_overrides/             # Human decision justifications
│   │   ├── auth_strategy_override.md # Human decision on authentication approach
│   │   └── data_privacy_override.md  # Human decision on data privacy approach
│   └── lifecycle_log.json           # Node state transitions: ideated → implemented → deployed
│
└── observability/                    # Runtime & Telemetry Layer
    ├── telemetry_config.yaml        # REQ/Component ID tagging configuration
    ├── slo_mappings.yaml            # SLOs linked to NFR graph nodes
    └── production_evidence/          # Runtime proof of requirement satisfaction
        ├── req_auth_001_metrics.json # Performance data for auth requirements
        ├── nfr_perf_001_traces.json  # Performance traces for NFR validation
        └── compliance_report.json    # Security/compliance requirement evidence
```

## File Naming Conventions

### ID Patterns
```
REQ-{DOMAIN}-{NUMBER}     # REQ-AUTH-001, REQ-USER-002, REQ-DATA-003
NFR-{TYPE}-{NUMBER}       # NFR-PERF-001, NFR-SEC-002, NFR-SCALE-003  
FRS-{FEATURE}-{NUMBER}    # FRS-AUTH-001, FRS-USER-002, FRS-DATA-003
T-{COMPONENT}-{NUMBER}    # T-AUTH-001, T-USER-002, T-DATA-003
UC-{NUMBER}               # UC-001, UC-002, UC-003
ADR-{NUMBER}              # ADR-001, ADR-002, ADR-003
```

### Code Provenance Headers
```python
"""
Authentication Service

IMPLEMENTS: REQ-AUTH-001, FRS-AUTH-001, NFR-SEC-002
VERIFIED_BY: test_auth_service.py, test_auth_api.py
DEPENDS_ON: user_model.py, validation.py
EXPOSES: /api/auth/login, /api/auth/logout, /api/auth/refresh
CONSUMES: user.json-schema, auth_token.proto
LINKED_TO: VISION.md#user-security, PRD.md#authentication-requirements
LAST_SYNC: 2025-08-30 (auto-updated on change)
"""
```

### Test Provenance Headers
```python
"""
Authentication Service Unit Tests

VERIFIES: REQ-AUTH-001 (user authentication requirements)
TESTS: auth_service.py (authentication business logic)
COVERS: login_user(), logout_user(), refresh_token(), validate_credentials()
INTERFACES: api_auth.openapi.yaml paths /login, /logout, /refresh
USE_CASES: UC-001 (user signup), UC-002 (user login)
LAST_SYNC: 2025-08-30 (auto-updated on code change)
"""
```

## Symmetry Enforcement Rules

### CI/CD Gates
1. **No Orphan Code**: Every .py file must have provenance header with IMPLEMENTS tag
2. **Test Coverage**: Every IMPLEMENTS must have corresponding VERIFIED_BY test file
3. **Spec Alignment**: Every API endpoint must match OpenAPI/GraphQL schema
4. **Requirement Coverage**: Every REQ-*.yaml must have implementing code
5. **Change Propagation**: Any code change triggers impact analysis and affected doc updates

### Auto-Generated Artifacts
- `traceability/matrix.csv` - Updated on every commit
- `traceability/impact_graph.json` - Dependency graph for change analysis  
- `traceability/orphan_detection.json` - Weekly scan for orphaned artifacts
- `observability/production_evidence/` - Runtime telemetry proving requirement satisfaction

## Examples

### Example REQ File: `specs/requirements/REQ-AUTH-001.yaml`
```yaml
id: REQ-AUTH-001
title: User Authentication System
description: System must authenticate users with OAuth 2.0 and maintain secure sessions
priority: HIGH
source_documents:
  - docs/PRD.md#authentication-requirements
  - docs/sub_prds/FRS-AUTH-001.md
acceptance_criteria:
  - Users can log in with OAuth 2.0 providers (Google, GitHub)
  - Sessions expire after 24 hours of inactivity
  - Failed login attempts are rate-limited
implementing_code:
  - src/services/auth_service.py
  - src/controllers/auth_controller.py
  - src/models/auth_model.py
verified_by:
  - tests/unit/test_auth_service.py
  - tests/integration/test_auth_api.py
  - tests/e2e/test_user_login.py
interfaces:
  - specs/interfaces/api_auth.openapi.yaml
last_updated: 2025-08-30
```

### Example Code File: `src/services/auth_service.py`
```python
"""
Authentication Service

IMPLEMENTS: REQ-AUTH-001, FRS-AUTH-001, NFR-SEC-002
VERIFIED_BY: tests/unit/test_auth_service.py, tests/integration/test_auth_api.py
DEPENDS_ON: src/models/user_model.py, src/utils/validation.py
EXPOSES: /api/auth/login, /api/auth/logout, /api/auth/refresh
CONSUMES: specs/schemas/user.json-schema, specs/schemas/auth_token.proto
LINKED_TO: docs/VISION.md#user-security, docs/PRD.md#authentication-requirements
LAST_SYNC: 2025-08-30
"""

from typing import Optional
from src.models.auth_model import AuthToken, UserCredentials
from src.models.user_model import User

class AuthService:
    """Handles user authentication with OAuth 2.0 providers"""
    
    def login_user(self, credentials: UserCredentials) -> Optional[AuthToken]:
        """
        IMPLEMENTS: REQ-AUTH-001.acceptance_criteria[0] (OAuth login)
        VERIFIES: User can log in with OAuth 2.0 providers
        """
        pass
    
    def logout_user(self, token: AuthToken) -> bool:
        """
        IMPLEMENTS: REQ-AUTH-001.acceptance_criteria[1] (session management)
        VERIFIES: Sessions can be properly terminated
        """
        pass
```

This structure ensures complete symmetry and traceability from initial idea through runtime telemetry.