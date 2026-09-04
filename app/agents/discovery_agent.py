"""
Discovery Agent - Multi-hop Discovery Experience

Q2 Growth Track: Graph visualization, guided discovery, cross-document references.

Extends multi-hop reasoning with:
- Document relationship graph analysis
- Guided discovery flows
- Cross-document reference highlighting
- Discovery analytics
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

# Shared client seam: tests patch <module>._get_client, which rebinds
# this module attribute and is picked up by all call sites below.
from app.agents.llm_client import get_llm_client as _get_client
from app.config import settings

log = logging.getLogger(__name__)

# ─── LLM Client ───────────────────────────────────────────────────────────────


# ─── Enums ───────────────────────────────────────────────────────────────────

class DiscoveryFlowType(Enum):
    """Types of guided discovery flows."""
    EXPLORE_RELATED = "explore_related"
    TRACE_ORIGIN = "trace_origin"
    FIND_CONTRADICTIONS = "find_contradictions"
    SYNTHESIZE = "synthesize"
    TEMPORAL_JOURNEY = "temporal_journey"


class DiscoveryStatus(Enum):
    """Status of a discovery session."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# ─── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class DocumentNode:
    """A node in the document relationship graph."""
    id: str
    title: str
    entity_ids: list[str] = field(default_factory=list)
    salience: float = 0.5
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    connection_count: int = 0


@dataclass
class RelationshipEdge:
    """An edge representing relationship between documents."""
    source_id: str
    target_id: str
    relationship_type: str  # "cites", "contradicts", "extends", "mentions"
    weight: float = 0.5
    evidence: str = ""


@dataclass
class DocumentGraph:
    """Document relationship graph."""
    nodes: list[DocumentNode] = field(default_factory=list)
    edges: list[RelationshipEdge] = field(default_factory=list)

    def get_node(self, node_id: str) -> DocumentNode | None:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_neighbors(self, node_id: str) -> list[str]:
        """Get IDs of neighboring nodes."""
        neighbors = []
        for edge in self.edges:
            if edge.source_id == node_id:
                neighbors.append(edge.target_id)
            elif edge.target_id == node_id:
                neighbors.append(edge.source_id)
        return neighbors


@dataclass
class DiscoverySession:
    """A guided discovery session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Flow details
    flow_type: DiscoveryFlowType = DiscoveryFlowType.EXPLORE_RELATED
    starting_doc_id: str = ""
    target_doc_id: str | None = None

    # Path taken
    path: list[str] = field(default_factory=list)  # Document IDs in order
    current_step: int = 0

    # Results
    connections_found: list[dict] = field(default_factory=list)

    # Metadata
    status: DiscoveryStatus = DiscoveryStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    # Analytics
    steps_taken: int = 0
    documents_explored: int = 0


@dataclass
class CrossDocumentReference:
    """A reference to content across documents."""
    source_doc_id: str
    target_doc_id: str
    source_excerpt: str
    target_excerpt: str
    reference_type: str  # "cites", "extends", "contradicts", "mentions"
    relevance_score: float = 0.5


@dataclass
class DiscoveryInsight:
    """An insight discovered during guided exploration."""
    title: str
    description: str
    related_doc_ids: list[str]
    insight_type: str  # "connection", "contradiction", "evolution"
    confidence: float = 0.5
    evidence: list[str] = field(default_factory=list)


# ─── Prompts ─────────────────────────────────────────────────────────────────

GRAPH_ANALYSIS_PROMPT = """Analyze documents and their relationships to build a connection graph.

Documents:
{documents}

Identify:
1. Key entities and topics in each document
2. Relationships between documents (cites, extends, contradicts, mentions)
3. Strong and weak connections
4. Potential bridging documents that connect otherwise unrelated topics

Respond with JSON:
{{
    "nodes": [
        {{
            "id": "doc-123",
            "title": "Document Title",
            "entity_ids": ["entity-1", "entity-2"],
            "salience": 0.85,
            "connection_count": 3
        }}
    ],
    "edges": [
        {{
            "source_id": "doc-1",
            "target_id": "doc-2",
            "relationship_type": "cites|extends|contradicts|mentions",
            "weight": 0.75,
            "evidence": "Brief evidence from documents"
        }}
    ]
}}"""


GUIDED_DISCOVERY_PROMPT = """You are guiding a user through a discovery journey.

Starting document: {start_title}
Discovery goal: {goal_type}
Target document (if any): {target_title}

