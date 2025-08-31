# ARCHITECTURE_COMPLETE.md — Complete Idea Operating System

**Owner:** Erik Cohen  
**Date:** 2025-08-30  
**Status:** Complete Technical Architecture  
**Links:** [Vision](./VISION.md) | [PRD_MVP](./PRD_MVP.md) | [PRD_Platform](./PRD_PLATFORM.md) | [PRD_Provenance](./PRD_PROVENANCE.md)

## System Overview

Complete pipeline from raw idea → production code with Neo4j graph backend, multi-model LLM council, research expansion, and bidirectional provenance tracking through every layer.

## Architecture Layers

### 1. Graph Data Layer (Neo4j)

**Technology Choice:** Neo4j Community/Enterprise  
**Justification:** Native graph operations, Cypher query language, APOC procedures, excellent performance for relationship traversals  
**Alternative Considered:** ArangoDB (rejected: less mature ecosystem), PostgreSQL with recursive CTEs (rejected: poor performance at scale)

**Core Schema:**
```cypher
// Idea Layer
(:Idea)-[:CONTAINS]->(:Problem)
(:Idea)-[:TARGETS]->(:ICP)
(:Idea)-[:MAKES]->(:Assumption)
(:Idea)-[:BOUNDED_BY]->(:Constraint)
(:Idea)-[:AIMS_FOR]->(:Outcome)

// Research Layer  
(:Problem)-[:RESEARCHED_BY]->(:ResearchSource)
(:ICP)-[:VALIDATED_BY]->(:Evidence)
(:Competitor)-[:ADDRESSES]->(:Problem)
(:Market)-[:CONTAINS]->(:ICP)

// Document Layer
(:PRD)-[:SELECTS]->(:Requirement)
(:Requirement)-[:CONSTRAINED_BY]->(:NFR)
(:Requirement)-[:TRACES_TO]->(:Problem)

// Code Layer
(:Service)-[:IMPLEMENTS]->(:Requirement)
(:Service)-[:EXPOSES]->(:Interface)
(:Service)-[:COMPOSED_OF]->(:Module)
(:Module)-[:CONTAINS]->(:Class)
(:Class)-[:DEFINES]->(:Function)

// Test Layer
(:Test)-[:VERIFIES]->(:Function)
(:Test)-[:COVERS]->(:Requirement)
(:E2ETest)-[:VALIDATES]->(:UserJourney)
```

**Universal Node Properties:**
```yaml
meta:
  id: string
  name: string  
  stage: mvp|v1|v2|backlog|cut
  status: ideated|validated|implemented|deployed|retired
  risk_weight: float
  value_weight: float
  confidence: float
  evidence_refs: [string]
  provenance: {source, tool, version, timestamp}
  owners: [string]
  updated_at: timestamp
```

### 2. Question & Review System

**Technology Choice:** FastAPI + WebSocket + React Hook Form  
**Justification:** Real-time question flow, form validation, seamless human-LLM handoff  

**Question Generation Pipeline:**
```python
# src/llm_council/services/question_engine.py
class QuestionEngine:
    def generate_paradigm_questions(
        self, 
        paradigm: Paradigm, 
        graph: IdeaGraph
    ) -> List[Question]:
        """Generate questions based on paradigm template and graph gaps"""
        
    def prioritize_human_questions(
        self, 
        questions: List[Question]
    ) -> Tuple[List[Question], List[Question]]:
        """Split into human-required vs LLM-answerable"""
        
    def create_review_session(
        self, 
        questions: List[Question]
    ) -> ReviewSession:
        """Create reviewable question batch with context"""
```

**Human Review Interface:**
- **Question Card UI**: Context + question + suggested LLM answer + human override
- **Batch Review Mode**: Review all paradigm questions in single session  
- **Progress Tracking**: Show completion % and remaining critical questions
- **Context Panel**: Show related graph entities and research evidence

### 3. Research Expansion Engine

**Technology Choice:** Tavily API + Custom Web Scraping + LangChain Document Loaders  
**Justification:** Tavily for structured research, custom scraping for competitors, LangChain for document processing  

```python
# src/llm_council/services/research_expander.py
class ResearchExpander:
    def expand_market_context(self, problem: Problem) -> MarketContext:
        """TAM/SAM/SOM, industry reports, regulations"""
        
    def analyze_competitors(self, problem: Problem) -> List[Competitor]:
        """Direct/indirect competitors, positioning, features"""
        
    def validate_assumptions(self, assumptions: List[Assumption]) -> List[Evidence]:
        """Find supporting/contradicting evidence"""
        
    def enrich_icp(self, icp: ICP) -> EnrichedICP:
        """Demographics, pain points, willingness to pay"""
```

