import hashlib
from typing import Any, Dict, List
from app.models.graph import EvidenceStatus, NormalizedGraph


class GraphifyExporter:
    @staticmethod
    def export_graphify_json(graph: NormalizedGraph) -> Dict[str, Any]:
        """
        Converts the normalized RepoGraph codebase into Graphify-Labs standard knowledge graph schema
        (graphify-out/graph.json format compatible with Graphify v1 schema).
        """
        # Compute community numbers deterministically from node clusters/layers
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
            elif node.layer == "database":
                file_type = "concept"
            elif node.type == "module":
                file_type = "rationale"

            source_loc = f"L{node.start_line}" if node.start_line else "L1"

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
                    "position_3d": {
                        "x": node.position_3d.x if node.position_3d else 0.0,
                        "y": node.position_3d.y if node.position_3d else 0.0,
                        "z": node.position_3d.z if node.position_3d else 0.0,
                    } if node.position_3d else None
                }
            })

        edges_data: List[Dict[str, Any]] = []
        for edge in graph.edges:
            # Map edge relation to Graphify relations: calls | imports | uses | inherits | references
            relation = "references"
            if edge.type in ("calls", "imports", "inherits"):
                relation = edge.type
            elif edge.type in ("reads_from", "writes_to", "depends_on"):
                relation = "uses"

            # Confidence: EXTRACTED | INFERRED | AMBIGUOUS
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
                "evidence": edge.evidence
            })

        return {
            "schema_version": "1",
            "graphify_version": "0.9.4",
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
