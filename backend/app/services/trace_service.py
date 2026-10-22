from collections import deque
from typing import Dict, List, Optional, Set, Tuple
from app.models.api import TraceResponse
from app.models.graph import GraphEdge, GraphNode, NormalizedGraph


class TraceService:
    @staticmethod
    def trace_feature_path(
        graph: NormalizedGraph,
        start_node_id: str,
        target_node_id: Optional[str] = None,
        max_depth: int = 6
    ) -> TraceResponse:
        nodes_by_id: Dict[str, GraphNode] = {n.id: n for n in graph.nodes}
        if start_node_id not in nodes_by_id:
            return TraceResponse(path_found=False, step_descriptions=[f"Start node '{start_node_id}' not found."])

        # Build adjacency map (outgoing directed edges)
        adj: Dict[str, List[GraphEdge]] = {}
        for edge in graph.edges:
            adj.setdefault(edge.source, []).append(edge)

        # 1. Target node specified -> BFS shortest path
        if target_node_id:
            if target_node_id not in nodes_by_id:
                return TraceResponse(
                    path_found=False,
                    step_descriptions=[f"Target node '{target_node_id}' not found in graph."]
                )

            queue = deque([(start_node_id, [start_node_id], [])])
            visited = {start_node_id}
            found_path_nodes: List[str] = []
            found_path_edges: List[GraphEdge] = []

            while queue:
                curr_id, path_nodes, path_edges = queue.popleft()
                if curr_id == target_node_id:
                    found_path_nodes = path_nodes
                    found_path_edges = path_edges
                    break

                if len(path_nodes) > max_depth:
                    continue

                for edge in adj.get(curr_id, []):
                    next_id = edge.target
                    if next_id not in visited and next_id in nodes_by_id:
                        visited.add(next_id)
                        queue.append((next_id, path_nodes + [next_id], path_edges + [edge]))

            if not found_path_nodes:
                return TraceResponse(
                    path_found=False,
                    step_descriptions=[
                        f"No static connection path found from '{nodes_by_id[start_node_id].label}' "
                        f"to '{nodes_by_id[target_node_id].label}' within depth {max_depth}."
                    ]
                )

            # Build step descriptions
            steps: List[str] = []
            for i, edge in enumerate(found_path_edges):
                src = nodes_by_id[edge.source].label
                tgt = nodes_by_id[edge.target].label
                edge_t = edge.type.replace("_", " ")
                steps.append(f"Step {i+1}: {src} [{edge_t}] ➔ {tgt} (via {edge.evidence})")

            return TraceResponse(
                path_found=True,
                path_nodes=[nodes_by_id[nid] for nid in found_path_nodes],
                path_edges=found_path_edges,
                step_descriptions=steps
            )

        # 2. Target not specified -> downstream flow discovery up to max_depth
        visited = {start_node_id}
        queue = deque([(start_node_id, 0)])
        discovered_nodes: List[GraphNode] = [nodes_by_id[start_node_id]]
        discovered_edges: List[GraphEdge] = []
        steps: List[str] = [f"Origin: {nodes_by_id[start_node_id].label} ({nodes_by_id[start_node_id].type})"]

        while queue:
            curr_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for edge in adj.get(curr_id, []):
                next_id = edge.target
                if next_id not in visited and next_id in nodes_by_id:
                    visited.add(next_id)
                    discovered_nodes.append(nodes_by_id[next_id])
                    discovered_edges.append(edge)
                    steps.append(
                        f"Depth {depth+1}: {nodes_by_id[curr_id].label} [{edge.type}] ➔ "
                        f"{nodes_by_id[next_id].label} ({nodes_by_id[next_id].type})"
                    )
                    queue.append((next_id, depth + 1))

        return TraceResponse(
            path_found=len(discovered_nodes) > 1,
            path_nodes=discovered_nodes,
            path_edges=discovered_edges,
            step_descriptions=steps
        )
