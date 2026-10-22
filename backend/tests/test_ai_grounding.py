import pytest
from unittest.mock import patch
from app.models.graph import ArchitecturalLayer, GraphEdge, GraphNode, NodeType
from app.services.ai_service import AIService


def create_sample_nodes():
    return [
        GraphNode(
            id="backend/api/routes.py::checkout_cart",
            label="checkout_cart",
            type=NodeType.ROUTE.value,
            layer=ArchitecturalLayer.API.value,
            file_path="backend/api/routes.py",
            start_line=15,
            end_line=30,
            confidence=0.95
        ),
        GraphNode(
            id="backend/services/order_service.py::OrderService",
            label="OrderService",
            type=NodeType.CLASS.value,
            layer=ArchitecturalLayer.BUSINESS_LOGIC.value,
            file_path="backend/services/order_service.py",
            start_line=10,
            end_line=45,
            confidence=0.92
        ),
        GraphNode(
            id="backend/models/order.py::Order",
            label="Order",
            type=NodeType.MODEL.value,
            layer=ArchitecturalLayer.DATABASE.value,
            file_path="backend/models/order.py",
            start_line=5,
            end_line=25,
            confidence=0.98
        )
    ]


def test_validate_grounded_references_valid():
    nodes = create_sample_nodes()
    findings = [
        "Component checkout_cart is defined in routes.py and coordinates cart operations.",
        "Invokes OrderService to validate order requirements before persisting.",
        "Creates an instance of Order mapped to the database."
    ]

    valid, demoted, warnings = AIService.validate_grounded_references(findings, nodes)
    assert len(valid) == 3
    assert len(demoted) == 0
    assert len(warnings) == 0


def test_validate_grounded_references_hallucinated_file():
    nodes = create_sample_nodes()
    findings = [
        "Component checkout_cart coordinates order lifecycle.",
        "Dispatches payment telemetry to analytics_tracker.py for external monitoring."
    ]

    valid, demoted, warnings = AIService.validate_grounded_references(findings, nodes)
    assert len(valid) == 1
    assert "checkout_cart" in valid[0]
    assert len(demoted) == 1
    assert "[Ungrounded Reference: file 'analytics_tracker.py']" in demoted[0]
    assert len(warnings) == 1
    assert "analytics_tracker.py" in warnings[0]


def test_validate_grounded_references_hallucinated_symbol():
    nodes = create_sample_nodes()
    findings = [
        "Handles the checkout flow using OrderService.",
        "Invokes method `execute_instant_refund` on order failure."
    ]

    valid, demoted, warnings = AIService.validate_grounded_references(findings, nodes)
    assert len(valid) == 1
    assert len(demoted) == 1
    assert "[Ungrounded Reference: symbol 'execute_instant_refund']" in demoted[0]
    assert len(warnings) == 1
    assert "execute_instant_refund" in warnings[0]


def test_validate_grounded_references_ignores_standard_framework_tokens():
    nodes = create_sample_nodes()
    findings = [
        "Uses FastAPI for HTTP route registration and Pydantic for validation.",
        "Configuration is specified in requirements.txt and package.json.",
        "Connects to PostgreSQL database via SQLAlchemy session."
    ]

    valid, demoted, warnings = AIService.validate_grounded_references(findings, nodes)
    assert len(valid) == 3
    assert len(demoted) == 0
    assert len(warnings) == 0


@pytest.mark.asyncio
async def test_explain_component_grounding_integration():
    nodes = create_sample_nodes()
    target_node = nodes[0]

    mock_llm_response = (
        "CONFIRMED FINDINGS:\n"
        "- Route checkout_cart handles POST requests in routes.py.\n"
        "- Dispatches request payload to external_audit_service.py for audit compliance.\n\n"
        "INFERRED HYPOTHESES:\n"
        "- May support idempotency tokens.\n\n"
        "UNRESOLVED QUESTIONS:\n"
        "- Exact retry policy for upstream timeouts.\n"
    )

    with patch.object(AIService, "is_ai_available", return_value=True):
        with patch.object(AIService, "generate_explanation", return_value=(mock_llm_response, "gemma-4-26b-a4b-it")):
            response = await AIService.explain_component(
                node=target_node,
                source_snippet="def checkout_cart(): pass",
                incoming_edges=[],
                outgoing_edges=[],
                question="Explain this endpoint",
                known_nodes=nodes
            )

            # Grounded finding preserved
            assert any("checkout_cart" in f for f in response.verified_findings)
            # Hallucinated file finding demoted to hypotheses
            assert any("[Ungrounded Reference: file 'external_audit_service.py']" in h for h in response.inferred_hypotheses)
            # Warning registered in unresolved questions
            assert any("external_audit_service.py" in q for q in response.unresolved_questions)
            # Confidence penalized from 0.92 to 0.84
            assert response.confidence == 0.84
