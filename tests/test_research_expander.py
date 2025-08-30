"""Tests for research expansion service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import json

from llm_council.services.research_expander import ResearchExpander, ResearchInsight, ExpandedContext
from llm_council.services.entity_extractor import Entity, Relationship, ContextGraph
from llm_council.orchestrator import AuditorWorker
from llm_council.research_agent import ResearchAgent


class TestResearchExpansion:
    """Test research expansion functionality."""
    
    def test_research_insight_creation(self):
        """Test ResearchInsight dataclass creation."""
        insight = ResearchInsight(
            entity_id="test_entity",
            insight_type="market_data",
            title="Market Analysis",
            content="Market shows strong demand",
            sources=["source1.com", "source2.com"],
            relevance_score=0.8
        )
        
        assert insight.entity_id == "test_entity"
        assert insight.insight_type == "market_data"
        assert insight.title == "Market Analysis"
        assert len(insight.sources) == 2
        assert insight.relevance_score == 0.8

    def test_expanded_context_creation(self):
        """Test ExpandedContext dataclass creation."""
        original_graph = ContextGraph([], [], "", 0.5)
        insights = [ResearchInsight("e1", "market_data", "Test", "Content", [], 0.7)]
        new_entities = [Entity("e2", "New Entity", "market", "New", 0.6, 0.8)]
        new_relationships = [Relationship("r1", "e1", "e2", "relates_to", "relates", 0.5, "Test")]
        
        expanded = ExpandedContext(
            original_graph=original_graph,
            insights=insights,
            new_entities=new_entities, 
            new_relationships=new_relationships,
            expansion_confidence=0.75
        )
        
        assert expanded.original_graph == original_graph
        assert len(expanded.insights) == 1
        assert len(expanded.new_entities) == 1
        assert len(expanded.new_relationships) == 1
        assert expanded.expansion_confidence == 0.75

    def test_identify_research_targets(self):
        """Test research target identification logic."""
        entities = [
            Entity("e1", "High Importance Low Certainty", "core_idea", "Test", 0.8, 0.5),  # Should be selected
            Entity("e2", "Low Importance High Certainty", "feature", "Test", 0.3, 0.9),   # Should NOT be selected
            Entity("e3", "Central Entity", "core_idea", "Test", 0.9, 0.6),                # Should be selected (central)
            Entity("e4", "High Both", "user_group", "Test", 0.9, 0.9),                   # Should NOT be selected
        ]
        
        graph = ContextGraph(entities, [], "e3", 0.7)
        
        mock_worker = MagicMock()
        mock_research_agent = MagicMock()
        expander = ResearchExpander(mock_worker, mock_research_agent)
        
        targets = expander._identify_research_targets(graph, None)
        
        # Should include high importance/low certainty (e1) and central entity (e3)
        target_ids = [t.id for t in targets]
        assert "e1" in target_ids
        assert "e3" in target_ids
        assert "e2" not in target_ids
        assert "e4" not in target_ids

    def test_identify_research_targets_with_focus(self):
        """Test research target identification with focus areas."""
        entities = [
            Entity("e1", "User Research", "user_group", "Test", 0.8, 0.5),
            Entity("e2", "Market Analysis", "market", "Test", 0.7, 0.4),
            Entity("e3", "Technology Stack", "technology", "Test", 0.9, 0.3)
        ]
        
        graph = ContextGraph(entities, [], "e1", 0.7)
        
        mock_worker = MagicMock()
        mock_research_agent = MagicMock()
        expander = ResearchExpander(mock_worker, mock_research_agent)
        
        # Focus on user-related entities
        targets = expander._identify_research_targets(graph, ["user", "market"])
        
        target_ids = [t.id for t in targets]
        assert "e1" in target_ids  # Contains "user"
        assert "e2" in target_ids  # Contains "market"
        assert "e3" not in target_ids  # Technology not in focus

    def test_generate_research_queries_core_idea(self):
        """Test query generation for core idea entities."""
        entity = Entity("idea1", "AI Fitness App", "core_idea", "Test", 0.9, 0.7)
        
        mock_worker = MagicMock()
        mock_research_agent = MagicMock()
        expander = ResearchExpander(mock_worker, mock_research_agent)
        
        queries = expander._generate_research_queries(entity)
        
        assert len(queries) == 2  # Limited to 2 queries
        assert any("market size" in q.lower() for q in queries)
        assert any("competitive" in q.lower() for q in queries)

    def test_generate_research_queries_user_group(self):
        """Test query generation for user group entities."""
        entity = Entity("users1", "Fitness Enthusiasts", "user_group", "Test", 0.8, 0.6)
        
        mock_worker = MagicMock()
        mock_research_agent = MagicMock()
        expander = ResearchExpander(mock_worker, mock_research_agent)
        
        queries = expander._generate_research_queries(entity)
        
        assert len(queries) == 2
        assert any("demographics" in q.lower() for q in queries)
        assert any("pain points" in q.lower() for q in queries)

    def test_classify_insight_type(self):
        """Test insight type classification."""
        mock_worker = MagicMock()
        mock_research_agent = MagicMock()
        expander = ResearchExpander(mock_worker, mock_research_agent)
        
        assert expander._classify_insight_type("market size analysis", "core_idea") == "market_data"
        assert expander._classify_insight_type("competitor research", "core_idea") == "competitor"
        assert expander._classify_insight_type("technology implementation", "technology") == "technology"
        assert expander._classify_insight_type("risk mitigation", "risk") == "risk"
        assert expander._classify_insight_type("business opportunity", "market") == "opportunity"

    def test_calculate_expansion_confidence_no_insights(self):
        """Test confidence calculation with no insights."""
        mock_worker = MagicMock()
        mock_research_agent = MagicMock()
        expander = ResearchExpander(mock_worker, mock_research_agent)
        
        confidence = expander._calculate_expansion_confidence([], [])
        assert confidence == 0.0

    def test_calculate_expansion_confidence_with_data(self):
        """Test confidence calculation with insights and new entities."""
        insights = [
            ResearchInsight("e1", "market_data", "Test", "Content", [], 0.8),
            ResearchInsight("e2", "competitor", "Test", "Content", [], 0.9)
        ]
        new_entities = [
            Entity("e3", "New Entity", "market", "Test", 0.7, 0.8),
            Entity("e4", "Another Entity", "competitor", "Test", 0.6, 0.9)
        ]
        
        mock_worker = MagicMock()
        mock_research_agent = MagicMock()
        expander = ResearchExpander(mock_worker, mock_research_agent)
        
        confidence = expander._calculate_expansion_confidence(insights, new_entities)
        
        # Should be average relevance (0.85) + entity bonus (0.1) = 0.95
        assert abs(confidence - 0.95) < 0.001  # Account for floating point precision

    @pytest.mark.asyncio
    async def test_research_entity_success(self):
        """Test successful entity research."""
        entity = Entity("test", "Test Entity", "core_idea", "Test", 0.8, 0.6)
        graph = ContextGraph([entity], [], "test", 0.7)
        
        mock_worker = MagicMock()
        mock_research_agent = AsyncMock()
        mock_research_agent.search_and_synthesize.return_value = "Market research results"
        
        expander = ResearchExpander(mock_worker, mock_research_agent)
        insights = await expander._research_entity(entity, graph)
        
        assert len(insights) > 0
        assert all(i.entity_id == "test" for i in insights)
        assert all(i.content == "Market research results" for i in insights)

    @pytest.mark.asyncio  
    async def test_research_entity_failure_handling(self):
        """Test research entity with agent failure."""
        entity = Entity("test", "Test Entity", "core_idea", "Test", 0.8, 0.6)
        graph = ContextGraph([entity], [], "test", 0.7)
        
        mock_worker = MagicMock()
        mock_research_agent = AsyncMock()
        mock_research_agent.search_and_synthesize.side_effect = Exception("API Error")
        
        expander = ResearchExpander(mock_worker, mock_research_agent)
        insights = await expander._research_entity(entity, graph)
        
        # Should handle failure gracefully
        assert insights == []

    @pytest.mark.asyncio
    async def test_extract_new_elements_success(self):
        """Test extraction of new elements from insights."""
        insights = [
            ResearchInsight("e1", "market_data", "Market Analysis", "Strong market demand", [], 0.8)
        ]
        original_graph = ContextGraph([Entity("e1", "Original", "core_idea", "Test", 0.9, 0.8)], [], "e1", 0.7)
        
        mock_worker = AsyncMock()
        mock_worker.execute_audit.return_value = json.dumps({
            "new_entities": [
                {"id": "market_segment", "label": "Target Market", "type": "market", "description": "Primary market segment", "importance": 0.7, "certainty": 0.9}
            ],
            "new_relationships": [
                {"id": "targets_market", "source": "e1", "target": "market_segment", "type": "targets", "label": "targets", "strength": 0.8, "description": "Targets market segment"}
            ]
        })
        
        mock_research_agent = MagicMock()
        expander = ResearchExpander(mock_worker, mock_research_agent)
        
        new_entities, new_relationships = await expander._extract_new_elements(insights, original_graph)
        
        assert len(new_entities) == 1
        assert len(new_relationships) == 1
        assert new_entities[0].id == "market_segment"
        assert new_relationships[0].source_id == "e1"

    @pytest.mark.asyncio
    async def test_extract_new_elements_failure_handling(self):
        """Test new element extraction with worker failure."""
        insights = [ResearchInsight("e1", "market_data", "Test", "Content", [], 0.8)]
        original_graph = ContextGraph([], [], "", 0.5)
        
        mock_worker = AsyncMock()
        mock_worker.execute_audit.side_effect = Exception("LLM Error")
        
        mock_research_agent = MagicMock()
        expander = ResearchExpander(mock_worker, mock_research_agent)
        
        new_entities, new_relationships = await expander._extract_new_elements(insights, original_graph)
        
        # Should handle failure gracefully
        assert new_entities == []
        assert new_relationships == []