**Research Sources Integration:**
- **Tavily API**: Industry reports, market data, regulatory info
- **Company websites**: Competitor analysis, feature comparison  
- **GitHub/Product Hunt**: Technical alternatives, adoption metrics
- **Regulatory databases**: Compliance requirements (GDPR, HIPAA, SOX)

### 4. Multi-Model Council System

**Technology Choice:** LiteLLM for unified interface + Custom role assignments  
**Justification:** Single API for all providers, cost optimization, role-based model selection  

**Council Architecture:**
```python
# src/llm_council/council_members.py
class CouncilMember:
    role: CouncilRole  # PM, Security, UX, Infrastructure, Data, Cost
    model_provider: str  # openai, anthropic, google, meta
    model_name: str
    personality_prompt: str
    rubric_weights: Dict[str, float]
    
class Council:
    def debate_topic(self, topic: DebateTopic) -> Consensus:
        """Multi-round debate between council members"""
        
    def generate_consensus(self, responses: List[Response]) -> Consensus:
        """Trimmed mean + agreement analysis"""
        
    def escalate_to_human(self, topic: DebateTopic, reason: str) -> HumanDecision:
        """Human-in-loop when consensus fails"""
```

**Model Selection Strategy:**
- **PM Role**: OpenAI GPT-4o (general reasoning, business context)  
- **Security Role**: Claude 3.5 Sonnet (careful analysis, risk assessment)
- **Infrastructure Role**: Google Gemini Pro (technical depth, scalability)
- **UX Role**: OpenAI GPT-4o (human empathy, user experience)
- **Data Role**: Google Gemini Pro (analytics, ML/AI understanding)
- **Cost Role**: Claude 3.5 Sonnet (conservative financial analysis)

**Consensus Algorithm:**
1. **Initial Responses**: Each member provides scored response (0-1) + rationale
2. **Debate Rounds**: Members can respond to each other (max 2 rounds)  
3. **Trimmed Mean**: Remove outliers, weight by role importance
4. **Variance Check**: If std dev > 0.3, trigger human escalation
5. **Final Decision**: PASS/FAIL + reasoning + human override option

### 5. Provenance & Traceability System

**Technology Choice:** Neo4j + File System Headers + CI/CD Hooks  
**Justification:** Graph naturally represents traceability, file headers for local reference, CI hooks for enforcement

**Complete Provenance Chain:**
```
Idea → Problem → Requirement → Architecture → Component → Service → 
File → Module → Class → Function → Test → E2E → Runtime Telemetry
```

**File Header Template:**
```typescript
/*
 * ServiceName: UserAuthService  
 * Implements: REQ-001, REQ-015, constrained by NFR-SEC-001
 * Architecture: COMP-AUTH-001 (Authentication Component)
 * Tests: TEST-U-001, TEST-I-005, TEST-E2E-002
 * Generated: 2025-08-30 by codegen@1.2 from ARCH-001.yaml
 * Provenance: Problem(P-001) -> Requirement(REQ-001) -> Component(COMP-AUTH-001)
 */
```

**Traceability Matrix Auto-Generation:**
```sql
-- Cypher query to generate traceability matrix
MATCH (r:Requirement)-[:IMPLEMENTED_BY]->(s:Service)
OPTIONAL MATCH (s)<-[:VERIFIES]-(t:Test)  
OPTIONAL MATCH (r)<-[:COVERS]-(e:E2ETest)
RETURN r.id as REQ_ID, 
       s.name as SERVICE, 
       collect(t.id) as UNIT_TESTS,
       collect(e.id) as E2E_TESTS,
       s.coverage as COVERAGE,
       CASE WHEN s.status = 'implemented' AND size(collect(t)) > 0 
            THEN 'GREEN' ELSE 'RED' END as STATUS
```

### 6. Code Generation & Architecture Engine

**Technology Choice:** Jinja2 Templates + OpenAPI Code Generation + Custom AST manipulation  
**Justification:** Proven templating, standard OpenAPI tooling, fine-grained control with AST

**Generation Pipeline:**
```python
# src/llm_council/services/codegen_engine.py
class CodegenEngine:
    def generate_service_skeleton(
        self, 
        component: Component, 
        requirements: List[Requirement]
    ) -> ServiceCode:
        """Generate service structure with provenance headers"""
        
    def generate_test_suite(
        self, 
        service: Service,
        requirements: List[Requirement]  
    ) -> TestSuite:
        """Generate unit/integration/e2e test skeletons"""
        
    def generate_openapi_spec(
        self, 
        interfaces: List[Interface]
    ) -> OpenAPISpec:
        """Generate API contracts from architecture"""
        
    def update_traceability_matrix(self) -> TraceabilityMatrix:
        """Scan code, update Neo4j graph, generate matrix"""
```

