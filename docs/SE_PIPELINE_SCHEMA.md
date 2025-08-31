# Systems Engineering Pipeline Schema

## Graph-Native Artifact Flow

```mermaid
erDiagram
    PARADIGM {
        string framework_id PK
        string name
        string description
        json question_set
        json validation_rules
        string created_at
    }
    
    ENTITY {
        string id PK
        string label
        string type
        string description
        float importance
        float certainty
        json se_meta
        string paradigm_id FK
        Stage stage
        Status status
        ArtifactLayer layer
        json provenance_chain
    }
    
    SE_META {
        ValueMetrics value_metrics
        RiskMetrics risk_metrics
        CostData cost_data
        WSJFMetrics wsjf_metrics
    }
    
    VALUE_METRICS {
        float reach
        float frequency
        float pain
        float willingness_to_pay
        float product_fit
    }
    
    RISK_METRICS {
        float severity
        float likelihood
        float exposure
        float confidence
    }
    
    COST_DATA {
        float one_time
        float monthly
        float effort_points
    }
    
    WSJF_METRICS {
        float business_value
        float time_criticality
        float risk_reduction
        float effort
    }
    
    RELATIONSHIP {
        string id PK
        string source_id FK
        string target_id FK
        string type
        string label
        float strength
        string description
        float propagation_factor
    }
    
    ARTIFACT_PROJECTION {
        ArtifactLayer layer PK
        json entities
        json relationships
        json focus_areas
        json decisions
        json traceability
    }
    
    MVP_CUT {
        json selected_entities
        json deferred_entities
        float total_value
        float total_risk
        float total_cost
        float feasibility_score
    }
    
    COMPONENT {
        string component_id PK
        string name
        string function
        json interfaces
        json nfr_constraints
        json dependencies
        float estimated_effort
        json assigned_entities
    }
    
    TASK {
        string task_id PK
        string title
        string description
        string component_id FK
        WSJFMetrics wsjf_metrics
        json dependencies
        float estimated_hours
        string assigned_to
        string sprint_target
    }
    
    SPECIFICATION {
        string spec_id PK
        string type
        string file_path
        json content
        json linked_requirements
        json linked_entities
        string generated_from
        string last_updated
    }
    
    CODE_ARTIFACT {
        string artifact_id PK
        string file_path
        string artifact_type
        json implements_specs
        json verified_by_tests
        json depends_on
        json exposes
        json consumes
        json provenance_header
        string last_sync
    }
    
    TEST_ARTIFACT {
        string test_id PK
        string file_path
        string test_type
        json verifies_requirements
        json tests_code_artifacts
        json covers_interfaces
        json validates_use_cases
        float coverage_percent
        string last_run
    }
    
    TELEMETRY_TAG {
        string tag_id PK
        string req_id FK
        string component_id FK
        json metric_data
        json trace_data
        json evidence_data
        string timestamp
    }

    PARADIGM ||--o{ ENTITY : guides
    ENTITY ||--|| SE_META : has
    SE_META ||--|| VALUE_METRICS : contains
    SE_META ||--|| RISK_METRICS : contains
    SE_META ||--|| COST_DATA : contains
    SE_META ||--|| WSJF_METRICS : contains
    ENTITY ||--o{ RELATIONSHIP : source
    ENTITY ||--o{ RELATIONSHIP : target
    ENTITY ||--o{ SPECIFICATION : generates
    SPECIFICATION ||--o{ CODE_ARTIFACT : implements
    CODE_ARTIFACT ||--o{ TEST_ARTIFACT : verified_by
    CODE_ARTIFACT ||--o{ TELEMETRY_TAG : emits
    ARTIFACT_PROJECTION }o--|| ENTITY : projects
    MVP_CUT }o--|| ENTITY : selects
    COMPONENT }o--|| ENTITY : implements
    TASK }o--|| COMPONENT : decomposes
```

## Layered Artifact Pipeline

```mermaid
flowchart TD
    I[1. Idea Input\n+Paradigm Selection] --> E[2. Context Expansion\n+Research +Entities]
    E --> V[3. Vision Layer\n+ConOps +Why]
    V --> P[4. PRD Layer\n+Requirements +What]
    P --> SP[5. Spec Layer\n+REQ/NFR YAML]
    SP --> A[6. Architecture Layer\n+Components +How]
    A --> IM[7. Implementation Layer\n+Tasks +WBS]
    IM --> CG[8. Code Generation\n+Provenance Headers]
    CG --> TL[9. Test Layer\n+Tagged Coverage]
    TL --> RT[10. Runtime/Observability\n+Telemetry Tags]
    
    IM --> M[MVP Cut\n+Resource Optimization]
    M --> CG
    
    V -->|Council Debate| VC[Vision Consensus]
    P -->|Council Debate| PC[PRD Consensus]
    A -->|Council Debate| AC[Architecture Consensus]
    IM -->|Council Debate| IC[Implementation Consensus]
    
    VC --> P
    PC --> A
    AC --> IM
    IC --> M
    
    M -->|Feedback| P
    M -->|Feedback| A
    
    subgraph "SE Pipeline Operations"
        EXP[Expand\nAddNodes, LinkEvidence, InferEdges]
        ASS[Assess\nComputeValue, ComputeRisk, Propagate]
        CON[Condense\nSolveCutSet, Budget Constraints]
        DEC[Decompose\nFunctional→Physical, Interfaces]
        ALL[Allocate\nWSJF, Team Assignment]
        VER[Verify\nTests, Gates, V&V]
    end
    
    E --> EXP
    EXP --> ASS
    ASS --> CON
    CON --> DEC
    DEC --> ALL
    ALL --> VER
    VER -->|learn| ASS
```

