"""Research expansion service for adding context to ideas and entities."""

from __future__ import annotations
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .entity_extractor import ContextGraph, Entity, Relationship
from ..orchestrator import AuditorWorker
from ..research_agent import ResearchAgent
from ..observability.phoenix_tracer import get_phoenix_tracer


@dataclass
class ResearchInsight:
    """Research insight that can expand context."""
    entity_id: str
    insight_type: str  # "market_data", "competitor", "technology", "risk", "opportunity"
    title: str
    content: str
    sources: List[str]
    relevance_score: float  # 0.0-1.0


@dataclass
class ExpandedContext:
    """Context graph enhanced with research insights."""
    original_graph: ContextGraph
    insights: List[ResearchInsight]
    new_entities: List[Entity]
    new_relationships: List[Relationship]
    expansion_confidence: float


class ResearchExpander:
    """Expands context graphs with targeted research and insights."""
    
    def __init__(self, auditor_worker: AuditorWorker, research_agent: ResearchAgent):
        self.auditor_worker = auditor_worker
        self.research_agent = research_agent
        self.tracer = get_phoenix_tracer()
    
    async def expand_context(self, graph: ContextGraph, 
                           focus_areas: Optional[List[str]] = None) -> ExpandedContext:
        """Expand context graph with targeted research."""
        
        with self.tracer.trace_audit_run(
            audit_id="context_expansion",
            project_id="research_expansion",
            stage="research",
            model=self.auditor_worker.model,
            docs_path="context_graph"
        ) as span:
            
            # Identify research targets
            research_targets = self._identify_research_targets(graph, focus_areas)
            
            if span:
                span.set_attribute("research.targets_count", len(research_targets))
                span.set_attribute("research.focus_areas", ",".join(focus_areas or []))
            
            # Conduct research for each target
            insights = []
            for target in research_targets:
                target_insights = await self._research_entity(target, graph)
                insights.extend(target_insights)
            
            # Generate new entities and relationships from insights
            new_entities, new_relationships = await self._extract_new_elements(insights, graph)
            
            # Calculate expansion confidence
            confidence = self._calculate_expansion_confidence(insights, new_entities)
            
            if span:
                span.set_attribute("insights.count", len(insights))
                span.set_attribute("new_entities.count", len(new_entities))
                span.set_attribute("new_relationships.count", len(new_relationships))
                span.set_attribute("expansion.confidence", confidence)
            
            return ExpandedContext(
                original_graph=graph,
                insights=insights,
                new_entities=new_entities,
                new_relationships=new_relationships,
                expansion_confidence=confidence
            )
    
    def _identify_research_targets(self, graph: ContextGraph, 
                                 focus_areas: Optional[List[str]]) -> List[Entity]:
        """Identify which entities need research expansion."""
        targets = []
        
        # Focus on high-importance, low-certainty entities
        for entity in graph.entities:
            if entity.importance > 0.6 and entity.certainty < 0.8:
                targets.append(entity)
        
        # Add central entity if not already included
        central = next((e for e in graph.entities if e.id == graph.central_entity_id), None)
        if central and central not in targets:
            targets.append(central)
        
        # Filter by focus areas if specified
        if focus_areas:
            targets = [t for t in targets if any(area.lower() in t.type.lower() or 
                      area.lower() in t.label.lower() for area in focus_areas)]
        
        return targets[:5]  # Limit to top 5 for cost control
    
    async def _research_entity(self, entity: Entity, graph: ContextGraph) -> List[ResearchInsight]:
        """Research a specific entity to gather insights."""
        
        # Create research queries based on entity type
        queries = self._generate_research_queries(entity)
        
        insights = []
        for query in queries:
            try:
                # Use research agent to gather information
                search_results = await self.research_agent.search_and_synthesize(
                    query, max_results=3
                )
                
                if search_results:
                    insight = ResearchInsight(
                        entity_id=entity.id,
                        insight_type=self._classify_insight_type(query, entity.type),
                        title=f"Research: {entity.label}",
                        content=search_results,
                        sources=[],  # Research agent should provide sources
                        relevance_score=0.8  # Could be calculated based on content quality
                    )
                    insights.append(insight)
                    
            except Exception as e:
                print(f"Research failed for {entity.label}: {e}")
                continue
        
        return insights
    
    def _generate_research_queries(self, entity: Entity) -> List[str]:
        """Generate targeted research queries based on entity type."""
        base_label = entity.label.lower()
        
        queries = []
        
        if entity.type == "core_idea":
            queries.extend([
                f"{base_label} market size and trends",
                f"{base_label} competitive landscape",
                f"{base_label} technology requirements"
            ])
        elif entity.type == "user_group":
            queries.extend([
                f"{base_label} demographics and behavior",
                f"{base_label} pain points and needs",
                f"{base_label} market research"
            ])
        elif entity.type == "problem":
            queries.extend([
                f"{base_label} existing solutions",
                f"{base_label} market demand",
                f"{base_label} cost of problem"
            ])
        elif entity.type == "technology":
            queries.extend([
                f"{base_label} implementation complexity",
                f"{base_label} alternatives and vendors",
                f"{base_label} scalability considerations"
            ])
        elif entity.type == "risk":
            queries.extend([
                f"{base_label} mitigation strategies",
                f"{base_label} industry examples",
                f"{base_label} probability and impact"
            ])
        else:
            # Generic research for other entity types
            queries.append(f"{base_label} market analysis and trends")
        
        return queries[:2]  # Limit queries per entity
    
    def _classify_insight_type(self, query: str, entity_type: str) -> str:
        """Classify the type of insight based on query and entity."""
        query_lower = query.lower()
        
        if "market" in query_lower or "size" in query_lower:
            return "market_data"
        elif "competitor" in query_lower or "alternative" in query_lower:
            return "competitor"
        elif "technology" in query_lower or "implementation" in query_lower:
            return "technology"
        elif "risk" in query_lower or "mitigation" in query_lower:
            return "risk"
        else:
            return "opportunity"
    
    async def _extract_new_elements(self, insights: List[ResearchInsight], 
                                  original_graph: ContextGraph) -> tuple[List[Entity], List[Relationship]]:
        """Extract new entities and relationships from research insights."""
        
        # Combine all insight content for analysis
        combined_insights = "\n\n".join([
            f"Entity: {insight.entity_id}\nType: {insight.insight_type}\n{insight.content}"
            for insight in insights
        ])
        
        prompt = f"""
Based on the research insights below, identify NEW entities and relationships that should be added to expand the context graph.

Current entities: {[e.label for e in original_graph.entities]}

Research insights:
{combined_insights}

Return JSON with:
- "new_entities": List of entities not already in the graph
- "new_relationships": List of relationships involving new or existing entities

Use the same format as the original entity extraction.
"""
        
        try:
            result = await self.auditor_worker.execute_audit(prompt)
            if isinstance(result, str):
                result = json.loads(result)
            
            new_entities = [
                Entity(
                    id=e["id"],
                    label=e["label"],
                    type=e.get("type", "concept"), 
                    description=e.get("description", ""),
                    importance=float(e.get("importance", 0.4)),
                    certainty=float(e.get("certainty", 0.9))  # High certainty from research
                )
                for e in result.get("new_entities", [])
            ]
            
            new_relationships = [
                Relationship(
                    id=r["id"],
                    source_id=r["source"],
                    target_id=r["target"],
                    type=r.get("type", "relates_to"),
                    label=r.get("label", ""),
                    strength=float(r.get("strength", 0.6)),
                    description=r.get("description", "")
                )
                for r in result.get("new_relationships", [])
            ]
            
            return new_entities, new_relationships
            
        except Exception as e:
            print(f"Failed to extract new elements: {e}")
            return [], []
    
    def _calculate_expansion_confidence(self, insights: List[ResearchInsight], 
                                      new_entities: List[Entity]) -> float:
        """Calculate confidence in the context expansion."""
        if not insights:
            return 0.0
        
        # Base confidence on insight relevance and quantity
        avg_relevance = sum(i.relevance_score for i in insights) / len(insights)
        
        # Boost confidence if we found new entities
        entity_bonus = min(0.2, len(new_entities) * 0.05)
        
        return min(1.0, avg_relevance + entity_bonus)