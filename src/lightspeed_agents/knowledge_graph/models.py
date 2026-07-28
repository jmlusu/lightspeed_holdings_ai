from enum import Enum
from typing import Any
from datetime import datetime, UTC
from uuid import uuid4
from pydantic import BaseModel, Field


class GraphNodeType(str, Enum):
    """Types of nodes in the knowledge graph."""

    # Core entity types
    CONCEPT = "Concept"           # Abstract concepts, topics, ideas
    AGENT = "Agent"               # Agents in the system
    DECISION = "Decision"         # Decisions made by agents/leadership
    TASK = "Task"                 # Tasks assigned to agents
    DOCUMENT = "Document"         # Documents, files, artifacts
    PERSON = "Person"             # People (agents, humans, stakeholders)
    ORGANIZATION = "Organization" # Teams, departments, companies
    EVENT = "Event"               # Events, meetings, incidents
    PROJECT = "Project"           # Projects, initiatives
    SKILL = "Skill"               # Skills, capabilities, competencies
    TOOL = "Tool"                 # Tools, technologies, platforms
    METRIC = "Metric"             # Metrics, KPIs, measurements

    # Knowledge graph structural types
    TAG = "Tag"                   # Tags for categorization
    CATEGORY = "Category"         # High-level categories
    SOURCE = "Source"             # Source of information (doc, agent, system)


class GraphEdgeType(str, Enum):
    """Types of edges (relationships) in the knowledge graph."""

    # Structural relationships
    PART_OF = "PART_OF"           # Part-whole relationship
    HAS_PART = "HAS_PART"         # Inverse of PART_OF
    IS_A = "IS_A"                 # Type/subtype relationship
    INSTANCE_OF = "INSTANCE_OF"   # Instance-type relationship

    # Dependency relationships
    DEPENDS_ON = "DEPENDS_ON"     # A depends on B
    BLOCKS = "BLOCKS"             # A blocks B
    ENABLES = "ENABLES"           # A enables B
    REQUIRES = "REQUIRES"         # A requires B

    # Temporal relationships
    PRECEDES = "PRECEDES"         # A happens before B
    FOLLOWS = "FOLLOWS"           # A happens after B
    DURING = "DURING"             # A occurs during B
    OVERLAPS = "OVERLAPS"         # A overlaps with B

    # Causal relationships
    CAUSES = "CAUSES"             # A causes B
    INFLUENCES = "INFLUENCES"     # A influences B
    TRIGGERS = "TRIGGERS"         # A triggers B
    PREVENTS = "PREVENTS"         # A prevents B

    # Authorship/ownership
    CREATED_BY = "CREATED_BY"     # A created by B
    OWNED_BY = "OWNED_BY"         # A owned by B
    AUTHORED_BY = "AUTHORED_BY"   # A authored by B
    APPROVED_BY = "APPROVED_BY"   # A approved by B
    ASSIGNED_TO = "ASSIGNED_TO"   # A assigned to B

    # Semantic relationships
    RELATES_TO = "RELATES_TO"     # Generic relationship
    SIMILAR_TO = "SIMILAR_TO"     # A is similar to B
    OPPOSES = "OPPOSES"           # A opposes B
    SUPPORTS = "SUPPORTS"         # A supports B
    CONTRADICTS = "CONTRADICTS"   # A contradicts B
    REFERENCES = "REFERENCES"     # A references B
    DERIVES_FROM = "DERIVES_FROM" # A derives from B

    # Organizational relationships
    MEMBER_OF = "MEMBER_OF"       # A is member of B
    REPORTS_TO = "REPORTS_TO"     # A reports to B
    COLLABORATES_WITH = "COLLABORATES_WITH"  # A collaborates with B
    LEADS = "LEADS"               # A leads B

    # Knowledge relationships
    TAGGED_WITH = "TAGGED_WITH"   # A tagged with B
    CATEGORIZED_AS = "CATEGORIZED_AS"  # A categorized as B
    SOURCED_FROM = "SOURCED_FROM"      # A sourced from B
    MENTIONS = "MENTIONS"         # A mentions B
    IMPLEMENTS = "IMPLEMENTS"     # A implements B
    USES = "USES"                 # A uses B


class GraphNode(BaseModel):
    """Node in the knowledge graph."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    node_type: GraphNodeType
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    version: int = 1

    # Embedding for semantic similarity (optional, populated by embedding service)
    embedding: list[float] | None = None

    def touch(self):
        """Update access timestamp and version."""
        self.updated_at = datetime.now(UTC).isoformat()
        self.version += 1

    def add_property(self, key: str, value: Any):
        """Add or update a property."""
        self.properties[key] = value
        self.touch()

    def add_tag(self, tag: str):
        """Add a tag if not already present."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.touch()


