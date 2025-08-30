"""Tests for idea processing models."""

import pytest
from pydantic import ValidationError

from llm_council.models.idea_models import (
    IdeaInput, EntityData, RelationshipData, ContextGraphData,
    ResearchExpansionRequest, ResearchInsightData, ExpandedContextData, ReactFlowGraph
)


class TestIdeaInput:
    """Test IdeaInput model validation."""
    
    def test_valid_idea_input(self):
        """Test valid idea input creation."""
        idea = IdeaInput(
            text="A mobile app that helps people track their daily water intake with personalized reminders",
            project_name="Water Tracker",
            focus_areas=["health", "mobile"]
        )
        
        assert idea.text.startswith("A mobile app")
        assert idea.project_name == "Water Tracker"
        assert idea.focus_areas == ["health", "mobile"]

    def test_idea_input_minimum_length(self):
        """Test idea input minimum length validation."""
        with pytest.raises(ValidationError, match="at least 10 characters"):
            IdeaInput(text="Too short")

    def test_idea_input_maximum_length(self):
        """Test idea input maximum length validation."""
        long_text = "x" * 2001
        with pytest.raises(ValidationError, match="at most 2000 characters"):
            IdeaInput(text=long_text)

    def test_idea_input_optional_fields(self):
        """Test idea input with optional fields."""
        idea = IdeaInput(text="A great idea for tracking daily habits")
        
        assert idea.project_name is None
        assert idea.focus_areas is None


class TestEntityData:
    """Test EntityData model validation."""
    
    def test_valid_entity_data(self):
        """Test valid entity data creation."""
        entity = EntityData(
            id="mobile_app",
            label="Water Tracking App",
            type="core_idea",
            description="Mobile application for water intake tracking",
            importance=0.9,
            certainty=0.8
        )
        
        assert entity.id == "mobile_app"
        assert entity.label == "Water Tracking App"
        assert entity.type == "core_idea"
        assert entity.importance == 0.9
        assert entity.certainty == 0.8

    def test_entity_importance_bounds(self):
        """Test entity importance bounds validation."""
        # Valid bounds
        EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=0.0, certainty=0.5)
        EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=1.0, certainty=0.5)
        
        # Invalid bounds
        with pytest.raises(ValidationError):
            EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=-0.1, certainty=0.5)
        with pytest.raises(ValidationError):
            EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=1.1, certainty=0.5)

    def test_entity_certainty_bounds(self):
        """Test entity certainty bounds validation."""
        # Valid bounds
        EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=0.5, certainty=0.0)
        EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=0.5, certainty=1.0)
        
        # Invalid bounds
        with pytest.raises(ValidationError):
            EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=0.5, certainty=-0.1)
        with pytest.raises(ValidationError):
            EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=0.5, certainty=1.1)


class TestRelationshipData:
    """Test RelationshipData model validation."""
    
    def test_valid_relationship_data(self):
        """Test valid relationship data creation."""
        relationship = RelationshipData(
            id="rel_1",
            source_id="entity_1",
            target_id="entity_2",
            type="enables",
            label="enables feature",
            strength=0.8,
            description="Entity 1 enables Entity 2"
        )
        
        assert relationship.id == "rel_1"
        assert relationship.source_id == "entity_1"
        assert relationship.target_id == "entity_2"
        assert relationship.type == "enables"
        assert relationship.strength == 0.8

    def test_relationship_strength_bounds(self):
        """Test relationship strength bounds validation."""
        # Valid bounds
        RelationshipData(id="r1", source_id="e1", target_id="e2", type="enables", label="test", strength=0.0, description="test")
        RelationshipData(id="r1", source_id="e1", target_id="e2", type="enables", label="test", strength=1.0, description="test")
        
        # Invalid bounds
        with pytest.raises(ValidationError):
            RelationshipData(id="r1", source_id="e1", target_id="e2", type="enables", label="test", strength=-0.1, description="test")
        with pytest.raises(ValidationError):
            RelationshipData(id="r1", source_id="e1", target_id="e2", type="enables", label="test", strength=1.1, description="test")


