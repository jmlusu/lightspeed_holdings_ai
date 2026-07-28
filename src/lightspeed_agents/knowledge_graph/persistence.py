import json
import csv
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from datetime import datetime

from lightspeed_agents.knowledge_graph.models import (
    KnowledgeGraph,
    GraphNode,
    GraphEdge,
    GraphNodeType,
    GraphEdgeType,
)


class GraphPersistence(ABC):
    """Abstract base class for graph persistence backends."""

    @abstractmethod
    def save(self, graph: KnowledgeGraph, path: str) -> None:
        """Save a knowledge graph to storage."""
        pass

    @abstractmethod
    def load(self, path: str) -> KnowledgeGraph:
        """Load a knowledge graph from storage."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a graph exists at the given path."""
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        """Delete a graph from storage."""
        pass


class JSONGraphPersistence(GraphPersistence):
    """JSON file-based persistence for knowledge graphs."""

    def save(self, graph: KnowledgeGraph, path: str) -> None:
        """Save graph as JSON files (nodes.json, edges.json, meta.json)."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save metadata
        meta = {
            "id": graph.id,
            "name": graph.name,
            "created_at": graph.created_at,
            "updated_at": graph.updated_at,
            "version": graph.version,
            "metadata": graph.metadata,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
        }
        with open(path / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        # Save nodes
        nodes_data = [node.model_dump() for node in graph.nodes.values()]
        with open(path / "nodes.json", "w", encoding="utf-8") as f:
            json.dump(nodes_data, f, indent=2)

        # Save edges
        edges_data = [edge.model_dump() for edge in graph.edges.values()]
        with open(path / "edges.json", "w", encoding="utf-8") as f:
            json.dump(edges_data, f, indent=2)

    def load(self, path: str) -> KnowledgeGraph:
        """Load graph from JSON files."""
        path = Path(path)

        if not self.exists(path):
            raise FileNotFoundError(f"Graph not found at {path}")

        # Load metadata
        with open(path / "meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        graph = KnowledgeGraph(
            id=meta["id"],
            name=meta["name"],
            created_at=meta["created_at"],
            updated_at=meta["updated_at"],
            version=meta["version"],
            metadata=meta.get("metadata", {}),
        )

        # Load nodes
        with open(path / "nodes.json", "r", encoding="utf-8") as f:
            nodes_data = json.load(f)
        for node_data in nodes_data:
            node = GraphNode(**node_data)
            graph.nodes[node.id] = node

        # Load edges
        with open(path / "edges.json", "r", encoding="utf-8") as f:
            edges_data = json.load(f)
        for edge_data in edges_data:
            edge = GraphEdge(**edge_data)
            graph.edges[edge.id] = edge

        return graph

    def exists(self, path: str) -> bool:
        """Check if graph files exist."""
        path = Path(path)
        return (
            (path / "meta.json").exists()
            and (path / "nodes.json").exists()
            and (path / "edges.json").exists()
        )

    def delete(self, path: str) -> None:
        """Delete graph files."""
        path = Path(path)
        for fname in ["meta.json", "nodes.json", "edges.json"]:
            fpath = path / fname
            if fpath.exists():
                fpath.unlink()


class CSVGraphPersistence(GraphPersistence):
    """CSV file-based persistence for knowledge graphs (good for analytics/import)."""

    def save(self, graph: KnowledgeGraph, path: str) -> None:
        """Save graph as CSV files."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save nodes CSV
        if graph.nodes:
            nodes_file = path / "nodes.csv"
            fieldnames = [
                "id", "node_type", "label", "tags", "created_at", "updated_at",
                "version", "embedding"
            ] + [f"prop_{k}" for node in graph.nodes.values() for k in node.properties.keys()]
            fieldnames = list(dict.fromkeys(fieldnames))  # Remove duplicates while preserving order

            with open(nodes_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for node in graph.nodes.values():
                    row = {
                        "id": node.id,
                        "node_type": node.node_type.value,
                        "label": node.label,
                        "tags": "|".join(node.tags),
                        "created_at": node.created_at,
                        "updated_at": node.updated_at,
                        "version": node.version,
                        "embedding": json.dumps(node.embedding) if node.embedding else "",
                    }
                    # Add properties as columns
                    for k, v in node.properties.items():
                        row[f"prop_{k}"] = json.dumps(v) if not isinstance(v, (str, int, float, bool)) else v
                    for k, v in node.metadata.items():
                        row[f"meta_{k}"] = json.dumps(v) if not isinstance(v, (str, int, float, bool)) else v
                    writer.writerow(row)

        # Save edges CSV
        if graph.edges:
            edges_file = path / "edges.csv"
            fieldnames = [
                "id", "edge_type", "source_id", "target_id",
                "weight", "confidence", "tags", "created_at", "updated_at",
                "version", "created_by"
            ] + [f"prop_{k}" for edge in graph.edges.values() for k in edge.properties.keys()]
            fieldnames = list(dict.fromkeys(fieldnames))

            with open(edges_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for edge in graph.edges.values():
                    row = {
                        "id": edge.id,
                        "edge_type": edge.edge_type.value,
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "weight": edge.weight,
                        "confidence": edge.confidence,
                        "tags": "|".join(edge.tags),
                        "created_at": edge.created_at,
                        "updated_at": edge.updated_at,
                        "version": edge.version,
                        "created_by": edge.created_by,
                    }
                    for k, v in edge.properties.items():
                        row[f"prop_{k}"] = json.dumps(v) if not isinstance(v, (str, int, float, bool)) else v
                    for k, v in edge.metadata.items():
                        row[f"meta_{k}"] = json.dumps(v) if not isinstance(v, (str, int, float, bool)) else v
                    writer.writerow(row)

        # Save metadata
        meta = {
            "id": graph.id,
            "name": graph.name,
            "created_at": graph.created_at,
            "updated_at": graph.updated_at,
            "version": graph.version,
            "metadata": graph.metadata,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
        }
        with open(path / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def load(self, path: str) -> KnowledgeGraph:
        """Load graph from CSV files."""
        path = Path(path)

        if not self.exists(path):
            raise FileNotFoundError(f"Graph not found at {path}")

        # Load metadata
        with open(path / "meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        graph = KnowledgeGraph(
            id=meta["id"],
            name=meta["name"],
            created_at=meta["created_at"],
            updated_at=meta["updated_at"],
            version=meta["version"],
            metadata=meta.get("metadata", {}),
        )

        # Load nodes
        nodes_file = path / "nodes.csv"
        if nodes_file.exists():
            with open(nodes_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse properties and metadata
                    properties = {}
                    metadata = {}
                    for k, v in row.items():
                        if k.startswith("prop_"):
                            key = k[5:]
                            try:
                                properties[key] = json.loads(v)
                            except (json.JSONDecodeError, TypeError):
                                properties[key] = v
                        elif k.startswith("meta_"):
                            key = k[5:]
                            try:
                                metadata[key] = json.loads(v)
                            except (json.JSONDecodeError, TypeError):
                                metadata[key] = v

                    node = GraphNode(
                        id=row["id"],
                        node_type=GraphNodeType(row["node_type"]),
                        label=row["label"],
                        tags=row["tags"].split("|") if row["tags"] else [],
                        properties=properties,
                        metadata=metadata,
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        version=int(row["version"]),
                        embedding=json.loads(row["embedding"]) if row["embedding"] else None,
                    )
                    graph.nodes[node.id] = node

        # Load edges
        edges_file = path / "edges.csv"
        if edges_file.exists():
            with open(edges_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    properties = {}
                    metadata = {}
                    for k, v in row.items():
                        if k.startswith("prop_"):
                            key = k[5:]
                            try:
                                properties[key] = json.loads(v)
                            except (json.JSONDecodeError, TypeError):
                                properties[key] = v
                        elif k.startswith("meta_"):
                            key = k[5:]
                            try:
                                metadata[key] = json.loads(v)
                            except (json.JSONDecodeError, TypeError):
                                metadata[key] = v

                    edge = GraphEdge(
                        id=row["id"],
                        edge_type=GraphEdgeType(row["edge_type"]),
                        source_id=row["source_id"],
                        target_id=row["target_id"],
                        properties=properties,
                        metadata=metadata,
                        weight=float(row["weight"]),
                        confidence=float(row["confidence"]),
                        tags=row["tags"].split("|") if row["tags"] else [],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        version=int(row["version"]),
                        created_by=row["created_by"],
                    )
                    graph.edges[edge.id] = edge

        return graph

    def exists(self, path: str) -> bool:
        """Check if graph files exist."""
        path = Path(path)
        return (path / "meta.json").exists()

    def delete(self, path: str) -> None:
        """Delete graph files."""
        path = Path(path)
        for fname in ["meta.json", "nodes.csv", "edges.csv"]:
            fpath = path / fname
            if fpath.exists():
                fpath.unlink()


class GraphDBPersistence(GraphPersistence):
    """Base class for GraphDB persistence (Neo4j, Kuzu, etc.)."""

    def __init__(self, connection_string: str = "", **kwargs):
        self.connection_string = connection_string
        self.config = kwargs
        self._driver = None

    @abstractmethod
    def _connect(self):
        """Establish connection to graph database."""
        pass

    @abstractmethod
    def _close(self):
        """Close connection to graph database."""
        pass

    def save(self, graph: KnowledgeGraph, path: str) -> None:
        """Save graph to graph database."""
        # Path is used as graph name/database name in GraphDB
        self._connect()
        try:
            self._save_graph(graph, path)
        finally:
            self._close()

    def load(self, path: str) -> KnowledgeGraph:
        """Load graph from graph database."""
        self._connect()
        try:
            return self._load_graph(path)
        finally:
            self._close()

    def exists(self, path: str) -> bool:
        """Check if graph exists in database."""
        self._connect()
        try:
            return self._graph_exists(path)
        finally:
            self._close()

    def delete(self, path: str) -> None:
        """Delete graph from database."""
        self._connect()
        try:
            self._delete_graph(path)
        finally:
            self._close()

    @abstractmethod
    def _save_graph(self, graph: KnowledgeGraph, graph_name: str) -> None:
        pass

    @abstractmethod
    def _load_graph(self, graph_name: str) -> KnowledgeGraph:
        pass

    @abstractmethod
    def _graph_exists(self, graph_name: str) -> bool:
        pass

    @abstractmethod
    def _delete_graph(self, graph_name: str) -> None:
        pass


class KuzuGraphPersistence(GraphDBPersistence):
    """KuzuDB embedded graph database persistence."""

    def _connect(self):
        try:
            import kuzu
            self._db = kuzu.Database(self.connection_string or ":memory:")
            self._conn = kuzu.Connection(self._db)
        except ImportError:
            raise ImportError("KuzuDB not installed. Install with: pip install kuzu")

    def _close(self):
        if self._conn:
            self._conn.close()
        if self._db:
            self._db.close()

    def _save_graph(self, graph: KnowledgeGraph, graph_name: str) -> None:
        # Create schema
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {graph_name}_nodes (
                id STRING, node_type STRING, label STRING, tags STRING[],
                properties STRING, metadata STRING, created_at STRING,
                updated_at STRING, version INT64, embedding STRING,
                PRIMARY KEY (id)
            )
        """)
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {graph_name}_edges (
                id STRING, edge_type STRING, source_id STRING, target_id STRING,
                properties STRING, metadata STRING, weight DOUBLE,
                confidence DOUBLE, tags STRING[], created_at STRING,
                updated_at STRING, version INT64, created_by STRING,
                PRIMARY KEY (id)
            )
        """)

        # Insert nodes
        for node in graph.nodes.values():
            self._conn.execute(f"""
                INSERT INTO {graph_name}_nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                node.id, node.node_type.value, node.label,
                json.dumps(node.tags), json.dumps(node.properties),
                json.dumps(node.metadata), node.created_at,
                node.updated_at, node.version,
                json.dumps(node.embedding) if node.embedding else "[]"
            ])

        # Insert edges
        for edge in graph.edges.values():
            self._conn.execute(f"""
                INSERT INTO {graph_name}_edges VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                edge.id, edge.edge_type.value, edge.source_id, edge.target_id,
                json.dumps(edge.properties), json.dumps(edge.metadata),
                edge.weight, edge.confidence, json.dumps(edge.tags),
                edge.created_at, edge.updated_at, edge.version, edge.created_by
            ])

    def _load_graph(self, graph_name: str) -> KnowledgeGraph:
        graph = KnowledgeGraph(name=graph_name)

        # Load nodes
        result = self._conn.execute(f"SELECT * FROM {graph_name}_nodes")
        while result.has_next():
            row = result.get_next()
            node = GraphNode(
                id=row[0],
                node_type=GraphNodeType(row[1]),
                label=row[2],
                tags=json.loads(row[3]),
                properties=json.loads(row[4]),
                metadata=json.loads(row[5]),
                created_at=row[6],
                updated_at=row[7],
                version=row[8],
                embedding=json.loads(row[9]) if row[9] else None,
            )
            graph.nodes[node.id] = node

        # Load edges
        result = self._conn.execute(f"SELECT * FROM {graph_name}_edges")
        while result.has_next():
            row = result.get_next()
            edge = GraphEdge(
                id=row[0],
                edge_type=GraphEdgeType(row[1]),
                source_id=row[2],
                target_id=row[3],
                properties=json.loads(row[4]),
                metadata=json.loads(row[5]),
                weight=row[6],
                confidence=row[7],
                tags=json.loads(row[8]),
                created_at=row[9],
                updated_at=row[10],
                version=row[11],
                created_by=row[12],
            )
            graph.edges[edge.id] = edge

        return graph

    def _graph_exists(self, graph_name: str) -> bool:
        try:
            self._conn.execute(f"SELECT 1 FROM {graph_name}_nodes LIMIT 1")
            return True
        except Exception:
            return False

    def _delete_graph(self, graph_name: str) -> None:
        self._conn.execute(f"DROP TABLE IF EXISTS {graph_name}_nodes")
        self._conn.execute(f"DROP TABLE IF EXISTS {graph_name}_edges")


def get_persistence(backend: str = "json", **kwargs) -> GraphPersistence:
    """Factory function to get persistence backend."""
    backends = {
        "json": JSONGraphPersistence,
        "csv": CSVGraphPersistence,
        "kuzu": KuzuGraphPersistence,
    }
    if backend not in backends:
        raise ValueError(f"Unknown persistence backend: {backend}. Available: {list(backends.keys())}")
    return backends[backend](**kwargs)