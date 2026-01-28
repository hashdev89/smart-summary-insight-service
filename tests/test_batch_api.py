"""Tests for batch analyze API."""
import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.main import app
from app.models.schemas import AnalyzeResponse, Insight, NextAction, Metadata
from app.services.batch_job_store import batch_job_store
from datetime import datetime, timezone


BASE_URL = "http://test"
BATCH_ANALYZE_URL = f"{BASE_URL}/api/v1/batch/analyze"


def make_mock_analyze_response():
    """Build a valid AnalyzeResponse for mocking."""
    return AnalyzeResponse(
        summary="Test summary.",
        insights=[
            Insight(title="Insight 1", description="First insight.", category="support", priority="high"),
        ],
        next_actions=[
            NextAction(action="Follow up.", priority="high", rationale="Test."),
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
def valid_batch_request():
    """Minimal valid batch request (2 records)."""
    return {
        "records": [
            {"notes": "First note."},
            {"notes": "Second note."},
        ]
    }


@pytest.fixture(autouse=True)
def reset_batch_store():
    """Ensure batch store is clean between tests (no cross-test state)."""
    yield
    # Clear any jobs created during test (store is in-memory)
    batch_job_store._jobs.clear()


@pytest.mark.asyncio
@patch("app.api.routes.ai_service.analyze", new_callable=AsyncMock, return_value=make_mock_analyze_response())
async def test_batch_analyze_accepts_and_returns_job_id(mock_analyze, valid_batch_request):
    """POST /batch/analyze returns 202 with job_id and total_records."""
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post(BATCH_ANALYZE_URL, json=valid_batch_request)

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["total_records"] == 2
    assert data["status"] == "accepted"
    assert "batch" in data.get("message", "").lower() or "progress" in data.get("message", "").lower()


@pytest.mark.asyncio
@patch("app.api.routes.ai_service.analyze", new_callable=AsyncMock, return_value=make_mock_analyze_response())
async def test_batch_status_returns_progress(mock_analyze, valid_batch_request):
    """GET /batch/{job_id}/status returns progress and eventually results."""
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        submit = await client.post(BATCH_ANALYZE_URL, json=valid_batch_request)
    assert submit.status_code == 202
    job_id = submit.json()["job_id"]

    # Poll until completed (background task runs after response)
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        completed = False
        for _ in range(50):
            status_resp = await client.get(f"{BASE_URL}/api/v1/batch/{job_id}/status")
            assert status_resp.status_code == 200
            st = status_resp.json()
            assert st["job_id"] == job_id
            assert st["total_records"] == 2
            assert "completed_count" in st
            assert "progress_percent" in st
            if st["status"] == "completed":
                assert st["completed_count"] == 2
                assert st["progress_percent"] == 100.0
                assert "results" in st and len(st["results"]) == 2
                completed = True
                break
            await asyncio.sleep(0.1)
        assert completed, "Batch did not complete within timeout"


@pytest.mark.asyncio
async def test_batch_status_404_for_unknown_job():
    """GET /batch/{job_id}/status returns 404 for unknown job_id."""
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.get(f"{BASE_URL}/api/v1/batch/00000000-0000-0000-0000-000000000000/status")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_batch_analyze_rejects_empty_records():
    """POST /batch/analyze returns 422 when records is empty."""
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post(BATCH_ANALYZE_URL, json={"records": []})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_batch_analyze_rejects_over_500_records():
    """POST /batch/analyze returns 422 when records exceed 500."""
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.post(
            BATCH_ANALYZE_URL,
            json={"records": [{"notes": f"Note {i}."} for i in range(501)]},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_batch_list_jobs_returns_200_and_jobs_array():
    """GET /batch/jobs returns 200 and list of jobs (may be empty)."""
    async with AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.get(f"{BASE_URL}/api/v1/batch/jobs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert isinstance(data["jobs"], list)