**Template Structure:**
```
/templates/
  service/
    fastapi_service.py.j2
    service_test.py.j2  
    dockerfile.j2
  frontend/
    react_component.tsx.j2
    component_test.tsx.j2
  infrastructure/
    docker-compose.yml.j2
    github_workflow.yml.j2
```

### 7. CI/CD Integration & Gates

**Technology Choice:** GitHub Actions + Custom hooks + Neo4j queries  
**Justification:** Integrated with development workflow, custom validation, graph-powered checks

**Quality Gates:**
```yaml
# .github/workflows/provenance-gates.yml
- name: Check Provenance Headers
  run: python tools/check-provenance.py
  # Fails if any file lacks REQ/NFR/COMP tags
  
- name: Validate Traceability Matrix  
  run: python tools/validate-traceability.py
  # Fails if requirements lack implementing code/tests
  
- name: Update Graph Database
  run: python tools/sync-neo4j.py  
  # Syncs code changes to Neo4j graph
  
- name: Generate Impact Analysis
  run: python tools/impact-analysis.py ${{ github.event.pull_request.number }}
  # Comments on PR with change impact
```

**Orphan Code Prevention:**
```python
# tools/check-provenance.py
def validate_file_provenance(file_path: str) -> ValidationResult:
    """Check if file has valid REQ/NFR/COMP tags in header"""
    
def find_orphan_functions() -> List[OrphanFunction]:
    """Find functions without requirement traceability"""
    
def generate_provenance_report() -> ProvenanceReport:
    """Generate coverage report for all artifacts"""
```

## Implementation Phases

### Phase 1: Graph Foundation (4 weeks)
- **Week 1**: Neo4j setup, schema design, basic CRUD operations
- **Week 2**: Idea capture UI, entity extraction, graph visualization  
- **Week 3**: Research expansion engine, Tavily integration
- **Week 4**: Question system, human review interface

### Phase 2: Council & Consensus (3 weeks)  
- **Week 1**: Multi-model council setup, role definitions, LiteLLM integration
- **Week 2**: Debate system, consensus algorithm, human escalation
- **Week 3**: Council UI, real-time debate visualization, decision tracking

### Phase 3: Provenance System (4 weeks)
- **Week 1**: Code artifact graph, file system scanning  
- **Week 2**: Provenance header system, template engine
- **Week 3**: Traceability matrix generation, CI/CD integration
- **Week 4**: Impact analysis, change propagation visualization

### Phase 4: Integration & Polish (2 weeks)
- **Week 1**: End-to-end testing, performance optimization
- **Week 2**: Documentation, deployment automation, monitoring

## Technical Decisions & Trade-offs

### Database Choice: Neo4j vs Alternatives
**Chosen**: Neo4j Community Edition  
**Pros**: Native graph operations, excellent query performance, mature ecosystem  
**Cons**: Learning curve, memory usage, licensing costs at scale  
**Alternatives**: PostgreSQL with recursive CTEs (performance), ArangoDB (less mature)

### Model Selection: Multi-provider vs Single
**Chosen**: Multi-provider strategy via LiteLLM  
**Pros**: Risk mitigation, role-specific optimization, cost arbitrage  
**Cons**: Complexity, consistency challenges, multiple API keys  
**Alternatives**: Single provider (vendor lock-in), open-source only (capability gaps)

### Code Generation: Template-based vs LLM-based  
**Chosen**: Template-based with LLM-assisted customization  
**Pros**: Deterministic output, version control friendly, fast generation  
**Cons**: Less flexible than pure LLM generation  
**Alternatives**: Pure LLM (consistency issues), manual coding (slow)

### Frontend Framework: React vs Vue vs Svelte
**Chosen**: React with TypeScript  
**Pros**: Ecosystem maturity, team familiarity, graph visualization libraries  
**Cons**: Bundle size, complexity  
**Alternatives**: Vue (smaller ecosystem), Svelte (less mature)

## Success Metrics & Monitoring

**Performance Targets:**
- Idea → Document generation: ≤5 minutes
- Graph query response time: ≤100ms p95  
- Code generation: ≤30 seconds for service skeleton
- Traceability matrix update: ≤10 seconds

**Quality Targets:**  
- Provenance coverage: 100% (no orphan code)
- Test coverage: ≥85% per requirement  
- Council consensus rate: ≥80% (≤20% human escalation)
- Change impact accuracy: ≥95%

**Operational Monitoring:**
- Neo4j performance metrics (query time, memory usage)
- LLM API costs and latency per provider  
- CI/CD gate pass/fail rates
- User satisfaction scores for generated questions/code
