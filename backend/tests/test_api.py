import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "RepoGraph"


def test_ai_status_endpoint():
    res = client.get("/api/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "available" in data
    assert data["preferred_model"] == "gemma-4-26b-a4b-it"


def test_demo_repository_analysis_flow():
    # Analyze the built-in demo repository
    res = client.post("/api/repositories/analyze", json={
        "repository_url": "https://github.com/repograph-demo/ecommerce-platform"
    })
    assert res.status_code == 200
    init_data = res.json()
    analysis_id = init_data["analysis_id"]

    # Poll status (in test environment, synchronous background tasks execute immediately or we check status)
    status_res = client.get(f"/api/analyses/{analysis_id}")
    assert status_res.status_code == 200
    st_data = status_res.json()
    assert st_data["status"] in ("in_progress", "completed")

    # If completed, check graph, files, and er-diagram endpoints
    if st_data["status"] == "completed":
        graph_res = client.get(f"/api/analyses/{analysis_id}/graph")
        assert graph_res.status_code == 200
        g_data = graph_res.json()
        assert len(g_data["nodes"]) > 0

        er_res = client.get(f"/api/analyses/{analysis_id}/er-diagram")
        assert er_res.status_code == 200
        assert "entities" in er_res.json()
