from collections import deque
from typing import Any, Dict, List, Optional, Set
from app.models.graph import (
    ArchitecturalLayer,
    EdgeType,
    EvidenceStatus,
    GraphEdge,
    GraphNode,
    NormalizedGraph,
    NodeType,
)


class ApiFlowService:
    @staticmethod
    def get_api_routes(graph: NormalizedGraph) -> List[Dict[str, Any]]:
        """Identifies all API routes and endpoints in the normalized graph."""
        routes: List[Dict[str, Any]] = []

        for node in graph.nodes:
            if node.type == NodeType.ROUTE.value or (node.layer == ArchitecturalLayer.API.value and node.type == NodeType.FUNCTION.value):
                meta = node.metadata or {}
                http_method = meta.get("http_method") or "GET"
                route_path = meta.get("route_path") or f"/{node.label}"

                routes.append({
                    "id": node.id,
                    "label": node.label,
                    "http_method": http_method,
                    "route_path": route_path,
                    "file_path": node.file_path,
                    "start_line": node.start_line,
                    "end_line": node.end_line,
                    "summary": node.summary or f"Endpoint handler: {node.label}",
                    "confidence": node.confidence,
                })

        # Sort routes alphabetically by route_path
        routes.sort(key=lambda r: (r["route_path"], r["http_method"]))
        return routes

    @staticmethod
    def trace_api_flow(graph: NormalizedGraph, route_node_id: str, max_depth: int = 6) -> Dict[str, Any]:
        """
        Traces the downstream architecture chain for an API route:
        Route Entry -> Middleware/Auth -> Service/Logic -> Data Access -> Database Model/Table.
        """
        nodes_by_id: Dict[str, GraphNode] = {n.id: n for n in graph.nodes}
        if route_node_id not in nodes_by_id:
            return {
                "route": None,
                "flow_stages": [],
                "flow_nodes": [],
                "flow_edges": [],
                "disclaimer": f"Route '{route_node_id}' not found in graph."
            }

        route_node = nodes_by_id[route_node_id]

        # Build adjacency list (directed outgoing from route)
        adj: Dict[str, List[GraphEdge]] = {}
        for edge in graph.edges:
            adj.setdefault(edge.source, []).append(edge)

        visited: Set[str] = {route_node_id}
        queue = deque([(route_node_id, 0)])

        collected_nodes: List[GraphNode] = [route_node]
        collected_edges: List[GraphEdge] = []

        while queue:
            curr_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for edge in adj.get(curr_id, []):
                target_id = edge.target
                collected_edges.append(edge)

                if target_id not in visited and target_id in nodes_by_id:
                    visited.add(target_id)
                    target_node = nodes_by_id[target_id]
                    collected_nodes.append(target_node)
                    queue.append((target_id, depth + 1))

        # Categorize collected nodes into architectural flow stages
        stages: Dict[str, List[Dict[str, Any]]] = {
            "route": [],
            "middleware_auth": [],
            "service_logic": [],
            "data_access": [],
            "database_entities": [],
            "external_integrations": [],
        }

        for node in collected_nodes:
            item = {
                "id": node.id,
                "label": node.label,
                "type": node.type,
                "layer": node.layer,
                "file_path": node.file_path,
                "start_line": node.start_line,
                "summary": node.summary,
                "confidence": node.confidence,
                "evidence_status": node.evidence_status,
            }

            if node.id == route_node_id or node.type == NodeType.ROUTE.value:
                stages["route"].append(item)
            elif any(k in node.label.lower() for k in ("auth", "token", "verify", "permission", "guard", "session")):
                stages["middleware_auth"].append(item)
            elif node.layer == ArchitecturalLayer.DATABASE.value or node.type == NodeType.MODEL.value:
                stages["database_entities"].append(item)
            elif node.layer == ArchitecturalLayer.DATA_ACCESS.value or any(k in node.label.lower() for k in ("repo", "dao", "query", "db")):
                stages["data_access"].append(item)
            elif node.layer == ArchitecturalLayer.EXTERNAL.value or "external::" in node.id:
                stages["external_integrations"].append(item)
            else:
                stages["service_logic"].append(item)

        meta = route_node.metadata or {}
        route_header = {
            "id": route_node.id,
            "label": route_node.label,
            "http_method": meta.get("http_method", "GET"),
            "route_path": meta.get("route_path", f"/{route_node.label}"),
            "file_path": route_node.file_path,
            "start_line": route_node.start_line,
            "summary": route_node.summary,
        }

        return {
            "route": route_header,
            "stages": stages,
            "flow_nodes": collected_nodes,
            "flow_edges": collected_edges,
            "total_connected_components": len(collected_nodes),
            "disclaimer": (
                "Verified Static Dependency Flow: Represents statically detected references, "
                "calls, and data operations from codebase AST parsing. Runtime execution order, "
                "conditional branches, and dynamic dispatch may vary at runtime."
            )
        }
