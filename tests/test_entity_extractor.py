"""Tests for entity extraction service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import json

from llm_council.services.entity_extractor import EntityExtractor, Entity, Relationship, ContextGraph
from llm_council.orchestrator import AuditorWorker


class TestEntityExtraction:
    """Test entity extraction functionality."""
    
    def test_entity_creation(self):
        """Test Entity dataclass creation."""
        entity = Entity(
            id="test_entity",
            label="Test Entity",
            type="core_idea", 
            description="A test entity",
            importance=0.8,
            certainty=0.9
        )
        
        assert entity.id == "test_entity"
        assert entity.label == "Test Entity"
        assert entity.type == "core_idea"
        assert entity.importance == 0.8
        assert entity.certainty == 0.9
    
    def test_relationship_creation(self):
        """Test Relationship dataclass creation."""
        relationship = Relationship(
            id="test_rel",
            source_id="entity1",
            target_id="entity2",
            type="enables",
            label="enables",
            strength=0.7,
            description="Entity 1 enables Entity 2"
        )
        
        assert relationship.id == "test_rel"
        assert relationship.source_id == "entity1"
        assert relationship.target_id == "entity2"
        assert relationship.type == "enables"
        assert relationship.strength == 0.7

    def test_context_graph_creation(self):
        """Test ContextGraph dataclass creation."""
        entities = [
            Entity("e1", "Entity 1", "core_idea", "Test", 0.9, 0.8),
            Entity("e2", "Entity 2", "feature", "Test", 0.7, 0.6)
        ]
        relationships = [
            Relationship("r1", "e1", "e2", "enables", "enables", 0.8, "Test")
        ]
        
        graph = ContextGraph(
            entities=entities,
            relationships=relationships,
            central_entity_id="e1",
            confidence_score=0.75
        )
        
        assert len(graph.entities) == 2
        assert len(graph.relationships) == 1
        assert graph.central_entity_id == "e1"
        assert graph.confidence_score == 0.75

    @pytest.mark.asyncio
    async def test_extract_context_graph_success(self):
        """Test successful context graph extraction."""
        mock_worker = AsyncMock(spec=AuditorWorker)
        mock_worker.model = "gpt-4o"
        
        # Mock LLM response
        mock_response = {
            "entities": [
                {
                    "id": "mobile_app",
                    "label": "Water Tracking Mobile App",
                    "type": "core_idea",
                    "description": "Mobile application for tracking daily water intake",
                    "importance": 0.9,
                    "certainty": 0.8
                },
                {
                    "id": "users",
                    "label": "Health-conscious Users", 
                    "type": "user_group",
                    "description": "People who want to maintain proper hydration",
                    "importance": 0.8,
                    "certainty": 0.9
                }
            ],
            "relationships": [
                {
                    "id": "app_targets_users",
                    "source": "mobile_app",
                    "target": "users",
                    "type": "targets",
                    "label": "targets",
                    "strength": 0.9,
                    "description": "App is designed for health-conscious users"
                }
            ]
        }
        
        mock_worker.execute_audit.return_value = json.dumps(mock_response)
        
        extractor = EntityExtractor(mock_worker)
        result = await extractor.extract_context_graph(
            "A mobile app that helps people track their daily water intake"
        )
        
        assert len(result.entities) == 2
        assert len(result.relationships) == 1
        assert result.central_entity_id == "mobile_app"  # Highest importance
        assert 0.0 <= result.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_extract_context_graph_with_context(self):
        """Test context graph extraction with additional context."""
        mock_worker = AsyncMock(spec=AuditorWorker)
        mock_worker.model = "gpt-4o"
        mock_worker.execute_audit.return_value = '{"entities": [], "relationships": []}'
        
        extractor = EntityExtractor(mock_worker)
        result = await extractor.extract_context_graph(
            "Test idea",
            additional_context="Additional market context"
        )
        
        # Verify prompt included additional context
        mock_worker.execute_audit.assert_called_once()
        call_args = mock_worker.execute_audit.call_args[0][0]
        assert "Additional market context" in call_args

    def test_reactflow_conversion(self):
        """Test conversion to ReactFlow format."""
        entities = [
            Entity("e1", "Core Idea", "core_idea", "Main concept", 1.0, 0.8),
            Entity("e2", "Feature", "feature", "Key feature", 0.7, 0.9)
        ]
        relationships = [
            Relationship("r1", "e1", "e2", "contains", "contains", 0.8, "Core contains feature")
        ]
        
        graph = ContextGraph(entities, relationships, "e1", 0.85)
        extractor = EntityExtractor(MagicMock())
        
        reactflow_data = extractor.to_reactflow_format(graph)
        
        assert "nodes" in reactflow_data
        assert "edges" in reactflow_data
        assert "central_entity" in reactflow_data
        assert "confidence" in reactflow_data
        
        assert len(reactflow_data["nodes"]) == 2
        assert len(reactflow_data["edges"]) == 1
        assert reactflow_data["central_entity"] == "e1"
        assert reactflow_data["confidence"] == 0.85
        
        # Verify central entity styling
        central_node = next(n for n in reactflow_data["nodes"] if n["id"] == "e1")
        assert central_node["style"]["background"] == "#3b82f6"
        assert central_node["type"] == "custom"

    def test_empty_entities_handling(self):
        """Test handling of empty entity list."""
        graph = ContextGraph([], [], "", 0.0)
        extractor = EntityExtractor(MagicMock())
        
        reactflow_data = extractor.to_reactflow_format(graph)
        
        assert reactflow_data["nodes"] == []
        assert reactflow_data["edges"] == []
        assert reactflow_data["central_entity"] == ""
        assert reactflow_data["confidence"] == 0.0