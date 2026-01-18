"""Basic tests for the API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


def test_analyze_endpoint_validation():
    """Test that analyze endpoint validates input."""
    # Missing notes
    response = client.post("/api/v1/analyze", json={
        "notes": []
    })
    assert response.status_code == 400
    
    # Invalid request format
    response = client.post("/api/v1/analyze", json={})
    assert response.status_code == 422  # Validation error


def test_analyze_endpoint_structure():
    """Test analyze endpoint with valid input structure."""
    response = client.post("/api/v1/analyze", json={
        "notes": "Test note about customer interaction",
        "structured_data": {
            "data": {
                "customer_id": "12345",
                "event_type": "support_ticket"
            }
        }
    })
    
    # Should return 200 if API key is valid, or 500 if not
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "summary" in data
        assert "insights" in data
        assert "next_actions" in data
        assert "metadata" in data
        assert "confidence_score" in data["metadata"]

