"""Tests for KnowledgeGraphEngine."""

import tempfile
import threading
import time
from pathlib import Path

import pytest
import numpy as np

from lightspeed_agents.knowledge_graph import (
    KnowledgeGraphEngine,
    GraphNodeType,
    GraphEdgeType,
    TraversalDirection,
)
from lightspeed_agents.knowledge_graph.models import GraphNode, GraphEdge, KnowledgeGraph


class TestKnowledgeGraphEngine:
    """Tests for KnowledgeGraphEngine."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def engine(self, temp_dir):
        """Create a KnowledgeGraphEngine instance for testing."""
        graph_path = temp_dir / "test_graph"
        engine = KnowledgeGraphEngine(
            persistence_backend="json",
            config={},
            auto_save_interval=0,  # Disable auto-save for tests
            graph_name="test_graph",
            graph_path=str(graph_path),
        )
        yield engine
        engine.close()

    @pytest.fixture
    def populated_engine(self, engine):
        """Create an engine with some test data."""
        # Add nodes
        agent = engine.add_node(GraphNodeType.AGENT, "Agent-001", {"role": "engineer"}, ["backend", "python"])
        task = engine.add_node(GraphNodeType.TASK, "Build API", {"priority": "high"}, ["api", "backend"])
        decision = engine.add_node(GraphNodeType.DECISION, "Use FastAPI", {"rationale": "fast, async"}, ["architecture"])
        doc = engine.add_node(GraphNodeType.DOCUMENT, "API Spec", {"format": "openapi"}, ["documentation"])
        
        # Add edges
        engine.add_edge(agent.id, task.id, GraphEdgeType.ASSIGNED_TO, weight=0.9, confidence=1.0, created_by="system")
        engine.add_edge(task.id, decision.id, GraphEdgeType.REQUIRES, weight=0.8, confidence=0.9, created_by="agent")
        engine.add_edge(decision.id, doc.id, GraphEdgeType.REFERENCES, weight=0.7, confidence=0.8, created_by="agent")
        
        engine.save()
        return engine

    # ============================================================
    # Node Operations Tests
    # ============================================================

    def test_add_node(self, engine):
        """Test adding a node."""
        node = engine.add_node(
            GraphNodeType.CONCEPT,
            "Test Concept",
            {"key": "value"},
            ["tag1", "tag2"],
            embedding=[0.1, 0.2, 0.3]
        )
        
        assert node is not None
        assert node.node_type == GraphNodeType.CONCEPT
        assert node.label == "Test Concept"
        assert node.properties == {"key": "value"}
        assert node.tags == ["tag1", "tag2"]
        assert node.embedding == [0.1, 0.2, 0.3]
        assert node.id is not None

    def test_get_node(self, engine, populated_engine):
        """Test getting a node by ID."""
        node = populated_engine.get_node(populated_engine.graph.nodes[list(populated_engine.graph.nodes.keys())[0]].id)
        assert node is not None
        
        # Non-existent node
        assert populated_engine.get_node("nonexistent") is None

    def test_update_node(self, engine, populated_engine):
        """Test updating a node."""
        node_id = list(populated_engine.graph.nodes.keys())[0]
        
        updated = populated_engine.update_node(
            node_id,
            label="Updated Label",
            properties={"new_key": "new_value"},
            tags=["new_tag"],
            embedding=[0.5, 0.5, 0.5]
        )
        
        assert updated is not None
        assert updated.label == "Updated Label"
        assert updated.properties["new_key"] == "new_value"
        assert updated.tags == ["new_tag"]
        assert updated.embedding == [0.5, 0.5, 0.5]

    def test_remove_node(self, engine, populated_engine):
        """Test removing a node."""
        node_id = list(populated_engine.graph.nodes.keys())[0]
        assert populated_engine.remove_node(node_id) is True
        assert populated_engine.get_node(node_id) is None
        
        # Removing non-existent should return False
        assert populated_engine.remove_node("nonexistent") is False

    def test_add_node_custom_id(self, engine):
        """Test adding a node with custom ID."""
        node = engine.add_node(GraphNodeType.AGENT, "Custom ID Agent", node_id="custom-id-123")
        assert node.id == "custom-id-123"

    # ============================================================
    # Edge Operations Tests
    # ============================================================

    def test_add_edge(self, engine):
        """Test adding an edge."""
        source = engine.add_node(GraphNodeType.AGENT, "Source")
        target = engine.add_node(GraphNodeType.TASK, "Target")
        
        edge = engine.add_edge(
            source.id, target.id,
            GraphEdgeType.ASSIGNED_TO,
            weight=0.8,
            confidence=0.9,
            properties={"note": "assigned by manager"},
            tags=["urgent"],
            created_by="manager"
        )
        
        assert edge is not None
        assert edge.source_id == source.id
        assert edge.target_id == target.id
        assert edge.edge_type == GraphEdgeType.ASSIGNED_TO
        assert edge.weight == 0.8
        assert edge.confidence == 0.9
        assert edge.properties == {"note": "assigned by manager"}
        assert edge.tags == ["urgent"]
        assert edge.created_by == "manager"

    def test_add_edge_invalid_nodes(self, engine):
        """Test adding edge with invalid nodes raises error."""
        with pytest.raises(ValueError, match="Source node.*not found"):
            engine.add_edge("nonexistent", "also_nonexistent", GraphEdgeType.RELATES_TO)

    def test_get_edge(self, engine):
        """Test getting an edge by ID."""
        source = engine.add_node(GraphNodeType.AGENT, "Source")
        target = engine.add_node(GraphNodeType.TASK, "Target")
        edge = engine.add_edge(source.id, target.id, GraphEdgeType.ASSIGNED_TO)
        
        retrieved = engine.get_edge(edge.id)
        assert retrieved is not None
        assert retrieved.id == edge.id
        
        assert engine.get_edge("nonexistent") is None

    def test_update_edge(self, engine):
        """Test updating an edge."""
        source = engine.add_node(GraphNodeType.AGENT, "Source")
        target = engine.add_node(GraphNodeType.TASK, "Target")
        edge = engine.add_edge(source.id, target.id, GraphEdgeType.ASSIGNED_TO, weight=0.5)
        
        updated = engine.update_edge(
            edge.id,
            weight=0.9,
            confidence=0.95,
            properties={"updated": True},
            tags=["modified"]
        )
        
        assert updated is not None
        assert updated.weight == 0.9
        assert updated.confidence == 0.95
        assert updated.properties == {"updated": True}
        assert updated.tags == ["modified"]

    def test_remove_edge(self, engine):
        """Test removing an edge."""
        source = engine.add_node(GraphNodeType.AGENT, "Source")
        target = engine.add_node(GraphNodeType.TASK, "Target")
        edge = engine.add_edge(source.id, target.id, GraphEdgeType.ASSIGNED_TO)
        
        assert engine.remove_edge(edge.id) is True
        assert engine.get_edge(edge.id) is None
        
        # Removing non-existent should return False
        assert engine.remove_edge("nonexistent") is False

    # ============================================================
    # Query Operations Tests
    # ============================================================

    def test_get_neighbors(self, populated_engine):
        """Test getting neighbors."""
        # Find the task node
        task_node = next(n for n in populated_engine.graph.nodes.values() if n.node_type == GraphNodeType.TASK)
        
        neighbors = populated_engine.get_neighbors(task_node.id)
        assert len(neighbors) >= 2  # Agent and Decision
        
        # Test with depth 2
        neighbors_depth2 = populated_engine.get_neighbors(task_node.id, max_depth=2)
        assert len(neighbors_depth2) >= 3  # Agent, Decision, Document

    def test_get_neighbors_with_edge_filter(self, populated_engine):
        """Test getting neighbors filtered by edge type."""
        task_node = next(n for n in populated_engine.graph.nodes.values() if n.node_type == GraphNodeType.TASK)
        
        # Only ASSIGNED_TO edges
        neighbors = populated_engine.get_neighbors(
            task_node.id,
            edge_types=[GraphEdgeType.ASSIGNED_TO],
            max_depth=1
        )
        # Should only find the agent
        agent_neighbors = [n for n in neighbors if n.node_type == GraphNodeType.AGENT]
        assert len(agent_neighbors) >= 1

    def test_search_nodes(self, populated_engine):
        """Test text-based node search."""
        results = populated_engine.search_nodes("API", limit=10)
        assert len(results) >= 1
        
        # Should find "Build API" task and "API Spec" document
        labels = [node.label for node, _ in results]
        assert "Build API" in labels or "API Spec" in labels
        
        # Test with node type filter
        task_results = populated_engine.search_nodes("API", node_types=[GraphNodeType.TASK])
        assert all(node.node_type == GraphNodeType.TASK for node, _ in task_results)

    def test_search_nodes_by_tags(self, populated_engine):
        """Test searching nodes by tags."""
        results = populated_engine.search_nodes("", tags=["backend"], limit=10)
        assert len(results) >= 1
        
        for node, _ in results:
            assert "backend" in node.tags

    def test_semantic_search(self, engine):
        """Test vector similarity search."""
        # Add nodes with embeddings
        node1 = engine.add_node(GraphNodeType.CONCEPT, "Vector A", embedding=[1.0, 0.0, 0.0])
        node2 = engine.add_node(GraphNodeType.CONCEPT, "Vector B", embedding=[0.0, 1.0, 0.0])
        node3 = engine.add_node(GraphNodeType.CONCEPT, "Vector C", embedding=[0.707, 0.707, 0.0])
        node4 = engine.add_node(GraphNodeType.CONCEPT, "No Embedding")  # No embedding
        
        # Search for vector similar to node1
        results = engine.semantic_search([1.0, 0.0, 0.0], k=3)
        assert len(results) == 3  # node4 has no embedding
        
        # First result should be node1 (exact match = similarity 1.0)
        assert results[0][0].id == node1.id
        assert results[0][1] == pytest.approx(1.0, abs=1e-5)
        
        # Third result should be node3 (similarity ~0.707)
        assert results[2][0].id == node3.id
        assert results[2][1] == pytest.approx(0.707, abs=0.01)

    def test_semantic_search_with_filters(self, engine):
        """Test semantic search with node type filter."""
        engine.add_node(GraphNodeType.CONCEPT, "Concept A", embedding=[1.0, 0.0])
        engine.add_node(GraphNodeType.AGENT, "Agent B", embedding=[0.0, 1.0])
        
        # Search only concepts
        results = engine.semantic_search([1.0, 0.0], k=5, node_types=[GraphNodeType.CONCEPT])
        assert len(results) == 1
        assert results[0][0].node_type == GraphNodeType.CONCEPT

    def test_traverse(self, populated_engine):
        """Test graph traversal."""
        # Find task node
        task_node = next(n for n in populated_engine.graph.nodes.values() if n.node_type == GraphNodeType.TASK)
        
        nodes, edges = populated_engine.traverse(task_node.id, max_depth=2)
        
        assert len(nodes) >= 3  # Task, Agent, Decision, Document
        assert len(edges) >= 2  # Assigned_To, Requires, References
        
        # Test with edge type filter
        nodes_filtered, edges_filtered = populated_engine.traverse(
            task_node.id,
            edge_types=[GraphEdgeType.ASSIGNED_TO],
            max_depth=2
        )
        assert len(nodes_filtered) == 2  # Task and Agent only

    def test_traverse_direction(self, populated_engine):
        """Test traversal with direction filter."""
        task_node = next(n for n in populated_engine.graph.nodes.values() if n.node_type == GraphNodeType.TASK)
        
        # Outgoing only (task -> decision)
        nodes_out, edges_out = populated_engine.traverse(
            task_node.id,
            direction=TraversalDirection.OUTGOING,
            max_depth=1
        )
        
        # Incoming only (agent -> task)
        nodes_in, edges_in = populated_engine.traverse(
            task_node.id,
            direction=TraversalDirection.INCOMING,
            max_depth=1
        )
        
        assert len(nodes_out) >= 1
        assert len(nodes_in) >= 1

    def test_get_subgraph(self, populated_engine):
        """Test subgraph extraction."""
        node_ids = list(populated_engine.graph.nodes.keys())[:2]
        subgraph = populated_engine.get_subgraph(node_ids)
        
        assert len(subgraph.nodes) == 2
        # Edges only if both nodes in subgraph are connected
        for edge in subgraph.edges.values():
            assert edge.source_id in node_ids
            assert edge.target_id in node_ids

    def test_get_stats(self, populated_engine):
        """Test graph statistics."""
        stats = populated_engine.get_stats()
        
        assert "node_count" in stats
        assert "edge_count" in stats
        assert "node_types" in stats
        assert "edge_types" in stats
        assert stats["node_count"] >= 4
        assert stats["edge_count"] >= 3

    # ============================================================
    # Persistence Tests
    # ============================================================

    def test_save_and_load(self, temp_dir):
        """Test saving and loading graph."""
        graph_path = temp_dir / "persist_test"
        
        # Create and populate engine
        engine1 = KnowledgeGraphEngine(
            persistence_backend="json",
            config={},
            auto_save_interval=0,
            graph_name="persist_test",
            graph_path=str(graph_path),
        )
        
        node1 = engine1.add_node(GraphNodeType.CONCEPT, "Persisted Concept", {"persisted": True})
        node2 = engine1.add_node(GraphNodeType.AGENT, "Persisted Agent")
        engine1.add_edge(node1.id, node2.id, GraphEdgeType.RELATES_TO)
        engine1.save()
        engine1.close()
        
        # Load into new engine
        engine2 = KnowledgeGraphEngine(
            persistence_backend="json",
            config={},
            auto_save_interval=0,
            graph_name="persist_test",
            graph_path=str(graph_path),
        )
        
        assert engine2.node_count == 2
        assert engine2.edge_count == 1
        
        loaded_node = engine2.get_node(node1.id)
        assert loaded_node is not None
        assert loaded_node.label == "Persisted Concept"
        assert loaded_node.properties["persisted"] is True
        
        engine2.close()

    def test_csv_persistence(self, temp_dir):
        """Test CSV persistence backend."""
        graph_path = temp_dir / "csv_test"
        
        engine = KnowledgeGraphEngine(
            persistence_backend="csv",
            config={},
            auto_save_interval=0,
            graph_name="csv_test",
            graph_path=str(graph_path),
        )
        
        node = engine.add_node(GraphNodeType.CONCEPT, "CSV Concept")
        engine.save()
        engine.close()
        
        # Verify CSV files exist
        assert (graph_path / "nodes.csv").exists()
        assert (graph_path / "edges.csv").exists()
        assert (graph_path / "meta.json").exists()
        
        # Load back
        engine2 = KnowledgeGraphEngine(
            persistence_backend="csv",
            config={},
            auto_save_interval=0,
            graph_name="csv_test",
            graph_path=str(graph_path),
        )
        
        assert engine2.node_count == 1
        engine2.close()

    def test_auto_save(self, temp_dir):
        """Test auto-save functionality."""
        graph_path = temp_dir / "auto_save_test"
        
        engine = KnowledgeGraphEngine(
            persistence_backend="json",
            config={},
            auto_save_interval=0.1,  # 100ms
            graph_name="auto_save_test",
            graph_path=str(graph_path),
        )
        
        node = engine.add_node(GraphNodeType.CONCEPT, "Auto Save Test")
        node_id = node.id
        
        # Wait for auto-save
        time.sleep(0.3)
        
        # Create new engine and verify data persisted
        engine.close()
        
        engine2 = KnowledgeGraphEngine(
            persistence_backend="json",
            config={},
            auto_save_interval=0,
            graph_name="auto_save_test",
            graph_path=str(graph_path),
        )
        
        loaded = engine2.get_node(node_id)
        assert loaded is not None
        assert loaded.label == "Auto Save Test"
        
        engine2.close()

    # ============================================================
    # Thread Safety Tests
    # ============================================================

    def test_thread_safety_add_nodes(self, engine):
        """Test thread-safe node addition."""
        def add_nodes(start_idx, count):
            for i in range(count):
                engine.add_node(GraphNodeType.CONCEPT, f"Thread Node {start_idx + i}")
        
        threads = [threading.Thread(target=add_nodes, args=(i * 10, 10)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert engine.node_count == 50

    def test_thread_safety_add_edges(self, engine):
        """Test thread-safe edge addition."""
        # Pre-create nodes
        node_ids = []
        for i in range(20):
            node = engine.add_node(GraphNodeType.CONCEPT, f"Node {i}")
            node_ids.append(node.id)
        
        def add_edges(start_idx):
            for i in range(start_idx, start_idx + 5):
                if i + 1 < len(node_ids):
                    engine.add_edge(node_ids[i], node_ids[i + 1], GraphEdgeType.RELATES_TO)
        
        threads = [threading.Thread(target=add_edges, args=(i * 2,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert engine.edge_count >= 10

    def test_thread_safety_concurrent_read_write(self, engine):
        """Test concurrent reads and writes."""
        results = {"reads": 0, "writes": 0, "errors": 0}
        
        def writer():
            try:
                for i in range(20):
                    engine.add_node(GraphNodeType.CONCEPT, f"Writer Node {i}")
                    time.sleep(0.001)
                results["writes"] += 1
            except Exception:
                results["errors"] += 1
        
        def reader():
            try:
                for _ in range(50):
                    _ = engine.node_count
                    _ = engine.get_stats()
                    time.sleep(0.001)
                results["reads"] += 1
            except Exception:
                results["errors"] += 1
        
        threads = [threading.Thread(target=writer) for _ in range(2)]
        threads += [threading.Thread(target=reader) for _ in range(3)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert results["errors"] == 0
        assert results["writes"] == 2
        assert results["reads"] == 3

    # ============================================================
    # Edge Cases and Properties Tests
    # ============================================================

    def test_weight_clamping(self, engine):
        """Test edge weight is clamped to [0, 1]."""
        source = engine.add_node(GraphNodeType.CONCEPT, "Source")
        target = engine.add_node(GraphNodeType.CONCEPT, "Target")
        
        edge = engine.add_edge(source.id, target.id, GraphEdgeType.RELATES_TO, weight=1.5)
        assert edge.weight == 1.0
        
        edge = engine.add_edge(source.id, target.id, GraphEdgeType.RELATES_TO, weight=-0.5)
        assert edge.weight == 0.0

    def test_confidence_clamping(self, engine):
        """Test edge confidence is clamped to [0, 1]."""
        source = engine.add_node(GraphNodeType.CONCEPT, "Source")
        target = engine.add_node(GraphNodeType.CONCEPT, "Target")
        
        edge = engine.add_edge(source.id, target.id, GraphEdgeType.RELATES_TO, confidence=1.5)
        assert edge.confidence == 1.0

    def test_node_version_increment(self, engine):
        """Test node version increments on update."""
        node = engine.add_node(GraphNodeType.CONCEPT, "Version Test")
        initial_version = node.version
        
        engine.update_node(node.id, properties={"updated": True})
        
        updated = engine.get_node(node.id)
        assert updated.version == initial_version + 1

    def test_edge_version_increment(self, engine):
        """Test edge version increments on update."""
        source = engine.add_node(GraphNodeType.CONCEPT, "Source")
        target = engine.add_node(GraphNodeType.CONCEPT, "Target")
        edge = engine.add_edge(source.id, target.id, GraphEdgeType.RELATES_TO)
        initial_version = edge.version
        
        engine.update_edge(edge.id, weight=0.5)
        
        updated = engine.get_edge(edge.id)
        assert updated.version == initial_version + 1

    def test_context_manager(self, temp_dir):
        """Test context manager usage."""
        graph_path = temp_dir / "context_test"
        
        with KnowledgeGraphEngine(
            persistence_backend="json",
            config={},
            auto_save_interval=0,
            graph_name="context_test",
            graph_path=str(graph_path),
        ) as engine:
            engine.add_node(GraphNodeType.CONCEPT, "Context Node")
        
        # Verify saved after context exit
        engine2 = KnowledgeGraphEngine(
            persistence_backend="json",
            config={},
            auto_save_interval=0,
            graph_name="context_test",
            graph_path=str(graph_path),
        )
        assert engine2.node_count == 1
        engine2.close()

    def test_is_dirty(self, engine):
        """Test dirty flag tracking."""
        assert engine.is_dirty is False
        
        engine.add_node(GraphNodeType.CONCEPT, "Dirty Test")
        assert engine.is_dirty is True
        
        engine.save()
        assert engine.is_dirty is False

    def test_len(self, engine):
        """Test len() returns node count."""
        assert len(engine) == 0
        
        engine.add_node(GraphNodeType.CONCEPT, "Node 1")
        assert len(engine) == 1
        
        engine.add_node(GraphNodeType.CONCEPT, "Node 2")
        assert len(engine) == 2

    def test_properties(self, populated_engine):
        """Test property accessors."""
        assert populated_engine.node_count >= 4
        assert populated_engine.edge_count >= 3
        assert isinstance(populated_engine.graph, KnowledgeGraph)

    # ============================================================
    # Traversal Direction Enum Tests
    # ============================================================

    def test_traversal_direction_constants(self):
        """Test traversal direction constants."""
        assert TraversalDirection.OUTGOING == "outgoing"
        assert TraversalDirection.INCOMING == "incoming"
        assert TraversalDirection.BOTH == "both"

    def test_empty_graph_operations(self, engine):
        """Test operations on empty graph."""
        assert engine.get_node("nonexistent") is None
        assert engine.get_edge("nonexistent") is None
        assert engine.get_neighbors("nonexistent") == []
        assert engine.search_nodes("anything") == []
        assert engine.semantic_search([0.1, 0.2], k=5) == []
        assert engine.traverse("nonexistent") == ([], [])
        assert engine.get_subgraph([]).nodes == {}
        stats = engine.get_stats()
        assert stats["node_count"] == 0
        assert stats["edge_count"] == 0


class TestTraversalDirection:
    """Tests for TraversalDirection enum."""

    def test_values(self):
        assert TraversalDirection.OUTGOING == "outgoing"
        assert TraversalDirection.INCOMING == "incoming"
        assert TraversalDirection.BOTH == "both"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])