class GraphEdge(BaseModel):
    """Edge (relationship) in the knowledge graph."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    edge_type: GraphEdgeType
    source_id: str  # Source node ID
    target_id: str  # Target node ID
    properties: dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0  # Relationship strength (0.0 to 1.0)
    confidence: float = 1.0  # Confidence in this relationship (0.0 to 1.0)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    version: int = 1
    created_by: str = ""  # Agent or system that created this edge

    def touch(self):
        """Update access timestamp and version."""
        self.updated_at = datetime.now(UTC).isoformat()
        self.version += 1

    def add_property(self, key: str, value: Any):
        """Add or update a property."""
        self.properties[key] = value
        self.touch()


class KnowledgeGraph(BaseModel):
    """Complete knowledge graph container."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    name: str = "default"
    nodes: dict[str, GraphNode] = Field(default_factory=dict)
    edges: dict[str, GraphEdge] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    version: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_node(self, node: GraphNode) -> GraphNode:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        self.updated_at = datetime.now(UTC).isoformat()
        self.version += 1
        return node

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges."""
        if node_id not in self.nodes:
            return False
        # Remove all edges connected to this node
        edges_to_remove = [
            eid for eid, edge in self.edges.items()
            if edge.source_id == node_id or edge.target_id == node_id
        ]
        for eid in edges_to_remove:
            del self.edges[eid]
        del self.nodes[node_id]
        self.updated_at = datetime.now(UTC).isoformat()
        self.version += 1
        return True

    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        """Add an edge to the graph."""
        # Validate that both nodes exist
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError("Both source and target nodes must exist in the graph")
        self.edges[edge.id] = edge
        self.updated_at = datetime.now(UTC).isoformat()
        self.version += 1
        return edge

    def remove_edge(self, edge_id: str) -> bool:
        """Remove an edge by ID."""
        if edge_id not in self.edges:
            return False
        del self.edges[edge_id]
        self.updated_at = datetime.now(UTC).isoformat()
        self.version += 1
        return True

    def get_edge(self, edge_id: str) -> GraphEdge | None:
        """Get an edge by ID."""
        return self.edges.get(edge_id)

    def get_outgoing_edges(self, node_id: str) -> list[GraphEdge]:
        """Get all outgoing edges from a node."""
        return [e for e in self.edges.values() if e.source_id == node_id]

    def get_incoming_edges(self, node_id: str) -> list[GraphEdge]:
        """Get all incoming edges to a node."""
        return [e for e in self.edges.values() if e.target_id == node_id]

    def get_neighbors(self, node_id: str, edge_types: list[GraphEdgeType] = None) -> list[GraphNode]:
        """Get neighbor nodes connected to a node."""
        neighbors = []
        for edge in self.edges.values():
            if edge.source_id == node_id:
                neighbor = self.nodes.get(edge.target_id)
                if neighbor and (edge_types is None or edge.edge_type in edge_types):
                    neighbors.append(neighbor)
            elif edge.target_id == node_id:
                neighbor = self.nodes.get(edge.source_id)
                if neighbor and (edge_types is None or edge.edge_type in edge_types):
                    neighbors.append(neighbor)
        return neighbors

    def find_nodes_by_type(self, node_type: GraphNodeType) -> list[GraphNode]:
        """Find all nodes of a specific type."""
        return [n for n in self.nodes.values() if n.node_type == node_type]

    def find_nodes_by_tag(self, tag: str) -> list[GraphNode]:
        """Find all nodes with a specific tag."""
        return [n for n in self.nodes.values() if tag in n.tags]

    def find_edges_by_type(self, edge_type: GraphEdgeType) -> list[GraphEdge]:
        """Find all edges of a specific type."""
        return [e for e in self.edges.values() if e.edge_type == edge_type]

    def get_subgraph(self, node_ids: list[str]) -> "KnowledgeGraph":
        """Extract a subgraph containing only the specified nodes and their connecting edges."""
        subgraph = KnowledgeGraph(name=f"subgraph-{self.id}")
        for node_id in node_ids:
            if node_id in self.nodes:
                subgraph.add_node(self.nodes[node_id])
        for edge in self.edges.values():
            if edge.source_id in node_ids and edge.target_id in node_ids:
                subgraph.add_edge(edge)
        return subgraph

    def get_stats(self) -> dict:
        """Get graph statistics."""
        node_types = {}
        for node in self.nodes.values():
            node_types[node.node_type.value] = node_types.get(node.node_type.value, 0) + 1

        edge_types = {}
        for edge in self.edges.values():
            edge_types[edge.edge_type.value] = edge_types.get(edge.edge_type.value, 0) + 1

        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "node_types": node_types,
            "edge_types": edge_types,
            "version": self.version,
        }