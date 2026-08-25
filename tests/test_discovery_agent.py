"""
Tests for Discovery Agent - Multi-hop Discovery Experience

Q2 Growth Track: Graph visualization, guided discovery, cross-document references.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.agents import discovery_agent
from app.agents.discovery_agent import (
    DocumentNode,
    RelationshipEdge,
    DocumentGraph,
    DiscoverySession,
    DiscoveryFlowType,
    DiscoveryStatus,
    CrossDocumentReference,
    DiscoveryInsight,
    create_discovery_session,
    advance_session,
    complete_session,
    get_strongest_connections,
    find_bridging_documents,
    compute_graph_metrics,
    analyze_document_graph,
    find_cross_references,
    synthesize_discovery,
)


class TestDocumentNode:
    """Test DocumentNode dataclass."""

    def test_creation(self):
        """Test creating a DocumentNode."""
        node = DocumentNode(
            id="doc-123",
            title="Test Document",
            entity_ids=["entity-1", "entity-2"],
            salience=0.85,
            connection_count=5,
        )
        
        assert node.id == "doc-123"
        assert node.title == "Test Document"
        assert len(node.entity_ids) == 2
        assert node.salience == 0.85


class TestRelationshipEdge:
    """Test RelationshipEdge dataclass."""

    def test_creation(self):
        """Test creating a RelationshipEdge."""
        edge = RelationshipEdge(
            source_id="doc-1",
            target_id="doc-2",
            relationship_type="cites",
            weight=0.75,
            evidence="Document 1 references Document 2",
        )
        
        assert edge.source_id == "doc-1"
        assert edge.target_id == "doc-2"
        assert edge.relationship_type == "cites"
        assert edge.weight == 0.75


class TestDocumentGraph:
    """Test DocumentGraph dataclass."""

    def test_creation(self):
        """Test creating a DocumentGraph."""
        node1 = DocumentNode(id="doc-1", title="Doc 1")
        node2 = DocumentNode(id="doc-2", title="Doc 2")
        edge = RelationshipEdge(
            source_id="doc-1",
            target_id="doc-2",
            relationship_type="cites",
        )
        
        graph = DocumentGraph(nodes=[node1, node2], edges=[edge])
        
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_get_node(self):
        """Test getting a node by ID."""
        node = DocumentNode(id="doc-1", title="Doc 1")
        graph = DocumentGraph(nodes=[node])
        
        found = graph.get_node("doc-1")
        assert found is not None
        assert found.title == "Doc 1"
        
        not_found = graph.get_node("doc-nonexistent")
        assert not_found is None

    def test_get_neighbors(self):
        """Test getting neighboring nodes."""
        graph = DocumentGraph(
            nodes=[
                DocumentNode(id="doc-1", title="Doc 1"),
                DocumentNode(id="doc-2", title="Doc 2"),
                DocumentNode(id="doc-3", title="Doc 3"),
            ],
            edges=[
                RelationshipEdge(source_id="doc-1", target_id="doc-2", relationship_type="cites"),
                RelationshipEdge(source_id="doc-1", target_id="doc-3", relationship_type="extends"),
            ],
        )
        
        neighbors = graph.get_neighbors("doc-1")
        assert "doc-2" in neighbors
        assert "doc-3" in neighbors
        assert len(neighbors) == 2


class TestDiscoveryFlowType:
    """Test DiscoveryFlowType enum."""

    def test_all_types_exist(self):
        """All flow types should exist."""
        assert DiscoveryFlowType.EXPLORE_RELATED.value == "explore_related"
        assert DiscoveryFlowType.TRACE_ORIGIN.value == "trace_origin"
        assert DiscoveryFlowType.FIND_CONTRADICTIONS.value == "find_contradictions"
        assert DiscoveryFlowType.SYNTHESIZE.value == "synthesize"
        assert DiscoveryFlowType.TEMPORAL_JOURNEY.value == "temporal_journey"


class TestDiscoveryStatus:
    """Test DiscoveryStatus enum."""

    def test_all_statuses_exist(self):
        """All statuses should exist."""
        assert DiscoveryStatus.ACTIVE.value == "active"
        assert DiscoveryStatus.COMPLETED.value == "completed"
        assert DiscoveryStatus.ABANDONED.value == "abandoned"


class TestDiscoverySession:
    """Test DiscoverySession dataclass."""

    def test_creation_via_factory(self):
        """Test creating a DiscoverySession via factory function."""
        session = create_discovery_session(
            user_id="user-123",
            starting_doc_id="doc-1",
            flow_type=DiscoveryFlowType.EXPLORE_RELATED,
        )
        
        assert session.user_id == "user-123"
        assert session.starting_doc_id == "doc-1"
        assert session.flow_type == DiscoveryFlowType.EXPLORE_RELATED
        assert session.status == DiscoveryStatus.ACTIVE
        assert session.path == ["doc-1"]
        assert session.current_step == 0


class TestCreateDiscoverySession:
    """Test create_discovery_session function."""

    def test_create_basic_session(self):
        """Test creating a basic discovery session."""
        session = create_discovery_session(
            user_id="user-123",
            starting_doc_id="doc-1",
            flow_type=DiscoveryFlowType.EXPLORE_RELATED,
        )
        
        assert session.user_id == "user-123"
        assert session.starting_doc_id == "doc-1"
        assert session.path == ["doc-1"]

    def test_create_session_with_target(self):
        """Test creating a session with target document."""
        session = create_discovery_session(
            user_id="user-123",
            starting_doc_id="doc-1",
            flow_type=DiscoveryFlowType.TRACE_ORIGIN,
            target_doc_id="doc-final",
        )
        
        assert session.target_doc_id == "doc-final"


class TestAdvanceSession:
    """Test advance_session function."""

    def test_advance_session(self):
        """Test advancing a session."""
        session = create_discovery_session(
            user_id="user-123",
            starting_doc_id="doc-1",
        )
        
        connection = {
            "from_doc": "doc-1",
            "to_doc": "doc-2",
            "insight": "Found connection",
        }
        
        session = advance_session(session, "doc-2", connection)
        
        assert "doc-2" in session.path
        assert len(session.path) == 2
        assert session.current_step == 1
        assert session.steps_taken == 1
        assert len(session.connections_found) == 1


class TestCompleteSession:
    """Test complete_session function."""

    def test_complete_session(self):
        """Test completing a session."""
        session = create_discovery_session(
            user_id="user-123",
            starting_doc_id="doc-1",
        )
        
        session = complete_session(session)
        
        assert session.status == DiscoveryStatus.COMPLETED
        assert session.completed_at is not None


class TestGetStrongestConnections:
    """Test get_strongest_connections function."""

    def test_get_strongest_connections(self):
        """Test getting strongest connections."""
        graph = DocumentGraph(
            nodes=[
                DocumentNode(id="doc-1", title="Doc 1"),
                DocumentNode(id="doc-2", title="Doc 2"),
                DocumentNode(id="doc-3", title="Doc 3"),
            ],
            edges=[
                RelationshipEdge(source_id="doc-1", target_id="doc-2", relationship_type="cites", weight=0.9),
                RelationshipEdge(source_id="doc-1", target_id="doc-3", relationship_type="extends", weight=0.3),
            ],
        )
        
        connections = get_strongest_connections(graph, "doc-1", limit=5)
        
        assert len(connections) == 2
        assert connections[0] == ("doc-2", 0.9)  # Highest weight first


class TestFindBridgingDocuments:
    """Test find_bridging_documents function."""

    def test_find_bridging_documents(self):
        """Test finding bridging documents - need 3+ neighbors with 2+ diverse types."""
        graph = DocumentGraph(
            nodes=[
                DocumentNode(id="doc-1", title="Doc 1"),
                DocumentNode(id="doc-2", title="Doc 2"),
                DocumentNode(id="doc-3", title="Doc 3"),
                DocumentNode(id="doc-4", title="Doc 4"),
                DocumentNode(id="doc-5", title="Doc 5"),
            ],
            edges=[
                RelationshipEdge(source_id="doc-1", target_id="doc-2", relationship_type="cites"),
                RelationshipEdge(source_id="doc-1", target_id="doc-3", relationship_type="extends"),
                RelationshipEdge(source_id="doc-1", target_id="doc-4", relationship_type="mentions"),
                RelationshipEdge(source_id="doc-2", target_id="doc-5", relationship_type="contradicts"),
            ],
        )
        
        bridging = find_bridging_documents(graph)
        
        # doc-1 has 3 neighbors (>=3) and 2+ diverse types (cites, extends, mentions), so it's bridging
        assert "doc-1" in bridging

    def test_no_bridging_with_few_neighbors(self):
        """Test that documents with fewer than 3 neighbors are not bridging."""
        graph = DocumentGraph(
            nodes=[
                DocumentNode(id="doc-1", title="Doc 1"),
                DocumentNode(id="doc-2", title="Doc 2"),
            ],
            edges=[
                RelationshipEdge(source_id="doc-1", target_id="doc-2", relationship_type="cites"),
            ],
        )
        
        bridging = find_bridging_documents(graph)
        
        assert len(bridging) == 0


class TestComputeGraphMetrics:
    """Test compute_graph_metrics function."""

    def test_compute_metrics_empty_graph(self):
        """Test metrics for empty graph."""
        graph = DocumentGraph()
        metrics = compute_graph_metrics(graph)
        
        assert metrics["total_nodes"] == 0
        assert metrics["total_edges"] == 0

    def test_compute_metrics_with_data(self):
        """Test metrics with populated graph."""
        graph = DocumentGraph(
            nodes=[
                DocumentNode(id="doc-1", title="Doc 1"),
                DocumentNode(id="doc-2", title="Doc 2"),
            ],
            edges=[
                RelationshipEdge(source_id="doc-1", target_id="doc-2", relationship_type="cites", weight=0.8),
            ],
        )
        
        metrics = compute_graph_metrics(graph)
        
        assert metrics["total_nodes"] == 2
        assert metrics["total_edges"] == 1
        assert metrics["avg_connections_per_node"] == 1.0
        assert metrics["avg_edge_weight"] == 0.8


# ─── LLM-powered function tests ───────────────────────────────────────────────

class TestAnalyzeDocumentGraph:
    """Test analyze_document_graph function."""

    @pytest.mark.asyncio
    @patch("app.agents.discovery_agent._get_client")
    async def test_analyze_graph_success(self, mock_get_client):
        """Test successful graph analysis."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"nodes": [{"id": "doc-1", "title": "Doc 1", "entity_ids": [], "salience": 0.8, "connection_count": 2}], "edges": [{"source_id": "doc-1", "target_id": "doc-2", "relationship_type": "cites", "weight": 0.9, "evidence": "Reference found"}]}'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        documents = [
            {"id": "doc-1", "title": "Document 1", "content": "Content about X"},
            {"id": "doc-2", "title": "Document 2", "content": "Content about Y"},
        ]
        
        graph = await analyze_document_graph(documents)
        
        assert len(graph.nodes) == 1
        assert len(graph.edges) == 1
        assert graph.edges[0].relationship_type == "cites"

    @pytest.mark.asyncio
    @patch("app.agents.discovery_agent._get_client")
    async def test_analyze_graph_error(self, mock_get_client):
        """Test graph analysis handles errors gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        mock_get_client.return_value = mock_client

        documents = [{"id": "doc-1", "title": "Test", "content": "Content"}]
        
        graph = await analyze_document_graph(documents)
        
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0


class TestFindCrossReferences:
    """Test find_cross_references function."""

    @pytest.mark.asyncio
    @patch("app.agents.discovery_agent._get_client")
    async def test_find_references_success(self, mock_get_client):
        """Test successful cross-reference finding."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"references": [{"source_doc_id": "doc-1", "target_doc_id": "doc-2", "source_excerpt": "Passage 1", "target_excerpt": "Passage 2", "reference_type": "cites", "relevance_score": 0.85}], "summary": "Doc 1 cites Doc 2"}'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        doc1 = {"id": "doc-1", "title": "Doc 1", "content": "Content 1"}
        doc2 = {"id": "doc-2", "title": "Doc 2", "content": "Content 2"}
        
        references = await find_cross_references(doc1, doc2)
        
        assert len(references) == 1
        assert references[0].reference_type == "cites"
        assert references[0].relevance_score == 0.85

    @pytest.mark.asyncio
    @patch("app.agents.discovery_agent._get_client")
    async def test_find_references_error(self, mock_get_client):
        """Test cross-reference handles errors gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        mock_get_client.return_value = mock_client

        doc1 = {"id": "doc-1", "title": "Doc 1", "content": "Content 1"}
        doc2 = {"id": "doc-2", "title": "Doc 2", "content": "Content 2"}
        
        references = await find_cross_references(doc1, doc2)
        
        assert references == []


class TestSynthesizeDiscovery:
    """Test synthesize_discovery function."""

    @pytest.mark.asyncio
    @patch("app.agents.discovery_agent._get_client")
    async def test_synthesize_success(self, mock_get_client):
        """Test successful synthesis."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"title": "Key Insight", "description": "Synthesis of documents", "confidence": 0.9, "evidence": ["Point 1", "Point 2"]}'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        session = create_discovery_session(
            user_id="user-123",
            starting_doc_id="doc-1",
        )
        session.path = ["doc-1", "doc-2"]
        session.connections_found = [{"insight": "Connection found"}]
        
        documents = [
            {"id": "doc-1", "title": "Doc 1", "content": "Content 1"},
            {"id": "doc-2", "title": "Doc 2", "content": "Content 2"},
        ]
        
        synthesis = await synthesize_discovery(session, documents)
        
        assert synthesis.title == "Key Insight"
        assert synthesis.confidence == 0.9
        assert len(synthesis.evidence) == 2

    @pytest.mark.asyncio
    @patch("app.agents.discovery_agent._get_client")
    async def test_synthesize_error(self, mock_get_client):
        """Test synthesis handles errors gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        mock_get_client.return_value = mock_client

        session = create_discovery_session(user_id="user-123", starting_doc_id="doc-1")
        documents = [{"id": "doc-1", "title": "Doc 1", "content": "Content"}]
        
        synthesis = await synthesize_discovery(session, documents)
        
        assert synthesis.confidence == 0.3  # Default low confidence on error