Current path: {path}
Documents already explored: {explored}

Available documents:
{available_docs}

Based on the goal, suggest the next document to explore and explain why it matters.

If exploring related topics: Find the strongest connection.
If tracing origin: Find documents that influenced or preceded.
If finding contradictions: Find documents with opposing views.
If synthesizing: Find documents that together reveal something new.

Respond with JSON:
{{
    "next_doc_id": "doc-456",
    "next_doc_title": "Document Title",
    "reasoning": "Why this document is the right next step",
    "insight_preview": "What connection might be found here",
    "step_goal": "What to look for in this document"
}}"""


CROSS_REFERENCE_PROMPT = """Find cross-document references and connections.

Document 1: {doc1_title}
{doc1_content}

Document 2: {doc2_title}
{doc2_content}

Identify:
1. Direct references (one doc mentions the other)
2. Thematic connections (similar topics, arguments)
3. Temporal relationships (which came first, how views evolved)
4. Contradictions or opposing viewpoints

Respond with JSON:
{{
    "references": [
        {{
            "source_doc_id": "doc-1",
            "target_doc_id": "doc-2",
            "source_excerpt": "Relevant passage from doc 1",
            "target_excerpt": "Relevant passage from doc 2",
            "reference_type": "cites|extends|contradicts|mentions",
            "relevance_score": 0.85
        }}
    ],
    "summary": "Overall relationship between documents"
}}"""


DISCOVERY_SYNTHESIS_PROMPT = """Synthesize findings from a discovery journey.

Journey path:
{path}

Connections discovered:
{connections}

What new insight emerges from these connections? Synthesize a coherent understanding that wasn't apparent from any single document.

