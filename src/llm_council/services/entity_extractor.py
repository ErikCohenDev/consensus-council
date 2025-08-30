"""Entity extraction and relationship mapping for idea context graphs."""

from __future__ import annotations
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..orchestrator import AuditorWorker
from ..observability.phoenix_tracer import get_phoenix_tracer


@dataclass
class Entity:
    """Represents an entity extracted from idea text."""
    id: str
    label: str
    type: str  # "core_idea", "feature", "user_group", "problem", "solution", "risk", "dependency"
    description: str
    importance: float  # 0.0-1.0
    certainty: float   # 0.0-1.0 (how confident we are this entity exists)


@dataclass
class Relationship:
    """Represents a relationship between entities."""
    id: str
    source_id: str
    target_id: str
    type: str  # "enables", "requires", "conflicts", "contains", "targets", "solves"
    label: str
    strength: float  # 0.0-1.0
    description: str


@dataclass
class ContextGraph:
    """Complete context graph with entities and relationships."""
    entities: List[Entity]
    relationships: List[Relationship]
    central_entity_id: str
    confidence_score: float


class EntityExtractor:
    """Extracts entities and relationships from idea descriptions."""
    
    def __init__(self, worker: AuditorWorker):
        self.worker = worker
        self.tracer = get_phoenix_tracer()
    
    async def extract_context_graph(self, idea_text: str, 
                                  additional_context: str = "") -> ContextGraph:
        """Extract a complete context graph from idea text."""
        
        with self.tracer.trace_audit_run(
            audit_id="entity_extraction",
            project_id="context_graph", 
            stage="entity_extraction",
            model=self.worker.model,
            docs_path="idea_input"
        ) as span:
            prompt = self._create_extraction_prompt(idea_text, additional_context)
            
            try:
                result = await self.worker.execute_audit(prompt)
                
                # Parse the structured response
                if isinstance(result, str):
                    result = json.loads(result)
                
                entities = [
                    Entity(
                        id=e["id"],
                        label=e["label"], 
                        type=e.get("type", "concept"),
                        description=e.get("description", ""),
                        importance=float(e.get("importance", 0.5)),
                        certainty=float(e.get("certainty", 0.7))
                    )
                    for e in result.get("entities", [])
                ]
                
                relationships = [
                    Relationship(
                        id=r["id"],
                        source_id=r["source"], 
                        target_id=r["target"],
                        type=r.get("type", "relates_to"),
                        label=r.get("label", ""),
                        strength=float(r.get("strength", 0.5)),
                        description=r.get("description", "")
                    )
                    for r in result.get("relationships", [])
                ]
                
                # Find central entity (highest importance)
                central_id = max(entities, key=lambda e: e.importance).id if entities else ""
                
                # Calculate overall confidence
                confidence = sum(e.certainty * e.importance for e in entities) / len(entities) if entities else 0.0
                
                graph = ContextGraph(
                    entities=entities,
                    relationships=relationships, 
                    central_entity_id=central_id,
                    confidence_score=confidence
                )
                
                if span:
                    span.set_attribute("entities.count", len(entities))
                    span.set_attribute("relationships.count", len(relationships))
                    span.set_attribute("graph.confidence", confidence)
                    span.set_attribute("graph.central_entity", central_id)
                
                return graph
                
            except Exception as e:
                if span:
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                raise
    
    def _create_extraction_prompt(self, idea_text: str, context: str = "") -> str:
        """Create prompt for entity and relationship extraction."""
        additional_context = f"## Additional Context:\n{context}" if context.strip() else ""
        
        return f"""
You are an expert in business analysis and knowledge graphs. Analyze the following idea and extract:

1. **Entities**: Key concepts, features, user groups, problems, solutions, risks, and dependencies
2. **Relationships**: How these entities connect, depend on, enable, or conflict with each other

Focus on creating a comprehensive context graph that helps visualize the idea's ecosystem.

## Output Format (JSON):
```json
{{
  "entities": [
    {{
      "id": "unique_snake_case_id",
      "label": "Human Readable Label", 
      "type": "core_idea|feature|user_group|problem|solution|risk|dependency|market|technology",
      "description": "Brief description of this entity",
      "importance": 0.9,  // 0.0-1.0, how central this is to the idea
      "certainty": 0.8    // 0.0-1.0, confidence this entity is relevant
    }}
  ],
  "relationships": [
    {{
      "id": "rel_1",
      "source": "entity_id_1",
      "target": "entity_id_2", 
      "type": "enables|requires|conflicts|contains|targets|solves|depends_on",
      "label": "Short relationship description",
      "strength": 0.7,    // 0.0-1.0, how strong this relationship is
      "description": "Detailed explanation of the relationship"
    }}
  ]
}}
```

## Guidelines:
- Create 8-15 entities (core concepts, not trivial details)
- Focus on business-relevant entities (users, problems, solutions, markets, technologies)
- Identify the main idea as the central entity with highest importance (0.9-1.0)
- Create meaningful relationships that show dependencies, conflicts, and enablement
- Use descriptive relationship types that explain the connection

## Idea to Analyze:
{idea_text}

{additional_context}

Return only the JSON object, no additional text.
"""

    def to_reactflow_format(self, graph: ContextGraph) -> Dict[str, Any]:
        """Convert ContextGraph to ReactFlow nodes and edges format."""
        
        # Create nodes with positioning
        nodes = []
        for i, entity in enumerate(graph.entities):
            # Simple circular layout
            import math
            angle = 2 * math.pi * i / len(graph.entities)
            radius = 200 if entity.id != graph.central_entity_id else 0
            
            node = {
                "id": entity.id,
                "data": {
                    "label": entity.label,
                    "description": entity.description,
                    "type": entity.type,
                    "importance": entity.importance,
                    "certainty": entity.certainty
                },
                "position": {
                    "x": 400 + radius * math.cos(angle),
                    "y": 300 + radius * math.sin(angle)
                },
                "type": "custom" if entity.id == graph.central_entity_id else "default",
                "style": {
                    "background": "#3b82f6" if entity.id == graph.central_entity_id else "#e5e7eb",
                    "color": "white" if entity.id == graph.central_entity_id else "#374151",
                    "border": f"2px solid {'#1d4ed8' if entity.id == graph.central_entity_id else '#9ca3af'}",
                    "borderRadius": "8px",
                    "padding": "8px"
                }
            }
            nodes.append(node)
        
        # Create edges
        edges = []
        for rel in graph.relationships:
            edge = {
                "id": rel.id,
                "source": rel.source_id,
                "target": rel.target_id,
                "label": rel.label,
                "type": "smoothstep",
                "data": {
                    "relationship_type": rel.type,
                    "description": rel.description,
                    "strength": rel.strength
                },
                "style": {
                    "strokeWidth": max(1, rel.strength * 3),
                    "stroke": "#6b7280"
                },
                "labelStyle": {
                    "fontSize": "12px",
                    "fill": "#374151"
                }
            }
            edges.append(edge)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "central_entity": graph.central_entity_id,
            "confidence": graph.confidence_score
        }