"""API route handlers."""
import asyncio
import logging

from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from app.config import settings
from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    BatchAnalyzeRequest,
    BatchJobListItem,
    BatchJobListResponse,
    BatchJobResponse,
    BatchStatusResponse,
    BatchJobStatus,
)
from app.services.ai_service import AIService, AIServiceError
from app.services.cache_service import cache_service
from app.services.batch_job_store import batch_job_store
from app.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter()
ai_service = AIService()

# Rate limit: Claude API 50 requests/minute (configurable)
_rate_limiter = RateLimiter(requests_per_minute=getattr(settings, "claude_requests_per_minute", 50))


async def _process_one_record(
    job_id: str,
    idx: int,
    req: AnalyzeRequest,
    sem: asyncio.Semaphore,
) -> None:
    """
    Process a single record: cache check, then LLM with rate limit and concurrency limit.
    Failures are isolated—one bad record does not fail the entire batch.
    """
    structured_data = req.structured_data.data if req.structured_data else None
    notes = req.notes if isinstance(req.notes, list) else list(req.notes)
    if not notes:
        batch_job_store.append_result(job_id, idx, False, error="At least one note is required")
        return
    cached = cache_service.get(structured_data, notes)
    if cached:
        tokens = getattr(cached.metadata, "tokens_used", None) or 0
        batch_job_store.append_result(job_id, idx, True, response=cached, tokens_used=tokens)
        return
    max_attempts = 1 + getattr(settings, "batch_record_retry_count", 1)
    last_error = None
    for attempt in range(max_attempts):
        try:
            async with sem:
                await _rate_limiter.acquire()
                response = await ai_service.analyze(structured_data, notes)
            cache_service.set(structured_data, notes, response)
            tokens = getattr(response.metadata, "tokens_used", None) or 0
            batch_job_store.append_result(job_id, idx, True, response=response, tokens_used=tokens)
            return
        except Exception as e:
            last_error = e
            logger.warning("Batch record %s attempt %s failed: %s", idx, attempt + 1, e)
    logger.exception("Batch record %s failed after %s attempts", idx, max_attempts)
    batch_job_store.append_result(job_id, idx, False, error=str(last_error))


async def _process_batch(job_id: str, records: list[AnalyzeRequest]) -> None:
    """
    Background task: process records with configurable concurrency and rate limiting.
    - Respects Claude API rate limit (50 req/min).
    - Max concurrent LLM calls is configurable.
    - Handles failures gracefully—one bad record does not fail the entire batch.
    - Partial results are available before completion (persisted when backend=file).
    """
    batch_job_store.set_processing(job_id)
    concurrency = getattr(settings, "batch_max_concurrent_llm_calls", 5)
    sem = asyncio.Semaphore(concurrency)
    try:
        await asyncio.gather(
            *[_process_one_record(job_id, idx, req, sem) for idx, req in enumerate(records)]
        )
    except Exception as e:
        logger.exception("Batch job %s fatal error: %s", job_id, e)
        batch_job_store.set_job_failed(job_id, message=str(e))
        return
    batch_job_store.set_job_completed(job_id)
    logger.info("Batch job %s completed", job_id)


@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze structured data and free-text notes.
    
    This endpoint accepts structured JSON data and free-text notes,
    then uses an LLM to generate:
    - A concise summary
    - Key extracted insights
    - Suggested next actions
    - Metadata including confidence score and model version
    """
    try:
        # Validate input
        if not request.notes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one note is required"
            )
        
        # Prepare data for processing
        structured_data = request.structured_data.data if request.structured_data else None
        notes = request.notes if isinstance(request.notes, list) else [request.notes]
        
        # Check cache first
        cached_response = cache_service.get(structured_data, notes)
        if cached_response:
            logger.info("Returning cached response")
            return cached_response
        
        # Process with AI service
        response = await ai_service.analyze(structured_data, notes)
        
        # Cache the response
        cache_service.set(structured_data, notes, response)
        
        return response
        
    except HTTPException:
        raise
    except AIServiceError as e:
        logger.error(f"AI service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI processing failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/batch/analyze",
    response_model=BatchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit batch analysis",
)
async def batch_analyze(
    request: BatchAnalyzeRequest,
    background_tasks: BackgroundTasks,
) -> BatchJobResponse:
    """
    Submit a batch of up to 500 records for analysis.

    Returns immediately with a job_id. Process completes within ~30 minutes for 500 records.
    Use GET /api/v1/batch/{job_id}/status to track progress and retrieve results.
    """
    records = request.records
    job_id = batch_job_store.create_job(total_records=len(records))
    background_tasks.add_task(_process_batch, job_id, records)
    logger.info("Batch job %s submitted with %s records", job_id, len(records))
    return BatchJobResponse(
        job_id=job_id,
        status=BatchJobStatus.ACCEPTED,
        total_records=len(records),
        message="Batch accepted. Use GET /api/v1/batch/{job_id}/status to track progress.",
    )


@router.get(
    "/batch/{job_id}/status",
    response_model=BatchStatusResponse,
    summary="Get batch job status and progress",
)
async def batch_status(job_id: str) -> BatchStatusResponse:
    """
    Get progress and results for a batch job.

    Returns completed_count, failed_count, progress_percent, and results when available.
    """
    data = batch_job_store.get_status_response(job_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )
    return BatchStatusResponse(**data)


@router.get(
    "/batch/jobs",
    response_model=BatchJobListResponse,
    summary="List persisted batch jobs",
)
async def batch_list_jobs(limit: int = 50) -> BatchJobListResponse:
    """
    List persisted batch jobs (table data) for display below Batch Analyze.
    Most recent first. Use limit to cap results (default 50).
    """
    if limit < 1 or limit > 200:
        limit = 50
    rows = batch_job_store.list_jobs(limit=limit)
    jobs = [BatchJobListItem(**r) for r in rows]
    return BatchJobListResponse(jobs=jobs)


@router.get("/health")
async def health_check():
    """Health check endpoint (liveness)."""
    return {
        "status": "healthy",
        "service": "Smart Summary & Insight Service",
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe for enterprise SLA (99.9% availability).
    Returns 200 only when the app can serve traffic (e.g. persistence writable when backend=file).
    """
    from pathlib import Path
    backend = getattr(settings, "batch_persistence_backend", "memory")
    if backend == "file":
        path = Path(getattr(settings, "batch_job_storage_path", "data/batch_jobs"))
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".ready_probe"
            probe.write_text("ok")
            probe.unlink()
        except OSError as err:
            logger.warning("Readiness check failed: %s", err)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Storage not ready: {err}",
            )
    elif backend == "sqlite":
        sqlite_path = Path(getattr(settings, "batch_sqlite_path", "data/batch.db"))
        try:
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            import sqlite3
            conn = sqlite3.connect(str(sqlite_path))
            conn.execute("SELECT 1")
            conn.close()
        except Exception as err:
            logger.warning("Readiness check (sqlite) failed: %s", err)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"SQLite not ready: {err}",
            )
    return {"status": "ready"}

