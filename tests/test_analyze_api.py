"""Tests for the /analyze API and response parameters."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.main import app
from app.models.schemas import AnalyzeResponse, Insight, NextAction, Metadata


BASE_URL = "http://test"
ANALYZE_URL = f"{BASE_URL}/api/v1/analyze"


def make_mock_analyze_response():
    """Build a valid AnalyzeResponse for mocking."""
    return AnalyzeResponse(
        summary="Test summary.",
        insights=[
            Insight(title="Insight 1", description="First insight.", category="support", priority="high"),
        ],
        next_actions=[
            NextAction(action="Follow up with customer.", priority="high", rationale="Delay reported."),
        ],
        metadata=Metadata(
            confidence_score=0.9,
            model_version="test-model",
            processing_time_ms=100.0,
            tokens_used=50,
            timestamp=datetime.now(timezone.utc),
        ),
    )


@pytest.fixture
def valid_analyze_request():
    """Minimal valid request body for /analyze."""
    return {
        "notes": "Customer called about delayed shipment. Order #12345. Will follow up tomorrow.",
    }


@pytest.fixture
def analyze_request_with_structured_data():
    """Request body with structured_data and notes."""
    return {
        "structured_data": {
            "data": {
                "order_id": "12345",
                "status": "delayed",
                "customer_tier": "premium",
            }
        },
        "notes": ["Customer reported delay.", "Promised callback by EOD."],
    }


@pytest.mark.asyncio
@patch("app.api.routes.ai_service.analyze", new_callable=AsyncMock, return_value=make_mock_analyze_response())
async def test_analyze_response_params_structure(mock_analyze, valid_analyze_request):
    """Assert /analyze response contains required params: summary, insights, next_actions, metadata."""
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post(ANALYZE_URL, json=valid_analyze_request)

    assert response.status_code == 200
    data = response.json()

    # Required top-level response params
    assert "summary" in data
    assert "insights" in data
    assert "next_actions" in data
    assert "metadata" in data

    assert isinstance(data["summary"], str)
    assert len(data["summary"]) > 0

    assert isinstance(data["insights"], list)
    for insight in data["insights"]:
        assert "title" in insight
        assert "description" in insight
        assert isinstance(insight["title"], str)
        assert isinstance(insight["description"], str)

    assert isinstance(data["next_actions"], list)
    for action in data["next_actions"]:
        assert "action" in action
        assert "priority" in action
        assert isinstance(action["action"], str)
        assert isinstance(action["priority"], str)

    meta = data["metadata"]
    assert "confidence_score" in meta
    assert "model_version" in meta
    assert isinstance(meta["confidence_score"], (int, float))
    assert 0 <= meta["confidence_score"] <= 1
    assert isinstance(meta["model_version"], str)


@pytest.mark.asyncio
@patch("app.api.routes.ai_service.analyze", new_callable=AsyncMock, return_value=make_mock_analyze_response())
async def test_analyze_with_structured_data_response_params(mock_analyze, analyze_request_with_structured_data):
    """Assert response params when request includes structured_data."""
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post(ANALYZE_URL, json=analyze_request_with_structured_data)

    assert response.status_code == 200
    data = response.json()

    assert "summary" in data
    assert "insights" in data
    assert "next_actions" in data
    assert "metadata" in data
    assert isinstance(data["insights"], list)
    assert isinstance(data["next_actions"], list)


@pytest.mark.asyncio
async def test_analyze_rejects_empty_notes():
    """Assert 400 when notes is empty."""
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post(ANALYZE_URL, json={"notes": ""})

    assert response.status_code == 400
    assert "note" in response.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_analyze_rejects_missing_notes():
    """Assert 422 when notes is missing."""
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post(ANALYZE_URL, json={})

    assert response.status_code == 422
