from app.models.graph import (
    ArchitecturalLayer,
    EdgeType,
    EvidenceStatus,
    GraphEdge,
    GraphNode,
    NodeType,
    NormalizedGraph,
    Position3D,
)
from app.services.graphify_exporter import GraphifyExporter


def test_graphify_export_schema():
    n1 = GraphNode(
        id="app/main.py::app",
        label="app",
        type=NodeType.CLASS.value,
        file_path="app/main.py",
        start_line=10,
        end_line=20,
        layer=ArchitecturalLayer.API.value,
        cluster="app",
        position_3d=Position3D(x=10.0, y=20.0, z=30.0)
    )
    n2 = GraphNode(
        id="app/models/user.py::User",
        label="User",
        type=NodeType.MODEL.value,
        file_path="app/models/user.py",
        start_line=5,
        end_line=15,
        layer=ArchitecturalLayer.DATABASE.value,
        cluster="app/models",
        position_3d=Position3D(x=5.0, y=10.0, z=-20.0)
    )

    edge = GraphEdge(
        id="e1",
        source=n1.id,
        target=n2.id,
        type=EdgeType.CALLS.value,
        evidence="app -> User",
        evidence_status=EvidenceStatus.VERIFIED.value
    )

    graph = NormalizedGraph(nodes=[n1, n2], edges=[edge])
    export = GraphifyExporter.export_graphify_json(graph)

    assert export["schema_version"] == "1"
    assert export["graphify_version"] == "0.9.4"
    assert export["directed"] is False
    assert len(export["nodes"]) == 2
    assert len(export["edges"]) == 1

    # Check node fields
    exported_node = export["nodes"][0]
    assert "id" in exported_node
    assert "label" in exported_node
    assert "source_file" in exported_node
    assert "source_location" in exported_node
    assert "file_type" in exported_node
    assert "community" in exported_node
    assert isinstance(exported_node["community"], int)

    # Check edge fields
    exported_edge = export["edges"][0]
    assert exported_edge["relation"] == "calls"
    assert exported_edge["confidence"] == "EXTRACTED"
    assert exported_edge["source"] == n1.id
    assert exported_edge["target"] == n2.id