Respond with JSON:
{{
    "title": "Synthesis Title",
    "description": "Full explanation of the synthesized insight",
    "confidence": 0.85,
    "evidence": ["Supporting point 1", "Supporting point 2"]
}}"""


# ─── Graph Analysis ───────────────────────────────────────────────────────────

async def analyze_document_graph(
    documents: list[dict],
) -> DocumentGraph:
    """
    Analyze documents to build a relationship graph.

    Args:
        documents: List of document dicts with id, title, content

    Returns:
        DocumentGraph with nodes and edges
    """
    import json

    client = _get_client()

    # Format documents for prompt
    doc_text = "\n\n".join([
        f"[{doc.get('id', i+1)}] {doc.get('title', 'Untitled')}\n"
        f"Content: {doc.get('content', '')[:1000]}..."
        for i, doc in enumerate(documents[:15])  # Limit to 15 docs
    ])

    prompt = GRAPH_ANALYSIS_PROMPT.format(documents=doc_text)

    try:
        response = await client.chat.completions.create(
            model=settings.MULTIHOP_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # Build graph
        nodes = []
        for node_data in result.get("nodes", []):
            nodes.append(DocumentNode(
                id=node_data["id"],
                title=node_data["title"],
                entity_ids=node_data.get("entity_ids", []),
                salience=node_data.get("salience", 0.5),
                connection_count=node_data.get("connection_count", 0),
            ))

        edges = []
        for edge_data in result.get("edges", []):
            edges.append(RelationshipEdge(
                source_id=edge_data["source_id"],
                target_id=edge_data["target_id"],
                relationship_type=edge_data.get("relationship_type", "mentions"),
                weight=edge_data.get("weight", 0.5),
                evidence=edge_data.get("evidence", ""),
            ))

        return DocumentGraph(nodes=nodes, edges=edges)

    except Exception as e:
        log.warning(f"Graph analysis failed: {e}")
        return DocumentGraph()


async def get_next_discovery_step(
    session: DiscoverySession,
    documents: list[dict],
    graph: DocumentGraph,
) -> dict:
    """
    Get the next step in a guided discovery flow.

    Args:
        session: Current discovery session
        documents: Available documents
        graph: Document relationship graph

    Returns:
        Dict with next_doc_id, reasoning, insight_preview, step_goal
    """
    import json

    client = _get_client()

    # Get starting document title
    start_title = "Unknown"
    for doc in documents:
        if doc.get("id") == session.starting_doc_id:
            start_title = doc.get("title", "Untitled")
            break

    # Get target document title
    target_title = "None specified"
    if session.target_doc_id:
        for doc in documents:
            if doc.get("id") == session.target_doc_id:
                target_title = doc.get("title", "Untitled")
                break

    # Get goal type
    goal_map = {
        DiscoveryFlowType.EXPLORE_RELATED: "Explore related topics and connections",
        DiscoveryFlowType.TRACE_ORIGIN: "Trace the origin of an idea",
        DiscoveryFlowType.FIND_CONTRADICTIONS: "Find contradictory viewpoints",
        DiscoveryFlowType.SYNTHESIZE: "Synthesize insights from multiple sources",
        DiscoveryFlowType.TEMPORAL_JOURNEY: "Journey through time to understand evolution",
    }
    goal_type = goal_map.get(session.flow_type, "Explore connections")

    # Format path and explored docs
    path_titles = []
    for doc_id in session.path:
        for doc in documents:
            if doc.get("id") == doc_id:
                path_titles.append(doc.get("title", "Untitled"))
                break

    explored_ids = set(session.path)
    available = [doc for doc in documents if doc.get("id") not in explored_ids][:10]

    available_text = "\n".join([
        f"- {doc.get('title', 'Untitled')}"
        for doc in available
    ])

    prompt = GUIDED_DISCOVERY_PROMPT.format(
        start_title=start_title,
        goal_type=goal_type,
        target_title=target_title,
        path=" -> ".join(path_titles) or "Start",
        explored=", ".join(path_titles) or "None",
        available_docs=available_text,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.MULTIHOP_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=500,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        return {
            "next_doc_id": result.get("next_doc_id", ""),
            "next_doc_title": result.get("next_doc_title", ""),
            "reasoning": result.get("reasoning", ""),
            "insight_preview": result.get("insight_preview", ""),
            "step_goal": result.get("step_goal", ""),
        }

    except Exception as e:
        log.warning(f"Discovery step failed: {e}")
        return {
            "next_doc_id": "",
            "reasoning": "Unable to determine next step",
            "insight_preview": "",
            "step_goal": "",
        }


async def find_cross_references(
    doc1: dict,
    doc2: dict,
) -> list[CrossDocumentReference]:
    """
    Find references between two documents.

    Args:
        doc1: First document dict
        doc2: Second document dict

    Returns:
        List of CrossDocumentReference
    """
    import json

    client = _get_client()

    prompt = CROSS_REFERENCE_PROMPT.format(
        doc1_title=doc1.get("title", "Untitled"),
        doc1_content=doc1.get("content", "")[:2000],
        doc2_title=doc2.get("title", "Untitled"),
        doc2_content=doc2.get("content", "")[:2000],
    )

    try:
        response = await client.chat.completions.create(
            model=settings.MULTIHOP_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1000,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        references = []
        for ref_data in result.get("references", []):
            references.append(CrossDocumentReference(
                source_doc_id=ref_data.get("source_doc_id", doc1.get("id", "")),
                target_doc_id=ref_data.get("target_doc_id", doc2.get("id", "")),
                source_excerpt=ref_data.get("source_excerpt", ""),
                target_excerpt=ref_data.get("target_excerpt", ""),
                reference_type=ref_data.get("reference_type", "mentions"),
                relevance_score=ref_data.get("relevance_score", 0.5),
            ))

        return references

    except Exception as e:
        log.warning(f"Cross-reference search failed: {e}")
        return []


async def synthesize_discovery(
    session: DiscoverySession,
    documents: list[dict],
) -> DiscoveryInsight:
    """
    Synthesize findings from a discovery journey.

    Args:
        session: Completed discovery session
        documents: All available documents

    Returns:
        DiscoveryInsight with synthesized understanding
    """
    import json

    client = _get_client()

    # Get document titles for path
    path_info = []
    for doc_id in session.path:
        for doc in documents:
            if doc.get("id") == doc_id:
                path_info.append(f"- {doc.get('title', 'Untitled')}")
                break

    connections_info = "\n".join([
        f"- {c.get('title', 'Connection')}: {c.get('description', '')}"
        for c in session.connections_found
    ]) or "No specific connections recorded"

    prompt = DISCOVERY_SYNTHESIS_PROMPT.format(
        path="\n".join(path_info),
        connections=connections_info,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.MULTIHOP_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=800,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        return DiscoveryInsight(
            title=result.get("title", "Discovery"),
            description=result.get("description", ""),
            related_doc_ids=session.path,
            insight_type="synthesis",
            confidence=result.get("confidence", 0.5),
            evidence=result.get("evidence", []),
        )

    except Exception as e:
        log.warning(f"Discovery synthesis failed: {e}")
        return DiscoveryInsight(
            title="Discovery Complete",
            description="Unable to synthesize findings",
            related_doc_ids=session.path,
            insight_type="synthesis",
            confidence=0.3,
        )


# ─── Discovery Session Management ─────────────────────────────────────────────

def create_discovery_session(
    user_id: str,
    starting_doc_id: str,
    flow_type: DiscoveryFlowType = DiscoveryFlowType.EXPLORE_RELATED,
    target_doc_id: str | None = None,
) -> DiscoverySession:
    """
    Create a new discovery session.

    Args:
        user_id: User ID
        starting_doc_id: Starting document ID
        flow_type: Type of discovery flow
        target_doc_id: Optional target document ID

    Returns:
        DiscoverySession instance
    """
    return DiscoverySession(
        user_id=user_id,
        starting_doc_id=starting_doc_id,
        flow_type=flow_type,
        target_doc_id=target_doc_id,
        path=[starting_doc_id],
        current_step=0,
    )


def advance_session(
    session: DiscoverySession,
    next_doc_id: str,
    connection: dict,
) -> DiscoverySession:
    """
    Advance a discovery session to the next step.

    Args:
        session: Current session
        next_doc_id: Next document ID
        connection: Connection info dict

    Returns:
        Updated session
    """
    session.path.append(next_doc_id)
    session.current_step += 1
    session.steps_taken += 1
    session.documents_explored += 1
    session.connections_found.append(connection)

    return session


def complete_session(session: DiscoverySession) -> DiscoverySession:
    """
    Mark a discovery session as completed.

    Args:
        session: Session to complete

    Returns:
        Updated session
    """
    session.status = DiscoveryStatus.COMPLETED
    session.completed_at = datetime.now(UTC)
    return session


# ─── Graph Utilities ──────────────────────────────────────────────────────────

def get_strongest_connections(
    graph: DocumentGraph,
    doc_id: str,
    limit: int = 5,
) -> list[tuple[str, float]]:
    """
    Get strongest connections for a document.

    Args:
        graph: Document graph
        doc_id: Source document ID
        limit: Maximum connections to return

    Returns:
        List of (target_id, weight) tuples
    """
    connections = []

    for edge in graph.edges:
        if edge.source_id == doc_id:
            connections.append((edge.target_id, edge.weight))
        elif edge.target_id == doc_id:
            connections.append((edge.source_id, edge.weight))

    # Sort by weight and return top
    connections.sort(key=lambda x: x[1], reverse=True)
    return connections[:limit]


def find_bridging_documents(
    graph: DocumentGraph,
) -> list[str]:
    """
    Find documents that connect otherwise unrelated topics.

    Args:
        graph: Document graph

    Returns:
        List of bridging document IDs
    """
    # A bridging document connects to multiple disconnected components
    # This is a simplified implementation
    bridging = []

    for node in graph.nodes:
        # Documents with high connection count and diverse connections
        neighbors = graph.get_neighbors(node.id)

        # Check for diverse relationship types
        edge_types = set()
        for edge in graph.edges:
            if edge.source_id == node.id:
                edge_types.add(edge.relationship_type)
            elif edge.target_id == node.id:
                edge_types.add(edge.relationship_type)

        # High connectivity + diverse types = bridging
        if len(neighbors) >= 3 and len(edge_types) >= 2:
            bridging.append(node.id)

    return bridging


def compute_graph_metrics(graph: DocumentGraph) -> dict:
    """
    Compute metrics for a document graph.

    Args:
        graph: Document graph

    Returns:
        Dict with graph metrics
    """
    total_nodes = len(graph.nodes)
    total_edges = len(graph.edges)

    # Average connections per node
    avg_connections = (total_edges * 2 / total_nodes) if total_nodes > 0 else 0

    # Edge type distribution
    edge_types: dict[str, int] = {}
    for edge in graph.edges:
        edge_types[edge.relationship_type] = edge_types.get(edge.relationship_type, 0) + 1

    # Average weight
    avg_weight = sum(e.weight for e in graph.edges) / total_edges if total_edges > 0 else 0

    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "avg_connections_per_node": round(avg_connections, 2),
        "edge_type_distribution": edge_types,
        "avg_edge_weight": round(avg_weight, 2),
        "graph_density": round(total_edges / (total_nodes * (total_nodes - 1) / 2), 4) if total_nodes > 1 else 0,
    }
