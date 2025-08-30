"""Service for generating graph representations of documents and context."""
from __future__ import annotations

from typing import Any, Dict, AsyncGenerator

from .orchestrator import AuditorWorker

class GraphService:
    """Service to generate and broadcast graph data from documents."""

    def __init__(self, worker: AuditorWorker):
        self.worker = worker

    async def generate_graph_from_document(
        self, document_content: str, context: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Analyzes a document and yields graph nodes and edges."""
        
        prompt = self._create_graph_prompt(document_content, context)
        
        # For now, we'll get the full graph in one go. 
        # In a more advanced implementation, we could stream the results.
        try:
            graph_data = await self.worker.execute_audit(prompt)
            
            if "nodes" in graph_data and isinstance(graph_data["nodes"], list):
                for node in graph_data["nodes"]:
                    yield {"type": "graph_node", "data": node}
            
            if "edges" in graph_data and isinstance(graph_data["edges"], list):
                for edge in graph_data["edges"]:
                    yield {"type": "graph_edge", "data": edge}

        except Exception as e:
            # In case of an error, we can yield an error message.
            yield {"type": "graph_error", "message": str(e)}

    def _create_graph_prompt(self, document_content: str, context: str) -> str:
        """Creates the prompt for the LLM to generate graph data."""
        return f"""
        You are an expert in knowledge graph extraction. Analyze the following document and context. 
        Identify the key entities, concepts, and topics as nodes. The main idea of the document should be the central node.
        Identify the relationships between them as edges.

        Return the output as a single JSON object with two keys: "nodes" and "edges".

        - "nodes" should be a list of objects, each with:
          - "id": a short, unique, descriptive string identifier (e.g., "main_idea", "feature_x").
          - "label": a user-friendly label for the node.
          - "type": (optional) can be "idea", "concept", "feature", "risk", etc.

        - "edges" should be a list of objects, each with:
          - "id": a unique string identifier for the edge (e.g., "e1", "e2").
          - "source": the id of the source node.
          - "target": the id of the target node.
          - "label": (optional) a short description of the relationship.

        Here is the document:
        ---
        {document_content}
        ---

        Here is the context:
        ---
        {context}
        ---
        """