class TestContextGraphData:
    """Test ContextGraphData model validation."""
    
    def test_valid_context_graph_data(self):
        """Test valid context graph creation."""
        entities = [
            EntityData(id="e1", label="App", type="core_idea", description="Test", importance=0.9, certainty=0.8)
        ]
        relationships = [
            RelationshipData(id="r1", source_id="e1", target_id="e1", type="contains", label="self", strength=0.5, description="test")
        ]
        
        graph = ContextGraphData(
            entities=entities,
            relationships=relationships,
            central_entity_id="e1",
            confidence_score=0.75
        )
        
        assert len(graph.entities) == 1
        assert len(graph.relationships) == 1
        assert graph.central_entity_id == "e1"
        assert graph.confidence_score == 0.75

    def test_context_graph_confidence_bounds(self):
        """Test context graph confidence bounds validation."""
        entities = [EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=0.5, certainty=0.5)]
        
        # Valid bounds
        ContextGraphData(entities=entities, relationships=[], central_entity_id="e1", confidence_score=0.0)
        ContextGraphData(entities=entities, relationships=[], central_entity_id="e1", confidence_score=1.0)
        
        # Invalid bounds
        with pytest.raises(ValidationError):
            ContextGraphData(entities=entities, relationships=[], central_entity_id="e1", confidence_score=-0.1)
        with pytest.raises(ValidationError):
            ContextGraphData(entities=entities, relationships=[], central_entity_id="e1", confidence_score=1.1)


class TestResearchExpansionRequest:
    """Test ResearchExpansionRequest model validation."""
    
    def test_valid_research_expansion_request(self):
        """Test valid research expansion request."""
        entities = [EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=0.5, certainty=0.5)]
        graph = ContextGraphData(entities=entities, relationships=[], central_entity_id="e1", confidence_score=0.7)
        
        request = ResearchExpansionRequest(
            graph=graph,
            focus_areas=["market", "technology"],
            max_insights=15
        )
        
        assert request.graph == graph
        assert request.focus_areas == ["market", "technology"]
        assert request.max_insights == 15

    def test_research_expansion_max_insights_bounds(self):
        """Test max_insights bounds validation."""
        entities = [EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=0.5, certainty=0.5)]
        graph = ContextGraphData(entities=entities, relationships=[], central_entity_id="e1", confidence_score=0.7)
        
        # Valid bounds
        ResearchExpansionRequest(graph=graph, max_insights=1)
        ResearchExpansionRequest(graph=graph, max_insights=20)
        
        # Invalid bounds
        with pytest.raises(ValidationError):
            ResearchExpansionRequest(graph=graph, max_insights=0)
        with pytest.raises(ValidationError):
            ResearchExpansionRequest(graph=graph, max_insights=21)

    def test_research_expansion_defaults(self):
        """Test research expansion request defaults."""
        entities = [EntityData(id="e1", label="Test", type="core_idea", description="Test", importance=0.5, certainty=0.5)]
        graph = ContextGraphData(entities=entities, relationships=[], central_entity_id="e1", confidence_score=0.7)
        
        request = ResearchExpansionRequest(graph=graph)
        
        assert request.focus_areas is None
        assert request.max_insights == 10  # Default value


class TestResearchInsightData:
    """Test ResearchInsightData model validation."""
    
    def test_valid_research_insight_data(self):
        """Test valid research insight creation."""
        insight = ResearchInsightData(
            entity_id="entity_1",
            insight_type="market_data",
            title="Market Analysis Results",
            content="Strong market demand identified",
            sources=["source1.com", "source2.com"],
            relevance_score=0.85
        )
        
        assert insight.entity_id == "entity_1"
        assert insight.insight_type == "market_data"
        assert insight.title == "Market Analysis Results"
        assert len(insight.sources) == 2
        assert insight.relevance_score == 0.85

    def test_research_insight_relevance_bounds(self):
        """Test research insight relevance bounds validation."""
        # Valid bounds
        ResearchInsightData(entity_id="e1", insight_type="market", title="Test", content="Test", relevance_score=0.0)
        ResearchInsightData(entity_id="e1", insight_type="market", title="Test", content="Test", relevance_score=1.0)
        
        # Invalid bounds
        with pytest.raises(ValidationError):
            ResearchInsightData(entity_id="e1", insight_type="market", title="Test", content="Test", relevance_score=-0.1)
        with pytest.raises(ValidationError):
            ResearchInsightData(entity_id="e1", insight_type="market", title="Test", content="Test", relevance_score=1.1)

    def test_research_insight_default_sources(self):
        """Test research insight default sources."""
        insight = ResearchInsightData(
            entity_id="e1",
            insight_type="market",
            title="Test",
            content="Test",
            relevance_score=0.7
        )
        
        assert insight.sources == []  # Default empty list