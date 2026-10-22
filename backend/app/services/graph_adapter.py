import hashlib
from typing import Any, Dict, List, Optional
from app.models.graph import (
    ArchitecturalLayer,
    EdgeType,
    EvidenceStatus,
    GraphEdge,
    GraphNode,
    NormalizedGraph,
    NodeType,
    Position2D,
    Position3D,
)
from app.services.graph_builder import GraphBuilder


class GraphAdapter:
    """
    Formal bidirectional adapter between Graphify-Labs knowledge graph schema
    and RepoGraph's NormalizedGraph internal representation.
    Preserves:
    - Stable node identities
    - Semantic types (classes, functions, routes, models, tables)
    - File and line evidence
    - Confidence and evidence status (VERIFIED/EXTRACTED, INFERRED, UNKNOWN/AMBIGUOUS)
    - Provenance and relationship metadata
    """

    GRAPHIFY_SCHEMA_VERSION = "1"
    GRAPHIFY_VERSION = "0.9.4"

    @classmethod
    def to_graphify_schema(cls, graph: NormalizedGraph) -> Dict[str, Any]:
        """Converts NormalizedGraph to Graphify v1 schema (graphify-out/graph.json format)."""
        clusters: Dict[str, int] = {}
        curr_community = 1

        nodes_data: List[Dict[str, Any]] = []
        for node in graph.nodes:
            cluster_key = node.cluster or node.layer or "default"
            if cluster_key not in clusters:
                clusters[cluster_key] = curr_community
                curr_community += 1

            community_id = clusters[cluster_key]

            # Map to Graphify file_type: code | document | paper | image | rationale | concept
            file_type = "code"
            if node.type in ("config", "test"):
                file_type = "document"
            elif node.layer == ArchitecturalLayer.DATABASE.value:
                file_type = "concept"
            elif node.type == NodeType.MODULE.value:
                file_type = "rationale"

            source_loc = f"L{node.start_line}" if node.start_line else "L1"
            if node.end_line and node.end_line != node.start_line:
                source_loc = f"L{node.start_line}-L{node.end_line}"

            nodes_data.append({
                "id": node.id,
                "label": node.label,
                "source_file": node.file_path,
                "source_location": source_loc,
                "file_type": file_type,
                "summary": node.summary or f"{node.type} in {node.file_path}",
                "community": community_id,
                "metadata": {
                    "layer": node.layer,
                    "symbol_type": node.type,
                    "language": node.language,
                    "confidence": node.confidence,
                    "evidence_status": node.evidence_status,
                    "position_3d": {
                        "x": node.position_3d.x if node.position_3d else 0.0,
                        "y": node.position_3d.y if node.position_3d else 0.0,
                        "z": node.position_3d.z if node.position_3d else 0.0,
                    } if node.position_3d else None,
                    "position_2d": {
                        "x": node.position_2d.x if node.position_2d else 0.0,
                        "y": node.position_2d.y if node.position_2d else 0.0,
                    } if node.position_2d else None,
                }
            })

        edges_data: List[Dict[str, Any]] = []
        for edge in graph.edges:
            relation = "references"
            if edge.type in ("calls", "imports", "inherits", "contains"):
                relation = edge.type
            elif edge.type in ("reads_from", "writes_to", "depends_on"):
                relation = "uses"

            confidence = "EXTRACTED"
            if edge.evidence_status == EvidenceStatus.INFERRED.value:
                confidence = "INFERRED"
            elif edge.evidence_status == EvidenceStatus.UNKNOWN.value:
                confidence = "AMBIGUOUS"

            edges_data.append({
                "source": edge.source,
                "target": edge.target,
                "relation": relation,
                "confidence": confidence,
                "evidence": edge.evidence,
                "metadata": {
                    "edge_type": edge.type,
                    "source_file": edge.source_file,
                    "source_line": edge.source_line,
                    "weight": getattr(edge, "weight", 1.0),
                }
            })

        return {
            "schema_version": cls.GRAPHIFY_SCHEMA_VERSION,
            "graphify_version": cls.GRAPHIFY_VERSION,
            "generator": "RepoGraph-Graphify-Adapter",
            "directed": False,
            "metadata": {
                "total_nodes": len(nodes_data),
                "total_edges": len(edges_data),
                "total_communities": len(clusters),
                "source_analyzer": "RepoGraph Deterministic AST Engine",
                "sponsored_by": "Graphify-Labs/graphify"
            },
            "nodes": nodes_data,
            "edges": edges_data
        }

    @classmethod
    def from_graphify_schema(cls, data: Dict[str, Any]) -> NormalizedGraph:
        """Imports a Graphify knowledge graph dictionary back into a RepoGraph NormalizedGraph."""
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        for item in data.get("nodes", []):
            meta = item.get("metadata", {})
            pos_3d_dict = meta.get("position_3d")
            pos_2d_dict = meta.get("position_2d")

            pos_3d = Position3D(**pos_3d_dict) if pos_3d_dict else Position3D(x=0.0, y=0.0, z=0.0)
            pos_2d = Position2D(**pos_2d_dict) if pos_2d_dict else Position2D(x=0.0, y=0.0)

            layer_val = meta.get("layer") or ArchitecturalLayer.BUSINESS_LOGIC.value
            type_val = meta.get("symbol_type") or NodeType.FILE.value

            loc_str = item.get("source_location", "")
            start_line = 1
            end_line = 1
            if loc_str.startswith("L"):
                parts = loc_str[1:].split("-L")
                try:
                    start_line = int(parts[0])
                    end_line = int(parts[1]) if len(parts) > 1 else start_line
                except ValueError:
                    pass

            node = GraphNode(
                id=item["id"],
                label=item.get("label", item["id"]),
                type=type_val,
                file_path=item.get("source_file", "unknown"),
                start_line=start_line,
                end_line=end_line,
                language=meta.get("language", "python"),
                summary=item.get("summary", ""),
                layer=layer_val,
                cluster=f"community_{item.get('community', 1)}",
                confidence=meta.get("confidence", 1.0),
                evidence_status=meta.get("evidence_status", EvidenceStatus.VERIFIED.value),
                position_3d=pos_3d,
                position_2d=pos_2d
            )
            nodes.append(node)

        for edge_item in data.get("edges", []):
            edge_meta = edge_item.get("metadata", {})
            relation = edge_item.get("relation", "references")
            edge_type = edge_meta.get("edge_type") or relation

            conf_str = edge_item.get("confidence", "EXTRACTED")
            status = EvidenceStatus.VERIFIED.value
            if conf_str == "INFERRED":
                status = EvidenceStatus.INFERRED.value
            elif conf_str == "AMBIGUOUS":
                status = EvidenceStatus.UNKNOWN.value

            edge = GraphEdge(
                id=f"{edge_item['source']}->{edge_item['target']}::{edge_type}",
                source=edge_item["source"],
                target=edge_item["target"],
                type=edge_type,
                evidence=edge_item.get("evidence", f"{relation} relation"),
                source_file=edge_meta.get("source_file"),
                source_line=edge_meta.get("source_line"),
                evidence_status=status,
                weight=edge_meta.get("weight", 1.0)
            )
            edges.append(edge)

        # Build normalized graph with layers and clusters
        builder = GraphBuilder()
        builder.nodes = {n.id: n for n in nodes}
        builder.edges = edges
        norm_graph, _, _ = builder.build_normalized_graph()
        return norm_graph
