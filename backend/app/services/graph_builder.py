import hashlib
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from app.models.graph import (
    ArchitecturalLayer,
    EdgeType,
    ERDiagramData,
    EREntity,
    ERRelationship,
    EvidenceStatus,
    FileItem,
    GraphEdge,
    GraphNode,
    GraphSummary,
    NormalizedGraph,
    Position2D,
    Position3D,
)

# Layer elevation (Z-depth) in the 3D Universe
LAYER_Z_OFFSETS: Dict[str, float] = {
    ArchitecturalLayer.UI.value: 36.0,
    ArchitecturalLayer.API.value: 20.0,
    ArchitecturalLayer.BUSINESS_LOGIC.value: 0.0,
    ArchitecturalLayer.DATA_ACCESS.value: -20.0,
    ArchitecturalLayer.DATABASE.value: -36.0,
    ArchitecturalLayer.CONFIGURATION.value: 12.0,
    ArchitecturalLayer.TESTS.value: -12.0,
    ArchitecturalLayer.EXTERNAL.value: -50.0,
}

# Layer vertical position (Y-offset) for the 2D Graph
LAYER_2D_Y_OFFSETS: Dict[str, float] = {
    ArchitecturalLayer.UI.value: 0.0,
    ArchitecturalLayer.API.value: 220.0,
    ArchitecturalLayer.BUSINESS_LOGIC.value: 480.0,
    ArchitecturalLayer.DATA_ACCESS.value: 740.0,
    ArchitecturalLayer.DATABASE.value: 980.0,
    ArchitecturalLayer.CONFIGURATION.value: 280.0,
    ArchitecturalLayer.TESTS.value: 600.0,
    ArchitecturalLayer.EXTERNAL.value: 1200.0,
}


def deterministic_seed(string_val: str) -> float:
    """Returns a deterministic pseudo-random float [0, 1) based on md5 hash."""
    h = hashlib.md5(string_val.encode("utf-8")).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


