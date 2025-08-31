"""Neo4j client for idea graph management and complete provenance tracking."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from neo4j import GraphDatabase, Driver, Session
from pydantic import BaseModel, Field

from ..models.idea_models import (
    IdeaGraph, 
    EntityData, 
    Problem, 
    ICP, 
    Assumption, 
    Constraint, 
    Outcome,
    ExtractedEntities
)
from ..models.se_models import (
    SEEntity,
    SERelationship,
    SEContextGraph,
    Stage,
    Status,
    ArtifactLayer
)

logger = logging.getLogger(__name__)

class Neo4jConfig(BaseModel):
    """Neo4j connection configuration."""
    uri: str = Field(default="bolt://localhost:7687")
    username: str = Field(default="neo4j")
    password: str = Field(default="password")
    database: str = Field(default="neo4j")

class Neo4jClient:
    """Neo4j client for complete idea-to-code graph management."""
    
    def __init__(self, config: Neo4jConfig):
        self.config = config
        self.driver: Optional[Driver] = None
        
    def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password)
            )
            # Test connection
            with self.driver.session(database=self.config.database) as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("Connected to Neo4j successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self) -> None:
        """Close Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def create_indexes(self) -> None:
        """Create necessary indexes for performance."""
        indexes = [
            "CREATE INDEX idea_id IF NOT EXISTS FOR (i:Idea) ON (i.id)",
            "CREATE INDEX requirement_id IF NOT EXISTS FOR (r:Requirement) ON (r.id)",
            "CREATE INDEX service_name IF NOT EXISTS FOR (s:Service) ON (s.name)",
            "CREATE INDEX function_name IF NOT EXISTS FOR (f:Function) ON (f.name)",
            "CREATE INDEX test_id IF NOT EXISTS FOR (t:Test) ON (t.id)",
            "CREATE INDEX provenance_source IF NOT EXISTS FOR (n) ON (n.provenance_source)",
        ]
        
        with self.driver.session(database=self.config.database) as session:
            for index in indexes:
                try:
                    session.run(index)
                    logger.debug(f"Created index: {index}")
                except Exception as e:
                    logger.warning(f"Failed to create index {index}: {e}")

    # ============= Idea Graph Management =============
    
    def create_idea_graph(self, idea_input: str, paradigm: str) -> str:
        """Create initial idea node and return idea ID."""
        idea_id = str(uuid4())
        
        query = """
        CREATE (i:Idea {
            id: $idea_id,
            content: $content,
            paradigm: $paradigm,
            status: 'ideated',
            created_at: datetime(),
            updated_at: datetime(),
            stage: 'mvp',
            confidence: 0.5,
            risk_weight: 0.0,
            value_weight: 0.0
        })
        RETURN i.id as id
        """
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, {
                "idea_id": idea_id,
                "content": idea_input,
                "paradigm": paradigm
            })
            return result.single()["id"]
    
    def add_extracted_entities(
        self, 
        idea_id: str, 
        entities: Dict[str, List[Dict[str, Any]]]
    ) -> None:
        """Add extracted entities (Problem, ICP, Assumptions, etc.) to idea graph."""
        
        with self.driver.session(database=self.config.database) as session:
            # Add problems
            for problem_data in entities.get("problems", []):
                self._create_problem(session, idea_id, problem_data)
            
            # Add ICPs
            for icp_data in entities.get("icps", []):
                self._create_icp(session, idea_id, icp_data)
            
            # Add assumptions
            for assumption_data in entities.get("assumptions", []):
                self._create_assumption(session, idea_id, assumption_data)
            
            # Add constraints
            for constraint_data in entities.get("constraints", []):
                self._create_constraint(session, idea_id, constraint_data)
            
            # Add outcomes
            for outcome_data in entities.get("outcomes", []):
                self._create_outcome(session, idea_id, outcome_data)
    
    def _create_problem(self, session: Session, idea_id: str, problem_data: Dict) -> str:
        """Create problem node linked to idea."""
        problem_id = str(uuid4())
        
        query = """
        MATCH (i:Idea {id: $idea_id})
        CREATE (p:Problem {
            id: $problem_id,
            statement: $statement,
            impact_metric: $impact_metric,
            pain_level: $pain_level,
            frequency: $frequency,
            confidence: $confidence,
            created_at: datetime(),
            updated_at: datetime(),
            stage: 'mvp',
            status: 'ideated'
        })
        CREATE (i)-[:CONTAINS]->(p)
        RETURN p.id as id
        """
        
        result = session.run(query, {
            "idea_id": idea_id,
            "problem_id": problem_id,
            **problem_data
        })
        return result.single()["id"]
    
    def _create_icp(self, session: Session, idea_id: str, icp_data: Dict) -> str:
        """Create ICP node linked to idea."""
        icp_id = str(uuid4())
        
        query = """
        MATCH (i:Idea {id: $idea_id})
        CREATE (icp:ICP {
            id: $icp_id,
            segment: $segment,
            size: $size,
            pains: $pains,
            gains: $gains,
            wtp: $wtp,
            confidence: $confidence,
            created_at: datetime(),
            updated_at: datetime(),
            stage: 'mvp',
            status: 'ideated'
        })
        CREATE (i)-[:TARGETS]->(icp)
        RETURN icp.id as id
        """
        
        result = session.run(query, {
            "idea_id": idea_id,
            "icp_id": icp_id,
            **icp_data
        })
        return result.single()["id"]
    
    def _create_assumption(self, session: Session, idea_id: str, assumption_data: Dict) -> str:
        """Create assumption node linked to idea."""
        assumption_id = str(uuid4())
        
        query = """
        MATCH (i:Idea {id: $idea_id})
        CREATE (a:Assumption {
            id: $assumption_id,
            statement: $statement,
            type: $type,
            criticality: $criticality,
            confidence: $confidence,
            validation_method: $validation_method,
            created_at: datetime(),
            updated_at: datetime(),
            stage: 'mvp',
            status: 'ideated'
        })
        CREATE (i)-[:MAKES]->(a)
        RETURN a.id as id
        """
        
        result = session.run(query, {
            "idea_id": idea_id,
            "assumption_id": assumption_id,
            **assumption_data
        })
        return result.single()["id"]
    
    def _create_constraint(self, session: Session, idea_id: str, constraint_data: Dict) -> str:
        """Create constraint node linked to idea."""
        constraint_id = str(uuid4())
        
        query = """
        MATCH (i:Idea {id: $idea_id})
        CREATE (c:Constraint {
            id: $constraint_id,
            type: $type,
            description: $description,
            impact: $impact,
            mitigation: $mitigation,
            confidence: $confidence,
            created_at: datetime(),
            updated_at: datetime(),
            stage: 'mvp',
            status: 'ideated'
        })
        CREATE (i)-[:BOUNDED_BY]->(c)
        RETURN c.id as id
        """
        
        result = session.run(query, {
            "idea_id": idea_id,
            "constraint_id": constraint_id,
            **constraint_data
        })
        return result.single()["id"]
    
    def _create_outcome(self, session: Session, idea_id: str, outcome_data: Dict) -> str:
        """Create outcome node linked to idea."""
        outcome_id = str(uuid4())
        
        query = """
        MATCH (i:Idea {id: $idea_id})
        CREATE (o:Outcome {
            id: $outcome_id,
            description: $description,
            metric: $metric,
            target: $target,
            timeline: $timeline,
            confidence: $confidence,
            created_at: datetime(),
            updated_at: datetime(),
            stage: 'mvp',
            status: 'ideated'
        })
        CREATE (i)-[:AIMS_FOR]->(o)
        RETURN o.id as id
        """
        
        result = session.run(query, {
            "idea_id": idea_id,
            "outcome_id": outcome_id,
            **outcome_data
        })
        return result.single()["id"]

    # ============= Research Data Integration =============
    
    def add_research_evidence(
        self, 
        idea_id: str, 
        evidence_data: List[Dict[str, Any]]
    ) -> None:
        """Add research evidence and link to relevant entities."""
        
        with self.driver.session(database=self.config.database) as session:
            for evidence in evidence_data:
                evidence_id = str(uuid4())
                
                # Create evidence node
                query = """
                CREATE (e:Evidence {
                    id: $evidence_id,
                    source: $source,
                    type: $type,
                    content: $content,
                    credibility: $credibility,
                    relevance: $relevance,
                    url: $url,
                    created_at: datetime(),
                    updated_at: datetime()
                })
                """
                
                session.run(query, {
                    "evidence_id": evidence_id,
                    **evidence
                })
                
                # Link to entities based on tags
                self._link_evidence_to_entities(session, evidence_id, evidence.get("entity_tags", []))
    
    def add_competitors(
        self, 
        idea_id: str, 
        competitors: List[Dict[str, Any]]
    ) -> None:
        """Add competitor analysis data."""
        
        with self.driver.session(database=self.config.database) as session:
            for competitor_data in competitors:
                competitor_id = str(uuid4())
                
                query = """
                MATCH (i:Idea {id: $idea_id})
                CREATE (c:Competitor {
                    id: $competitor_id,
                    name: $name,
                    description: $description,
                    positioning: $positioning,
                    strengths: $strengths,
                    weaknesses: $weaknesses,
                    market_share: $market_share,
                    pricing: $pricing,
                    url: $url,
                    created_at: datetime(),
                    updated_at: datetime()
                })
                CREATE (i)-[:COMPETES_WITH]->(c)
                """
                
                session.run(query, {
                    "idea_id": idea_id,
                    "competitor_id": competitor_id,
                    **competitor_data
                })
    
    def _link_evidence_to_entities(
        self, 
        session: Session, 
        evidence_id: str, 
        entity_tags: List[str]
    ) -> None:
        """Link evidence to relevant entities based on tags."""
        
        for tag in entity_tags:
            # Link to problems
            query = """
            MATCH (e:Evidence {id: $evidence_id})
            MATCH (p:Problem) 
            WHERE p.statement CONTAINS $tag OR p.id = $tag
            CREATE (e)-[:SUPPORTS]->(p)
            """
            session.run(query, {"evidence_id": evidence_id, "tag": tag})
            
            # Link to ICPs
            query = """
            MATCH (e:Evidence {id: $evidence_id})
            MATCH (icp:ICP) 
            WHERE icp.segment CONTAINS $tag OR icp.id = $tag
            CREATE (e)-[:VALIDATES]->(icp)
            """
            session.run(query, {"evidence_id": evidence_id, "tag": tag})

    # ============= Requirements & Architecture Integration =============
    
    def create_requirements_from_problems(self, idea_id: str) -> List[str]:
        """Generate requirement nodes from validated problems."""
        
        query = """
        MATCH (i:Idea {id: $idea_id})-[:CONTAINS]->(p:Problem)
        WHERE p.status = 'validated'
        RETURN p.id as problem_id, p.statement as statement, 
               p.impact_metric as metric, p.confidence as confidence
        """
        
        requirement_ids = []
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, {"idea_id": idea_id})
            
            for record in result:
                req_id = f"REQ-{len(requirement_ids) + 1:03d}"
                requirement_ids.append(req_id)
                
                # Create requirement node
                req_query = """
                MATCH (p:Problem {id: $problem_id})
                CREATE (r:Requirement {
                    id: $req_id,
                    description: $description,
                    type: 'FR',
                    priority: 'M',
                    acceptance_criteria: $acceptance_criteria,
                    confidence: $confidence,
                    created_at: datetime(),
                    updated_at: datetime(),
                    stage: 'mvp',
                    status: 'defined'
                })
                CREATE (r)-[:DERIVES_FROM]->(p)
                RETURN r.id as id
                """
                
                session.run(req_query, {
                    "problem_id": record["problem_id"],
                    "req_id": req_id,
                    "description": f"System shall {record['statement']}",
                    "acceptance_criteria": f"When implemented, {record['metric']}",
                    "confidence": record["confidence"]
                })
        
        return requirement_ids
    
    def link_components_to_requirements(
        self, 
        component_mapping: Dict[str, List[str]]
    ) -> None:
        """Link architectural components to requirements."""
        
        with self.driver.session(database=self.config.database) as session:
            for component_id, req_ids in component_mapping.items():
                for req_id in req_ids:
                    query = """
                    MATCH (r:Requirement {id: $req_id})
                    MERGE (c:Component {
                        id: $component_id,
                        name: $component_name,
                        created_at: datetime(),
                        updated_at: datetime(),
                        stage: 'mvp',
                        status: 'designed'
                    })
                    CREATE (c)-[:IMPLEMENTS]->(r)
                    """
                    
                    session.run(query, {
                        "req_id": req_id,
                        "component_id": component_id,
                        "component_name": component_id.replace("-", " ").title()
                    })

    # ============= Code Artifact Graph =============
    
    def sync_code_artifacts(
        self, 
        artifacts: List[Dict[str, Any]]
    ) -> None:
        """Sync code artifacts (services, modules, classes, functions) to graph."""
        
        with self.driver.session(database=self.config.database) as session:
            for artifact in artifacts:
                self._create_code_artifact(session, artifact)
    
    def _create_code_artifact(
        self, 
        session: Session, 
        artifact: Dict[str, Any]
    ) -> str:
        """Create code artifact node with provenance links."""
        
        artifact_type = artifact["type"]  # Service, Module, Class, Function
        artifact_id = artifact["id"]
        
        # Create the artifact node
        query = f"""
        MERGE (a:{artifact_type} {{
            id: $id,
            name: $name,
            file_path: $file_path,
            implements: $implements,
            verified_by: $verified_by,
            complexity: $complexity,
            lines_of_code: $loc,
            created_at: datetime(),
            updated_at: datetime(),
            stage: $stage,
            status: $status
        }})
        RETURN a.id as id
        """
        
        session.run(query, {
            "id": artifact_id,
            "name": artifact["name"],
            "file_path": artifact.get("file_path", ""),
            "implements": artifact.get("implements", []),
            "verified_by": artifact.get("verified_by", []),
            "complexity": artifact.get("complexity", 0),
            "loc": artifact.get("lines_of_code", 0),
            "stage": artifact.get("stage", "mvp"),
            "status": artifact.get("status", "implemented")
        })
        
        # Create implementation links
        for req_id in artifact.get("implements", []):
            link_query = """
            MATCH (a {id: $artifact_id})
            MATCH (r:Requirement {id: $req_id})
            MERGE (a)-[:IMPLEMENTS]->(r)
            """
            session.run(link_query, {
                "artifact_id": artifact_id,
                "req_id": req_id
            })
        
        # Create hierarchy links (Service -> Module -> Class -> Function)
        if artifact.get("parent_id"):
            parent_query = """
            MATCH (a {id: $artifact_id})
            MATCH (p {id: $parent_id})
            MERGE (p)-[:CONTAINS]->(a)
            """
            session.run(parent_query, {
                "artifact_id": artifact_id,
                "parent_id": artifact["parent_id"]
            })
        
        return artifact_id

    # ============= Traceability & Provenance Queries =============
    
    def generate_traceability_matrix(self) -> List[Dict[str, Any]]:
        """Generate complete traceability matrix: REQ -> Code -> Tests -> Coverage."""
        
        query = """
        MATCH (r:Requirement)
        OPTIONAL MATCH (r)<-[:IMPLEMENTS]-(code)
        OPTIONAL MATCH (code)<-[:VERIFIES]-(test:Test)
        OPTIONAL MATCH (r)<-[:COVERS]-(e2e:E2ETest)
        WITH r, 
             collect(DISTINCT code.name) as implementing_code,
             collect(DISTINCT test.id) as unit_tests,
             collect(DISTINCT e2e.id) as e2e_tests,
             CASE WHEN size(collect(DISTINCT code)) > 0 AND size(collect(DISTINCT test)) > 0 
                  THEN 'GREEN' 
                  WHEN size(collect(DISTINCT code)) > 0 
                  THEN 'YELLOW'
                  ELSE 'RED' END as status
        RETURN {
            req_id: r.id,
            description: r.description,
            implementing_code: implementing_code,
            unit_tests: unit_tests,
            e2e_tests: e2e_tests,
            coverage: CASE WHEN size(unit_tests) > 0 THEN 0.85 ELSE 0.0 END,
            status: status,
            updated_at: r.updated_at
        } as matrix_row
        ORDER BY r.id
        """
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query)
            return [record["matrix_row"] for record in result]
    
    def find_orphan_code(self) -> List[Dict[str, Any]]:
        """Find code artifacts not linked to any requirement."""
        
        query = """
        MATCH (code)
        WHERE code:Service OR code:Module OR code:Class OR code:Function
        AND NOT (code)-[:IMPLEMENTS]->(:Requirement)
        RETURN {
            type: labels(code)[0],
            id: code.id,
            name: code.name,
            file_path: code.file_path
        } as orphan
        """
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query)
            return [record["orphan"] for record in result]
    
    def find_orphan_requirements(self) -> List[Dict[str, Any]]:
        """Find requirements without implementing code."""
        
        query = """
        MATCH (r:Requirement)
        WHERE NOT (r)<-[:IMPLEMENTS]-()
        RETURN {
            req_id: r.id,
            description: r.description,
            priority: r.priority,
            stage: r.stage
        } as orphan
        """
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query)
            return [record["orphan"] for record in result]
    
    def calculate_change_impact(
        self, 
        changed_artifacts: List[str]
    ) -> Dict[str, List[str]]:
        """Calculate upstream and downstream impact of code changes."""
        
        impact = {
            "upstream_requirements": [],
            "upstream_problems": [],
            "downstream_tests": [],
            "downstream_services": []
        }
        
        with self.driver.session(database=self.config.database) as session:
            for artifact_id in changed_artifacts:
                # Find upstream requirements
                upstream_query = """
                MATCH (a {id: $artifact_id})-[:IMPLEMENTS]->(r:Requirement)
                RETURN collect(r.id) as requirements
                """
                result = session.run(upstream_query, {"artifact_id": artifact_id})
                impact["upstream_requirements"].extend(
                    result.single()["requirements"]
                )
                
                # Find downstream tests
                downstream_query = """
                MATCH (a {id: $artifact_id})<-[:VERIFIES]-(t:Test)
                RETURN collect(t.id) as tests
                """
                result = session.run(downstream_query, {"artifact_id": artifact_id})
                impact["downstream_tests"].extend(
                    result.single()["tests"]
                )
        
        return impact

    # ============= Graph Visualization Data =============
    
    def get_idea_graph_data(self, idea_id: str) -> Dict[str, Any]:
        """Get complete idea graph data for visualization."""
        
        query = """
        MATCH (i:Idea {id: $idea_id})
        OPTIONAL MATCH (i)-[r1:CONTAINS]->(p:Problem)
        OPTIONAL MATCH (i)-[r2:TARGETS]->(icp:ICP)
        OPTIONAL MATCH (i)-[r3:MAKES]->(a:Assumption)
        OPTIONAL MATCH (i)-[r4:BOUNDED_BY]->(c:Constraint)
        OPTIONAL MATCH (i)-[r5:AIMS_FOR]->(o:Outcome)
        OPTIONAL MATCH (i)-[r6:COMPETES_WITH]->(comp:Competitor)
        
        RETURN {
            idea: i,
            problems: collect(DISTINCT p),
            icps: collect(DISTINCT icp),
            assumptions: collect(DISTINCT a),
            constraints: collect(DISTINCT c),
            outcomes: collect(DISTINCT o),
            competitors: collect(DISTINCT comp)
        } as graph_data
        """
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, {"idea_id": idea_id})
            return result.single()["graph_data"]
    
    def get_provenance_chain(
        self, 
        function_id: str
    ) -> List[Dict[str, Any]]:
        """Get complete provenance chain from function back to original idea."""
        
        query = """
        MATCH (f:Function {id: $function_id})
        MATCH path = (f)-[:IMPLEMENTS]->(r:Requirement)-[:DERIVES_FROM]->(p:Problem)<-[:CONTAINS]-(i:Idea)
        RETURN [
            {type: 'Function', data: f},
            {type: 'Requirement', data: r},
            {type: 'Problem', data: p},
            {type: 'Idea', data: i}
        ] as provenance_chain
        """
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, {"function_id": function_id})
            record = result.single()
            return record["provenance_chain"] if record else []
