import pytest
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
from app.services.graph_adapter import GraphAdapter


def test_graph_adapter_bidirectional_conversion():
    node1 = GraphNode(
        id="backend/api/routes.py::checkout",
        label="checkout",
        type=NodeType.ROUTE.value,
        file_path="backend/api/routes.py",
        start_line=10,
        end_line=25,
        language="python",
        summary="Checkout handler",
        layer=ArchitecturalLayer.API.value,
        cluster="backend/api",
        position_3d=Position3D(x=10.0, y=20.0, z=30.0),
        position_2d=Position2D(x=15.0, y=25.0),
    )
    node2 = GraphNode(
        id="database/schema.sql::orders",
        label="orders",
        type=NodeType.MODEL.value,
        file_path="database/schema.sql",
        start_line=1,
        end_line=15,
        language="sql",
        summary="Orders table",
        layer=ArchitecturalLayer.DATABASE.value,
        cluster="database",
        position_3d=Position3D(x=-10.0, y=-20.0, z=-30.0),
        position_2d=Position2D(x=-15.0, y=-25.0),
    )
    edge = GraphEdge(
        id="e1",
        source=node1.id,
        target=node2.id,
        type=EdgeType.WRITES_TO.value,
        evidence="writes to orders table",
        source_file="backend/api/routes.py",
        source_line=15,
        evidence_status=EvidenceStatus.VERIFIED.value,
    )

    from app.services.graph_builder import GraphBuilder
    b = GraphBuilder()
    b.nodes = {node1.id: node1, node2.id: node2}
    b.edges = [edge]
    original_graph, _, _ = b.build_normalized_graph()

    # 1. Export to Graphify schema
    graphify_json = GraphAdapter.to_graphify_schema(original_graph)
    assert graphify_json["schema_version"] == "1"
    assert graphify_json["graphify_version"] == "0.9.4"
    assert len(graphify_json["nodes"]) == 2
    assert len(graphify_json["edges"]) == 1
    assert graphify_json["nodes"][0]["source_location"] == "L10-L25"
    assert graphify_json["edges"][0]["relation"] == "uses"
    assert graphify_json["edges"][0]["confidence"] == "EXTRACTED"

    # 2. Import back from Graphify schema
    reconstructed_graph = GraphAdapter.from_graphify_schema(graphify_json)
    assert len(reconstructed_graph.nodes) == 2
    assert len(reconstructed_graph.edges) == 1

    rec_node1 = next(n for n in reconstructed_graph.nodes if n.id == node1.id)
    assert rec_node1.label == "checkout"
    assert rec_node1.start_line == 10
    assert rec_node1.end_line == 25
    assert rec_node1.layer == ArchitecturalLayer.API.value
