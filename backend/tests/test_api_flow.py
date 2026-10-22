import pytest
from app.models.graph import (
    ArchitecturalLayer,
    EdgeType,
    EvidenceStatus,
    GraphEdge,
    GraphNode,
    NodeType,
)
from app.services.api_flow_service import ApiFlowService
from app.services.graph_builder import GraphBuilder


def test_api_flow_detection_and_tracing():
    route_node = GraphNode(
        id="api/orders.py::checkout",
        label="checkout",
        type=NodeType.ROUTE.value,
        file_path="api/orders.py",
        start_line=12,
        end_line=25,
        language="python",
        layer=ArchitecturalLayer.API.value,
        metadata={"http_method": "POST", "route_path": "/api/orders/checkout"}
    )
    auth_node = GraphNode(
        id="core/auth.py::verify_token",
        label="verify_token",
        type=NodeType.FUNCTION.value,
        file_path="core/auth.py",
        layer=ArchitecturalLayer.BUSINESS_LOGIC.value,
    )
    service_node = GraphNode(
        id="services/order.py::create_order",
        label="create_order",
        type=NodeType.FUNCTION.value,
        file_path="services/order.py",
        layer=ArchitecturalLayer.BUSINESS_LOGIC.value,
    )
    db_node = GraphNode(
        id="database/schema.sql::orders",
        label="orders",
        type=NodeType.MODEL.value,
        file_path="database/schema.sql",
        layer=ArchitecturalLayer.DATABASE.value,
    )

    edges = [
        GraphEdge(id="e1", source=route_node.id, target=auth_node.id, type=EdgeType.CALLS.value, evidence="calls verify_token"),
        GraphEdge(id="e2", source=route_node.id, target=service_node.id, type=EdgeType.CALLS.value, evidence="calls create_order"),
        GraphEdge(id="e3", source=service_node.id, target=db_node.id, type=EdgeType.WRITES_TO.value, evidence="writes to orders"),
    ]

    b = GraphBuilder()
    b.nodes = {n.id: n for n in [route_node, auth_node, service_node, db_node]}
    b.edges = edges
    graph, _, _ = b.build_normalized_graph()

    # 1. Get API routes
    routes = ApiFlowService.get_api_routes(graph)
    assert len(routes) == 1
    assert routes[0]["http_method"] == "POST"
    assert routes[0]["route_path"] == "/api/orders/checkout"

    # 2. Trace API flow from route
    flow = ApiFlowService.trace_api_flow(graph, route_node.id)
    assert flow["route"]["http_method"] == "POST"
    assert len(flow["stages"]["route"]) == 1
    assert len(flow["stages"]["middleware_auth"]) == 1
    assert len(flow["stages"]["service_logic"]) == 1
    assert len(flow["stages"]["database_entities"]) == 1
    assert flow["total_connected_components"] == 4