## Entity Type Hierarchy by Layer

```mermaid
graph TD
    subgraph "Vision Layer"
        VI_PROB[Problem Space]
        VI_AUD[Target Audience]
        VI_OUT[Desired Outcomes]
        VI_CONST[Constraints]
    end
    
    subgraph "PRD Layer"
        PRD_FR[Functional Requirements]
        PRD_NFR[Non-Functional Requirements]
        PRD_USER[User Stories]
        PRD_ACC[Acceptance Criteria]
    end
    
    subgraph "Architecture Layer"
        ARCH_COMP[Components]
        ARCH_INT[Interfaces]
        ARCH_DATA[Data Flows]
        ARCH_SEC[Security Controls]
    end
    
    subgraph "Spec Layer"
        SPEC_REQ[REQ-*.yaml Files]
        SPEC_NFR[NFR-*.yaml Files] 
        SPEC_API[OpenAPI/GraphQL Schemas]
        SPEC_DATA[JSON-Schema/Proto Files]
    end
    
    subgraph "Implementation Layer"
        IMPL_TASK[Development Tasks]
        IMPL_TEST[Test Cases]
        IMPL_DEP[Dependencies]
        IMPL_RISK[Implementation Risks]
    end
    
    subgraph "Code Artifact Layer"
        CODE_SVC[Services]
        CODE_MOD[Modules]
        CODE_CLS[Classes]
        CODE_FUN[Functions]
    end
    
    subgraph "Test Layer"
        TEST_UNIT[Unit Tests (REQ-tagged)]
        TEST_INT[Integration Tests (Interface-tagged)]
        TEST_E2E[E2E Tests (Use-case-tagged)]
        TEST_NFR[NFR Tests (Performance/Security)]
    end
    
    subgraph "Runtime Layer"
        RT_METRICS[Telemetry Metrics]
        RT_TRACES[Distributed Traces]
        RT_LOGS[Application Logs]
        RT_SLO[SLO Validation]
    end
    
    subgraph "MVP Scoped"
        MVP_FEAT[MVP Features]
        MVP_TASK[MVP Tasks]
        MVP_MILE[Milestones]
    end
    
    VI_PROB --> PRD_FR
    VI_AUD --> PRD_USER
    VI_OUT --> PRD_ACC
    PRD_FR --> SPEC_REQ
    PRD_NFR --> SPEC_NFR
    SPEC_REQ --> ARCH_COMP
    SPEC_NFR --> ARCH_SEC
    ARCH_COMP --> IMPL_TASK
    ARCH_INT --> IMPL_DEP
    IMPL_TASK --> CODE_SVC
    CODE_SVC --> CODE_MOD
    CODE_MOD --> CODE_CLS
    CODE_CLS --> CODE_FUN
    CODE_FUN --> TEST_UNIT
    SPEC_API --> TEST_INT
    PRD_USER --> TEST_E2E
    SPEC_NFR --> TEST_NFR
    TEST_UNIT --> RT_METRICS
    TEST_NFR --> RT_SLO
    IMPL_TASK --> MVP_TASK
    PRD_FR --> MVP_FEAT
```

## Value/Risk Propagation Model

```mermaid
graph LR
    subgraph "Value Flow"
        A[Core Idea\nValue: 0.9] -->|enables 0.8| B[Feature A\nValue: 0.72]
        A -->|enables 0.6| C[Feature B\nValue: 0.54]
        B -->|requires 0.9| D[Infrastructure\nValue: 0.65]
    end
    
    subgraph "Risk Flow"
        A2[Core Idea\nRisk: 0.3] -->|mitigates 0.7| B2[Security Control\nRisk: 0.21]
        A2 -->|increases 0.5| C2[Complexity Risk\nRisk: 0.45]
    end
    
    subgraph "Cost Aggregation"
        D1[Component 1\n$10k] 
        D2[Component 2\n$15k]
        D3[Component 3\n$8k]
        D1 --> TOT[Total MVP Cost\n$33k]
        D2 --> TOT
        D3 --> TOT
    end
```

## Decision Gates & Consensus Points

```mermaid
stateDiagram-v2
    [*] --> IdeaInput
    IdeaInput --> ContextExpansion
    ContextExpansion --> VisionDebate
    
    VisionDebate --> VisionConsensus : Council Agreement
    VisionDebate --> HumanReview : Low Consensus
    HumanReview --> VisionConsensus : Human Decision
    
    VisionConsensus --> PRDDebate
    PRDDebate --> PRDConsensus : Council Agreement
    PRDDebate --> HumanReview2 : Low Consensus
    HumanReview2 --> PRDConsensus : Human Decision
    
    PRDConsensus --> ArchDebate
    ArchDebate --> ArchConsensus : Council Agreement
    ArchDebate --> HumanReview3 : Low Consensus
    HumanReview3 --> ArchConsensus : Human Decision
    
    ArchConsensus --> ImplPlanning
    ImplPlanning --> MVPCut : Budget/Risk Analysis
    MVPCut --> ResourceAllocation
    ResourceAllocation --> [*]
    
    note right of VisionConsensus
        Layer: Vision
        Focus: Why, What outcome
        Entities: Problems, Audiences, Goals
    end note
    
    note right of PRDConsensus
        Layer: PRD
        Focus: What system should do
        Entities: Requirements, Stories, Criteria
    end note
    
    note right of ArchConsensus
        Layer: Architecture
        Focus: How system works
        Entities: Components, Interfaces, Controls
    end note
    
    note right of ResourceAllocation
        Layer: Implementation
        Focus: Who, When, How much
        Entities: Tasks, Sprints, Dependencies
    end note
```