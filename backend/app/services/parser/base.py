import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from app.models.graph import (
    ArchitecturalLayer,
    EREntity,
    ERRelationship,
    GraphEdge,
    GraphNode,
    NodeType,
)


def detect_layer_from_path(rel_path: str, node_type: Optional[str] = None) -> str:
    """Heuristic classification of architectural layer based on file path and node type."""
    lower = rel_path.lower().replace("\\", "/")
    parts = lower.split("/")

    # Tests layer
    if any(p in ("tests", "test", "__tests__", "spec", "specs") for p in parts):
        return ArchitecturalLayer.TESTS.value
    if lower.endswith(("_test.py", "test_.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js", ".test.tsx")):
        return ArchitecturalLayer.TESTS.value

    # UI / Presentation layer
    if any(p in ("components", "views", "pages", "frontend", "ui", "templates", "client", "screens") for p in parts):
        return ArchitecturalLayer.UI.value
    if lower.endswith((".tsx", ".jsx", ".vue", ".svelte", ".html")):
        return ArchitecturalLayer.UI.value

    # API / Routing layer
    if node_type == NodeType.ROUTE.value:
        return ArchitecturalLayer.API.value
    if any(p in ("api", "routes", "endpoints", "controllers", "handlers", "router") for p in parts):
        return ArchitecturalLayer.API.value

    # Database / Data access layer
    if node_type == NodeType.MODEL.value:
        return ArchitecturalLayer.DATABASE.value
    if any(p in ("models", "entities", "schemas", "prisma", "migrations", "alembic", "sql") for p in parts):
        return ArchitecturalLayer.DATABASE.value
    if any(p in ("repositories", "data_access", "dao", "db", "database", "crud") for p in parts):
        return ArchitecturalLayer.DATA_ACCESS.value

    # Configuration layer
    if any(p in ("config", "settings", "envs", "conf") for p in parts):
        return ArchitecturalLayer.CONFIGURATION.value
    if any(name in parts[-1] for name in ("config", "settings", "env", "manifest", "dockerfile", "makefile")):
        return ArchitecturalLayer.CONFIGURATION.value

    # External integrations
    if any(p in ("integrations", "clients", "external", "third_party", "sdk") for p in parts):
        return ArchitecturalLayer.EXTERNAL.value

    # Default to business logic for core services/logic
    return ArchitecturalLayer.BUSINESS_LOGIC.value


def create_node_id(rel_path: str, symbol_name: str) -> str:
    """Creates a deterministic, stable identifier for a code symbol."""
    norm_path = rel_path.replace("\\", "/")
    return f"{norm_path}::{symbol_name}"


def create_edge_id(source_id: str, target_id: str, edge_type: str) -> str:
    """Creates a deterministic, stable identifier for an edge."""
    return f"{source_id}->[{edge_type}]->{target_id}"


class BaseParser(ABC):
    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """Returns True if this parser supports the given file."""
        pass

    @abstractmethod
    def parse(
        self,
        file_path: Path,
        rel_path: str,
        content: str
    ) -> Tuple[List[GraphNode], List[GraphEdge], List[EREntity], List[ERRelationship]]:
        """
        Parses source code file and returns:
        - List of GraphNode
        - List of GraphEdge
        - List of EREntity (if database models/tables are detected)
        - List of ERRelationship
        """
        pass