class GraphBuilder:
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.edge_keys: Set[str] = set()
        self.er_entities: List[EREntity] = []
        self.er_relationships: List[ERRelationship] = []
        self.files_map: Dict[str, Dict[str, Any]] = {}
        self.warnings: List[str] = []

    def add_parsed_results(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        er_entities: List[EREntity],
        er_relationships: List[ERRelationship],
        rel_path: str,
        size_bytes: int,
        language: str
    ) -> None:
        norm_path = rel_path.replace("\\", "/")
        self.files_map[norm_path] = {
            "size_bytes": size_bytes,
            "language": language,
            "node_count": len(nodes),
        }

        for node in nodes:
            self.nodes[node.id] = node

        for edge in edges:
            if edge.id not in self.edge_keys:
                self.edge_keys.add(edge.id)
                self.edges.append(edge)

        self.er_entities.extend(er_entities)
        self.er_relationships.extend(er_relationships)

    def build_normalized_graph(self) -> Tuple[NormalizedGraph, ERDiagramData, FileItem]:
        """Resolves cross-node links, computes 3D/2D layouts, and creates tree/ER views."""
        self._resolve_edges()
        self._compute_3d_layout()
        self._compute_2d_layout()

        summary = self._compute_summary()
        normalized_graph = NormalizedGraph(
            nodes=list(self.nodes.values()),
            edges=self.edges,
            summary=summary
        )

        er_diagram = self._build_er_diagram_data()
        file_tree = self._build_file_tree()

        return normalized_graph, er_diagram, file_tree

    def _resolve_edges(self) -> None:
        """Attempts to link unresolved import/call targets to concrete nodes in the repo."""
        label_to_id: Dict[str, str] = {}
        path_to_file_id: Dict[str, str] = {}

        for node_id, node in self.nodes.items():
            label_to_id[node.label] = node_id
            if node.type == "file":
                path_to_file_id[node.file_path] = node_id

        resolved_edges: List[GraphEdge] = []
        for edge in self.edges:
            # If target exists directly in nodes
            if edge.target in self.nodes:
                resolved_edges.append(edge)
                continue

            # Check if target matches another node label (e.g. class or function name)
            target_cleaned = edge.target.replace("external::", "").replace("import::", "")
            simple_name = target_cleaned.split(".")[-1].split("::")[-1]

            if simple_name in label_to_id:
                concrete_id = label_to_id[simple_name]
                edge.target = concrete_id
                edge.confidence = 0.85
                edge.evidence_status = EvidenceStatus.INFERRED.value
                resolved_edges.append(edge)
            else:
                # Keep as external dependency reference
                resolved_edges.append(edge)

        self.edges = resolved_edges

    def _compute_3d_layout(self) -> None:
        """Deterministic 3D placement by architectural layer and module clustering."""
        layer_groups: Dict[str, List[GraphNode]] = {}
        for node in self.nodes.values():
            layer_groups.setdefault(node.layer, []).append(node)

        for layer_name, nodes_in_layer in layer_groups.items():
            z = LAYER_Z_OFFSETS.get(layer_name, 0.0)

            # Group by cluster (subfolder or module)
            clusters: Dict[str, List[GraphNode]] = {}
            for node in nodes_in_layer:
                cluster_key = node.cluster or "root"
                clusters.setdefault(cluster_key, []).append(node)

            cluster_names = sorted(clusters.keys())
            num_clusters = len(cluster_names)

            for c_idx, c_name in enumerate(cluster_names):
                c_nodes = clusters[c_name]
                # Center of this cluster on the XY plane
                c_angle = (2 * math.pi * c_idx) / max(1, num_clusters)
                c_radius = 24.0 + 8.0 * math.sqrt(num_clusters)
                cluster_cx = math.cos(c_angle) * c_radius
                cluster_cy = math.sin(c_angle) * c_radius

                num_in_cluster = len(c_nodes)
                for n_idx, node in enumerate(c_nodes):
                    # Deterministic circular positioning inside cluster
                    if num_in_cluster == 1:
                        node.position_3d = Position3D(x=round(cluster_cx, 2), y=round(cluster_cy, 2), z=round(z, 2))
                    else:
                        node_angle = (2 * math.pi * n_idx) / num_in_cluster
                        node_r = 4.0 + 1.8 * math.sqrt(n_idx)
                        nx = cluster_cx + math.cos(node_angle) * node_r
                        ny = cluster_cy + math.sin(node_angle) * node_r
                        node.position_3d = Position3D(x=round(nx, 2), y=round(ny, 2), z=round(z, 2))

    def _compute_2d_layout(self) -> None:
        """Deterministic 2D placement for @xyflow/react layered graph."""
        layer_groups: Dict[str, List[GraphNode]] = {}
        for node in self.nodes.values():
            layer_groups.setdefault(node.layer, []).append(node)

        for layer_name, nodes_in_layer in layer_groups.items():
            y_base = LAYER_2D_Y_OFFSETS.get(layer_name, 400.0)
            sorted_nodes = sorted(nodes_in_layer, key=lambda n: (n.cluster or "", n.label))
            total = len(sorted_nodes)

            row_width = min(1200.0, max(600.0, total * 180.0))
            for idx, node in enumerate(sorted_nodes):
                cols_per_row = 6
                row = idx // cols_per_row
                col = idx % cols_per_row
                x = col * 220.0 - 500.0
                y = y_base + row * 110.0
                node.position_2d = Position2D(x=round(x, 1), y=round(y, 1))

    def _compute_summary(self) -> GraphSummary:
        lang_counts: Dict[str, int] = {}
        layer_counts: Dict[str, int] = {}

        for info in self.files_map.values():
            lang = info.get("language") or "unknown"
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        for node in self.nodes.values():
            layer_counts[node.layer] = layer_counts.get(node.layer, 0) + 1

        return GraphSummary(
            total_files=len(self.files_map),
            total_nodes=len(self.nodes),
            total_edges=len(self.edges),
            languages=lang_counts,
            layers=layer_counts,
            warnings=self.warnings
        )

    def _build_er_diagram_data(self) -> ERDiagramData:
        has_evidence = len(self.er_entities) > 0
        summary_text = (
            f"Detected {len(self.er_entities)} database entities and {len(self.er_relationships)} relations "
            f"from parsed models/tables."
            if has_evidence else
            "No database entities detected in this codebase. RepoGraph inspects SQLAlchemy, Prisma, "
            "Django models, and SQL DDL declarations."
        )
        return ERDiagramData(
            has_database_evidence=has_evidence,
            detection_summary=summary_text,
            entities=self.er_entities,
            relationships=self.er_relationships
        )

    def _build_file_tree(self) -> FileItem:
        """Converts files map into a hierarchical file tree structure."""
        root = FileItem(
            path="",
            name="repository_root",
            is_directory=True,
            children=[]
        )

        for rel_path, info in sorted(self.files_map.items()):
            parts = rel_path.split("/")
            curr = root
            accum_path = ""
            for i, part in enumerate(parts):
                accum_path = f"{accum_path}/{part}" if accum_path else part
                is_last = (i == len(parts) - 1)

                if curr.children is None:
                    curr.children = []

                # Find child or create
                child = next((c for c in curr.children if c.name == part), None)
                if not child:
                    child = FileItem(
                        path=accum_path,
                        name=part,
                        is_directory=not is_last,
                        size_bytes=info.get("size_bytes", 0) if is_last else 0,
                        language=info.get("language") if is_last else None,
                        layer=ArchitecturalLayer.BUSINESS_LOGIC.value,
                        node_count=info.get("node_count", 0) if is_last else 0,
                        children=[] if not is_last else None
                    )
                    curr.children.append(child)
                curr = child

        return root
