import pytest
from app.models.graph import (
    ArchitecturalLayer,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
)
from app.services.comparison_service import ComparisonService
from app.services.graph_builder import GraphBuilder


def test_comparison_service_added_modified_removed():
    # Base Graph
    node1 = GraphNode(id="api/routes.py::get_users", label="get_users", type=NodeType.ROUTE.value, file_path="api/routes.py", start_line=1, end_line=10, layer=ArchitecturalLayer.API.value)
    node2 = GraphNode(id="services/user.py::find_user", label="find_user", type=NodeType.FUNCTION.value, file_path="services/user.py", start_line=1, end_line=15, layer=ArchitecturalLayer.BUSINESS_LOGIC.value)
    
    b1 = GraphBuilder()
    b1.nodes = {node1.id: node1, node2.id: node2}
    b1.edges = [GraphEdge(id="e1", source=node1.id, target=node2.id, type=EdgeType.CALLS.value, evidence="calls find_user")]
    base_graph, _, _ = b1.build_normalized_graph()

    # Target Graph (v2):
    # - node1 modified (line drift)
    # - node2 removed
    # - node3 added (new route)
    node1_mod = GraphNode(id="api/routes.py::get_users", label="get_users", type=NodeType.ROUTE.value, file_path="api/routes.py", start_line=1, end_line=25, summary="Modified v2", layer=ArchitecturalLayer.API.value)
    node3_new = GraphNode(id="api/routes.py::create_user", label="create_user", type=NodeType.ROUTE.value, file_path="api/routes.py", start_line=30, end_line=45, layer=ArchitecturalLayer.API.value)

    b2 = GraphBuilder()
    b2.nodes = {node1_mod.id: node1_mod, node3_new.id: node3_new}
    b2.edges = []
    target_graph, _, _ = b2.build_normalized_graph()

    res = ComparisonService.compare_graphs(base_graph, target_graph, base_ref="main", target_ref="v2")

    assert res["summary"]["added_count"] == 1
    assert res["summary"]["modified_count"] == 1
    assert res["summary"]["removed_count"] == 1
    assert any(n["label"] == "create_user" for n in res["changes"]["added_symbols"])
    assert any(n["label"] == "get_users" for n in res["changes"]["modified_symbols"])
    assert any(n["label"] == "find_user" for n in res["changes"]["removed_symbols"])
