from collections import deque
from typing import Dict, List, Set
from app.models.api import ImpactResponse
from app.models.graph import ArchitecturalLayer, GraphEdge, GraphNode, NodeType, NormalizedGraph


class ImpactService:
    @staticmethod
    def analyze_change_impact(
        graph: NormalizedGraph,
        node_id: str,
        max_depth: int = 4
    ) -> ImpactResponse:
        nodes_by_id: Dict[str, GraphNode] = {n.id: n for n in graph.nodes}
        if node_id not in nodes_by_id:
            raise ValueError(f"Target node '{node_id}' does not exist in graph.")

        target_node = nodes_by_id[node_id]

        # Reverse adjacency map: follows incoming edges (who depends on this node?)
        reverse_adj: Dict[str, List[GraphEdge]] = {}
        for edge in graph.edges:
            reverse_adj.setdefault(edge.target, []).append(edge)

        direct_dependents: List[GraphNode] = []
        transitive_dependents: List[GraphNode] = []

        visited: Set[str] = {node_id}
        # Queue item: (current_node_id, depth)
        queue = deque([(node_id, 0)])

        while queue:
            curr_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for edge in reverse_adj.get(curr_id, []):
                dep_id = edge.source
                if dep_id not in visited and dep_id in nodes_by_id:
                    visited.add(dep_id)
                    dep_node = nodes_by_id[dep_id]

                    if depth == 0:
                        direct_dependents.append(dep_node)
                    else:
                        transitive_dependents.append(dep_node)

                    queue.append((dep_id, depth + 1))

        all_impacted = direct_dependents + transitive_dependents

        # Categorize by architectural characteristics
        affected_routes: List[GraphNode] = [
            n for n in all_impacted if n.type == NodeType.ROUTE.value or n.layer == ArchitecturalLayer.API.value
        ]
        affected_db: List[GraphNode] = [
            n for n in all_impacted if n.type == NodeType.MODEL.value or n.layer == ArchitecturalLayer.DATABASE.value
        ]
        affected_tests: List[GraphNode] = [
            n for n in all_impacted if n.type == NodeType.TEST.value or n.layer == ArchitecturalLayer.TESTS.value
        ]

        affected_layers: Dict[str, int] = {}
        for n in all_impacted:
            affected_layers[n.layer] = affected_layers.get(n.layer, 0) + 1

        return ImpactResponse(
            target_node=target_node,
            direct_dependents=direct_dependents,
            transitive_dependents=transitive_dependents,
            affected_routes=affected_routes,
            affected_database=affected_db,
            affected_tests=affected_tests,
            affected_layers=affected_layers,
            total_impact_count=len(all_impacted)
        )
