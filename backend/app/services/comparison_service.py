from typing import Any, Dict, List, Optional, Set, Tuple
from app.models.graph import (
    ArchitecturalLayer,
    EdgeType,
    EvidenceStatus,
    GraphEdge,
    GraphNode,
    NormalizedGraph,
    NodeType,
)
from app.services.impact_service import ImpactService


class ComparisonService:
    @staticmethod
    def compare_graphs(
        base_graph: NormalizedGraph,
        target_graph: NormalizedGraph,
        base_ref: str = "base",
        target_ref: str = "target"
    ) -> Dict[str, Any]:
        """
        Performs semantic diff comparison between two repository revision graphs.
        Detects added, modified, removed, and impacted components.
        """
        # Map nodes by semantic key: (file_path, label, type)
        def node_key(node: GraphNode) -> str:
            return f"{node.file_path}::{node.label}::{node.type}"

        base_map: Dict[str, GraphNode] = {node_key(n): n for n in base_graph.nodes}
        target_map: Dict[str, GraphNode] = {node_key(n): n for n in target_graph.nodes}

        base_keys = set(base_map.keys())
        target_keys = set(target_map.keys())

        added_keys = target_keys - base_keys
        removed_keys = base_keys - target_keys
        common_keys = base_keys & target_keys

        added_nodes: List[Dict[str, Any]] = []
        for k in added_keys:
            n = target_map[k]
            added_nodes.append({
                "id": n.id,
                "label": n.label,
                "type": n.type,
                "layer": n.layer,
                "file_path": n.file_path,
                "start_line": n.start_line,
                "change_type": "added"
            })

        removed_nodes: List[Dict[str, Any]] = []
        for k in removed_keys:
            n = base_map[k]
            removed_nodes.append({
                "id": n.id,
                "label": n.label,
                "type": n.type,
                "layer": n.layer,
                "file_path": n.file_path,
                "start_line": n.start_line,
                "change_type": "removed"
            })

        modified_nodes: List[Dict[str, Any]] = []
        unchanged_nodes: List[Dict[str, Any]] = []

        for k in common_keys:
            b_node = base_map[k]
            t_node = target_map[k]

            # Detect modification via line drift or content changes
            is_modified = (
                b_node.start_line != t_node.start_line or
                b_node.end_line != t_node.end_line or
                b_node.summary != t_node.summary
            )

            item = {
                "id": t_node.id,
                "label": t_node.label,
                "type": t_node.type,
                "layer": t_node.layer,
                "file_path": t_node.file_path,
                "start_line": t_node.start_line,
                "end_line": t_node.end_line,
            }

            if is_modified:
                item["change_type"] = "modified"
                modified_nodes.append(item)
            else:
                item["change_type"] = "unchanged"
                unchanged_nodes.append(item)

        # File-level differences
        base_files = {n.file_path for n in base_graph.nodes}
        target_files = {n.file_path for n in target_graph.nodes}

        added_files = sorted(list(target_files - base_files))
        deleted_files = sorted(list(base_files - target_files))
        modified_files = sorted(list({n["file_path"] for n in modified_nodes}))

        # Route and Schema changes
        changed_routes = [n for n in (added_nodes + modified_nodes + removed_nodes) if n["type"] == NodeType.ROUTE.value or n["layer"] == ArchitecturalLayer.API.value]
        changed_schemas = [n for n in (added_nodes + modified_nodes + removed_nodes) if n["type"] == NodeType.MODEL.value or n["layer"] == ArchitecturalLayer.DATABASE.value]
        changed_tests = [n for n in (added_nodes + modified_nodes + removed_nodes) if n["type"] == NodeType.TEST.value or n["layer"] == ArchitecturalLayer.TESTS.value]

        # Calculate potentially impacted components via downstream BFS
        changed_node_ids = {n["id"] for n in (added_nodes + modified_nodes)}
        impacted_node_ids: Set[str] = set()

        for node_id in changed_node_ids:
            if any(n.id == node_id for n in target_graph.nodes):
                res = ImpactService.analyze_change_impact(target_graph, node_id, max_depth=3)
                for d in res.direct_dependents:
                    impacted_node_ids.add(d.id)
                for t in res.transitive_dependents:
                    impacted_node_ids.add(t.id)

        # Remove directly changed nodes from impacted set
        impacted_node_ids -= changed_node_ids

        # Build combined overlay graph for visual rendering
        overlay_nodes: List[Dict[str, Any]] = []
        for n in target_graph.nodes:
            diff_status = "unchanged"
            if any(an["id"] == n.id for an in added_nodes):
                diff_status = "added"
            elif any(mn["id"] == n.id for mn in modified_nodes):
                diff_status = "modified"
            elif n.id in impacted_node_ids:
                diff_status = "impacted"

            overlay_nodes.append({
                "id": n.id,
                "label": n.label,
                "type": n.type,
                "layer": n.layer,
                "file_path": n.file_path,
                "diff_status": diff_status,
                "position_3d": {
                    "x": n.position_3d.x if n.position_3d else 0.0,
                    "y": n.position_3d.y if n.position_3d else 0.0,
                    "z": n.position_3d.z if n.position_3d else 0.0,
                } if n.position_3d else None,
                "position_2d": {
                    "x": n.position_2d.x if n.position_2d else 0.0,
                    "y": n.position_2d.y if n.position_2d else 0.0,
                } if n.position_2d else None,
            })

        return {
            "comparison_meta": {
                "base_ref": base_ref,
                "target_ref": target_ref,
                "total_base_nodes": len(base_graph.nodes),
                "total_target_nodes": len(target_graph.nodes),
            },
            "summary": {
                "added_count": len(added_nodes),
                "modified_count": len(modified_nodes),
                "removed_count": len(removed_nodes),
                "impacted_count": len(impacted_node_ids),
                "changed_files_count": len(added_files) + len(modified_files) + len(deleted_files),
            },
            "files": {
                "added": added_files,
                "modified": modified_files,
                "deleted": deleted_files,
            },
            "changes": {
                "added_symbols": added_nodes,
                "modified_symbols": modified_nodes,
                "removed_symbols": removed_nodes,
                "changed_routes": changed_routes,
                "changed_schemas": changed_schemas,
                "changed_tests": changed_tests,
                "impacted_node_ids": list(impacted_node_ids),
            },
            "overlay_graph": {
                "nodes": overlay_nodes,
                "edges": target_graph.edges,
            }
        }
