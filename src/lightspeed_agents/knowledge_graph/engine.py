"""Knowledge Graph Engine - High-level engine wrapping KnowledgeGraph with persistence and queries."""

import threading
import time
from datetime import datetime, UTC
from typing import Any, Optional
from uuid import uuid4

from lightspeed_agents.knowledge_graph.models import (
    GraphNode,
    GraphEdge,
    GraphNodeType,
    GraphEdgeType,
    KnowledgeGraph,
)
from lightspeed_agents.knowledge_graph.persistence import (
    GraphPersistence,
    get_persistence,
)


class TraversalDirection:
    """Graph traversal direction options."""
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    BOTH = "both"


class KnowledgeGraphEngine:
    """
    High-level Knowledge Graph Engine wrapping KnowledgeGraph with persistence,
    querying, traversal, and auto-save capabilities.
    
    Thread-safe operations with configurable auto-save interval.
    """

    def __init__(
        self,
        persistence_backend: str = "json",
        config: dict[str, Any] | None = None,
        auto_save_interval: float = 30.0,
        graph_name: str = "default",
        graph_path: str = "./data/knowledge_graph",
    ):
        """
        Initialize the Knowledge Graph Engine.
        
        Args:
            persistence_backend: Persistence backend type ("json", "csv", "kuzu")
            config: Configuration dict for persistence backend
            auto_save_interval: Auto-save interval in seconds (0 to disable)
            graph_name: Name of the knowledge graph
            graph_path: Path for persistence storage
        """
        self.persistence_backend = persistence_backend
        self.config = config or {}
        self.auto_save_interval = auto_save_interval
        self.graph_name = graph_name
        self.graph_path = graph_path
        
        # Thread safety
        self._lock = threading.RLock()
        self._auto_save_thread: threading.Thread | None = None
        self._stop_auto_save = threading.Event()
        self._dirty = False
        self._last_save_time = time.time()
        
        # Initialize persistence
        self._persistence: GraphPersistence = get_persistence(persistence_backend, **self.config)
        
        # Load or create graph
        self._graph: KnowledgeGraph = self._load_or_create_graph()
        
        # Start auto-save if enabled
        if self.auto_save_interval > 0:
            self._start_auto_save()

    def _load_or_create_graph(self) -> KnowledgeGraph:
        """Load existing graph or create new one."""
        if self._persistence.exists(self.graph_path):
            return self._persistence.load(self.graph_path)
        return KnowledgeGraph(name=self.graph_name)

    def _start_auto_save(self) -> None:
        """Start the auto-save background thread."""
        self._stop_auto_save.clear()
        self._auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self._auto_save_thread.start()

    def _auto_save_loop(self) -> None:
        """Background auto-save loop."""
        while not self._stop_auto_save.is_set():
            time.sleep(self.auto_save_interval)
            if self._stop_auto_save.is_set():
                break
            with self._lock:
                if self._dirty and time.time() - self._last_save_time >= self.auto_save_interval:
                    try:
                        self._save_internal()
                    except Exception:
                        pass  # Silently fail auto-save, will retry next interval

    def _save_internal(self) -> None:
        """Internal save method (assumes lock is held)."""
        self._persistence.save(self._graph, self.graph_path)
        self._dirty = False
        self._last_save_time = time.time()

    def _mark_dirty(self) -> None:
        """Mark graph as dirty (needs save)."""
        with self._lock:
            self._dirty = True
            self._graph.updated_at = datetime.now(UTC).isoformat()
            self._graph.version += 1

    # ============================================================
    # Core Node Operations
    # ============================================================

    def add_node(
        self,
        node_type: GraphNodeType,
        label: str,
        properties: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        embedding: list[float] | None = None,
        node_id: str | None = None,
    ) -> GraphNode:
        """
        Add a node to the knowledge graph.
        
        Args:
            node_type: Type of the node
            label: Human-readable label
            properties: Custom properties dict
            tags: List of tags for categorization
            embedding: Optional embedding vector for semantic search
            node_id: Optional custom node ID (auto-generated if not provided)
            
        Returns:
            The created GraphNode
        """
        with self._lock:
            node = GraphNode(
                id=node_id or uuid4().hex[:12],
                node_type=node_type,
                label=label,
                properties=properties or {},
                tags=tags or [],
                embedding=embedding,
            )
            self._graph.add_node(node)
            self._mark_dirty()
            return node

    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        with self._lock:
            return self._graph.get_node(node_id)

    def update_node(
        self,
        node_id: str,
        properties: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        embedding: list[float] | None = None,
        label: str | None = None,
    ) -> GraphNode | None:
        """Update an existing node."""
        with self._lock:
            node = self._graph.get_node(node_id)
            if not node:
                return None
            
            if label is not None:
                node.label = label
            if properties is not None:
                node.properties.update(properties)
            if tags is not None:
                node.tags = tags
            if embedding is not None:
                node.embedding = embedding
            
            node.touch()
            self._mark_dirty()
            return node

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges."""
        with self._lock:
            result = self._graph.remove_node(node_id)
            if result:
                self._mark_dirty()
            return result

    # ============================================================
    # Core Edge Operations
    # ============================================================

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: GraphEdgeType,
        weight: float = 1.0,
        confidence: float = 1.0,
        properties: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        created_by: str = "",
        edge_id: str | None = None,
    ) -> GraphEdge:
        """
        Add an edge (relationship) between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Type of relationship
            weight: Relationship strength (0.0 to 1.0)
            confidence: Confidence in relationship (0.0 to 1.0)
            properties: Custom properties
            tags: Tags for categorization
            created_by: Agent/system that created this edge
            edge_id: Optional custom edge ID
            
        Returns:
            The created GraphEdge
            
        Raises:
            ValueError: If source or target node doesn't exist
        """
        with self._lock:
            # Validate nodes exist
            if source_id not in self._graph.nodes:
                raise ValueError(f"Source node {source_id} not found")
            if target_id not in self._graph.nodes:
                raise ValueError(f"Target node {target_id} not found")
            
            edge = GraphEdge(
                id=edge_id or uuid4().hex[:12],
                edge_type=edge_type,
                source_id=source_id,
                target_id=target_id,
                properties=properties or {},
                weight=max(0.0, min(1.0, weight)),
                confidence=max(0.0, min(1.0, confidence)),
                tags=tags or [],
                created_by=created_by,
            )
            self._graph.add_edge(edge)
            self._mark_dirty()
            return edge

    def get_edge(self, edge_id: str) -> GraphEdge | None:
        """Get an edge by ID."""
        with self._lock:
            return self._graph.get_edge(edge_id)

    def update_edge(
        self,
        edge_id: str,
        weight: float | None = None,
        confidence: float | None = None,
        properties: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> GraphEdge | None:
        """Update an existing edge."""
        with self._lock:
            edge = self._graph.get_edge(edge_id)
            if not edge:
                return None
            
            if weight is not None:
                edge.weight = max(0.0, min(1.0, weight))
            if confidence is not None:
                edge.confidence = max(0.0, min(1.0, confidence))
            if properties is not None:
                edge.properties.update(properties)
            if tags is not None:
                edge.tags = tags
            
            edge.touch()
            self._mark_dirty()
            return edge

    def remove_edge(self, edge_id: str) -> bool:
        """Remove an edge by ID."""
        with self._lock:
            result = self._graph.remove_edge(edge_id)
            if result:
                self._mark_dirty()
            return result

    # ============================================================
    # Query Operations
    # ============================================================

    def get_neighbors(
        self,
        node_id: str,
        edge_types: list[GraphEdgeType] | None = None,
        max_depth: int = 1,
        direction: str = TraversalDirection.BOTH,
    ) -> list[GraphNode]:
        """
        Get neighbor nodes within max_depth.
        
        Args:
            node_id: Starting node ID
            edge_types: Filter by edge types (None = all)
            max_depth: Maximum traversal depth
            direction: Traversal direction (outgoing, incoming, both)
            
        Returns:
            List of neighbor nodes
        """
        with self._lock:
            if max_depth <= 0:
                return []
            
            if node_id not in self._graph.nodes:
                return []
            
            visited = {node_id}
            current_level = {node_id}
            all_neighbors = []
            
            for depth in range(max_depth):
                next_level = set()
                for current_id in current_level:
                    edges = []
                    if direction in (TraversalDirection.OUTGOING, TraversalDirection.BOTH):
                        edges.extend(self._graph.get_outgoing_edges(current_id))
                    if direction in (TraversalDirection.INCOMING, TraversalDirection.BOTH):
                        edges.extend(self._graph.get_incoming_edges(current_id))
                    
                    for edge in edges:
                        if edge_types and edge.edge_type not in edge_types:
                            continue
                        
                        neighbor_id = edge.target_id if edge.source_id == current_id else edge.source_id
                        if neighbor_id not in visited:
                            visited.add(neighbor_id)
                            next_level.add(neighbor_id)
                            neighbor = self._graph.get_node(neighbor_id)
                            if neighbor:
                                all_neighbors.append(neighbor)
                
                current_level = next_level
                if not current_level:
                    break
            
            return all_neighbors

    def search_nodes(
        self,
        query: str,
        node_types: list[GraphNodeType] | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
        min_score: float = 0.0,
    ) -> list[tuple[GraphNode, float]]:
        """
        Text-based search for nodes by label, properties, or tags.
        
        Args:
            query: Search query string
            node_types: Filter by node types
            tags: Filter by tags (must have ALL tags)
            limit: Maximum results
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of (node, score) tuples sorted by score descending
        """
        with self._lock:
            query_lower = query.lower()
            results = []
            
            for node in self._graph.nodes.values():
                # Filter by node type
                if node_types and node.node_type not in node_types:
                    continue
                
                # Filter by tags (must have ALL specified tags)
                if tags and not all(tag in node.tags for tag in tags):
                    continue
                
                # Calculate text similarity score
                score = 0.0
                
                # Label match
                if query_lower in node.label.lower():
                    score += 0.5
                elif any(word in node.label.lower() for word in query_lower.split()):
                    score += 0.3
                
                # Tag matches
                tag_matches = sum(1 for tag in node.tags if query_lower in tag.lower())
                if tag_matches:
                    score += min(0.3, tag_matches * 0.1)
                
                # Property value matches
                prop_matches = 0
                for value in node.properties.values():
                    if isinstance(value, str) and query_lower in value.lower():
                        prop_matches += 1
                if prop_matches:
                    score += min(0.2, prop_matches * 0.05)
                
                if score >= min_score:
                    results.append((node, score))
            
            # Sort by score descending
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]

    def semantic_search(
        self,
        embedding: list[float],
        k: int = 10,
        node_types: list[GraphNodeType] | None = None,
        min_similarity: float = 0.0,
    ) -> list[tuple[GraphNode, float]]:
        """
        Vector similarity search using node embeddings.
        
        Args:
            embedding: Query embedding vector
            k: Number of results to return
            node_types: Filter by node types
            min_similarity: Minimum cosine similarity (0-1)
            
        Returns:
            List of (node, similarity) tuples sorted by similarity descending
        """
        import numpy as np
        
        with self._lock:
            query_vec = np.array(embedding, dtype=np.float32)
            query_norm = np.linalg.norm(query_vec)
            
            if query_norm == 0:
                return []
            
            query_vec = query_vec / query_norm
            results = []
            
            for node in self._graph.nodes.values():
                if node_types and node.node_type not in node_types:
                    continue
                if node.embedding is None:
                    continue
                
                node_vec = np.array(node.embedding, dtype=np.float32)
                node_norm = np.linalg.norm(node_vec)
                if node_norm == 0:
                    continue
                
                similarity = float(np.dot(query_vec, node_vec / node_norm))
                if similarity >= min_similarity:
                    results.append((node, similarity))
            
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:k]

    def traverse(
        self,
        start_id: str,
        edge_types: list[GraphEdgeType] | None = None,
        max_depth: int = 3,
        direction: str = TraversalDirection.BOTH,
        max_nodes: int = 100,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """
        Graph traversal from a starting node.
        
        Args:
            start_id: Starting node ID
            edge_types: Filter by edge types
            max_depth: Maximum traversal depth
            direction: Traversal direction
            max_nodes: Maximum nodes to visit
            
        Returns:
            Tuple of (visited_nodes, traversed_edges)
        """
        with self._lock:
            if start_id not in self._graph.nodes:
                return [], []
            
            visited_nodes = {start_id: self._graph.nodes[start_id]}
            visited_edges = {}
            current_level = {start_id}
            
            for depth in range(max_depth):
                if len(visited_nodes) >= max_nodes:
                    break
                
                next_level = set()
                
                for current_id in current_level:
                    edges = []
                    if direction in (TraversalDirection.OUTGOING, TraversalDirection.BOTH):
                        edges.extend(self._graph.get_outgoing_edges(current_id))
                    if direction in (TraversalDirection.INCOMING, TraversalDirection.BOTH):
                        edges.extend(self._graph.get_incoming_edges(current_id))
                    
                    for edge in edges:
                        if edge_types and edge.edge_type not in edge_types:
                            continue
                        
                        neighbor_id = edge.target_id if edge.source_id == current_id else edge.source_id
                        
                        if neighbor_id not in visited_nodes:
                            neighbor = self._graph.get_node(neighbor_id)
                            if neighbor:
                                visited_nodes[neighbor_id] = neighbor
                                next_level.add(neighbor_id)
                        
                        if edge.id not in visited_edges:
                            visited_edges[edge.id] = edge
                
                current_level = next_level
                if not current_level:
                    break
            
            return list(visited_nodes.values()), list(visited_edges.values())

    def get_subgraph(self, node_ids: list[str]) -> KnowledgeGraph:
        """
        Extract a subgraph containing only the specified nodes and their connecting edges.
        
        Args:
            node_ids: List of node IDs to include
            
        Returns:
            Subgraph KnowledgeGraph
        """
        with self._lock:
            return self._graph.get_subgraph(node_ids)

    def get_stats(self) -> dict:
        """Get graph statistics."""
        with self._lock:
            return self._graph.get_stats()

    # ============================================================
    # Persistence Operations
    # ============================================================

    def save(self) -> None:
        """Save the graph to persistence."""
        with self._lock:
            self._save_internal()

    def load(self) -> None:
        """Load the graph from persistence."""
        with self._lock:
            self._graph = self._persistence.load(self.graph_path)
            self._dirty = False
            self._last_save_time = time.time()

    def close(self) -> None:
        """Close the engine, saving if dirty and stopping auto-save."""
        if self.auto_save_interval > 0:
            self._stop_auto_save.set()
            if self._auto_save_thread:
                self._auto_save_thread.join(timeout=5.0)
        
        with self._lock:
            if self._dirty:
                self._save_internal()
            self._persistence = None
            self._graph = None

    def __enter__(self) -> "KnowledgeGraphEngine":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ============================================================
    # Properties
    # ============================================================

    @property
    def graph(self) -> KnowledgeGraph:
        """Get the underlying KnowledgeGraph (read-only access)."""
        return self._graph

    @property
    def node_count(self) -> int:
        """Get total node count."""
        with self._lock:
            return len(self._graph.nodes)

    @property
    def edge_count(self) -> int:
        """Get total edge count."""
        with self._lock:
            return len(self._graph.edges)

    @property
    def is_dirty(self) -> bool:
        """Check if graph has unsaved changes."""
        with self._lock:
            return self._dirty

    def __len__(self) -> int:
        """Return total node count."""
        return self.node_count