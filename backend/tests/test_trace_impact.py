from app.models.graph import (
    ArchitecturalLayer,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
    NormalizedGraph,
)
from app.services.impact_service import ImpactService
from app.services.trace_service import TraceService


def create_mock_pipeline_graph() -> NormalizedGraph:
    # A -> B -> C -> D
    n_a = GraphNode(id="A", label="ComponentA", type=NodeType.COMPONENT.value, file_path="ui/A.tsx", layer=ArchitecturalLayer.UI.value)
    n_b = GraphNode(id="B", label="RouteB", type=NodeType.ROUTE.value, file_path="api/B.py", layer=ArchitecturalLayer.API.value)
    n_c = GraphNode(id="C", label="ServiceC", type=NodeType.CLASS.value, file_path="core/C.py", layer=ArchitecturalLayer.BUSINESS_LOGIC.value)
    n_d = GraphNode(id="D", label="ModelD", type=NodeType.MODEL.value, file_path="db/D.py", layer=ArchitecturalLayer.DATABASE.value)

    edges = [
        GraphEdge(id="e1", source="A", target="B", type=EdgeType.CALLS.value, evidence="fetch /api/b"),
        GraphEdge(id="e2", source="B", target="C", type=EdgeType.CALLS.value, evidence="ServiceC.process()"),
        GraphEdge(id="e3", source="C", target="D", type=EdgeType.WRITES_TO.value, evidence="db.add(ModelD)"),
    ]
    return NormalizedGraph(nodes=[n_a, n_b, n_c, n_d], edges=edges)


def test_trace_feature_path_shortest_path():
    graph = create_mock_pipeline_graph()
    trace = TraceService.trace_feature_path(graph, start_node_id="A", target_node_id="D")

    assert trace.path_found is True
    assert [n.id for n in trace.path_nodes] == ["A", "B", "C", "D"]
    assert len(trace.path_edges) == 3
    assert len(trace.step_descriptions) == 3


def test_impact_analysis_transitive():
    graph = create_mock_pipeline_graph()
    # If D (database model) changes, what breaks?
    # C depends on D (direct), B depends on C (transitive), A depends on B (transitive)
    impact = ImpactService.analyze_change_impact(graph, node_id="D")

    direct_ids = {n.id for n in impact.direct_dependents}
    transitive_ids = {n.id for n in impact.transitive_dependents}

    assert "C" in direct_ids
    assert "B" in transitive_ids
    assert "A" in transitive_ids
    assert impact.total_impact_count == 3
    assert len(impact.affected_routes) == 1  # RouteB
