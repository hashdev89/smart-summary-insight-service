"""Pydantic models for API request/response validation."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

# Maximum records per batch (30 min target for 500 records)
BATCH_MAX_RECORDS = 500


class StructuredData(BaseModel):
    """Structured JSON data input."""
    data: Dict[str, Any] = Field(
        ...,
        description="Structured JSON data (e.g., customer info, events, metadata)"
    )


class AnalyzeRequest(BaseModel):
    """Request model for the /analyze endpoint."""
    structured_data: Optional[StructuredData] = Field(
        None,
        description="Optional structured JSON data"
    )
    notes: str | List[str] = Field(
        ...,
        description="Free-text notes (string or array of strings)"
    )
    
    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v):
        """Ensure notes is always a list for consistent processing."""
        if isinstance(v, str):
            return [v] if v.strip() else []
        return [note for note in v if note and note.strip()]


class Insight(BaseModel):
    """A single extracted insight."""
    title: str = Field(..., description="Brief title of the insight")
    description: str = Field(..., description="Detailed description")
    category: Optional[str] = Field(None, description="Category or type of insight")
    priority: Optional[str] = Field(None, description="Priority level (high/medium/low)")


class NextAction(BaseModel):
    """A suggested follow-up action."""
    action: str = Field(..., description="Description of the action")
    priority: str = Field(..., description="Priority level (high/medium/low)")
    rationale: Optional[str] = Field(None, description="Why this action is suggested")


class Metadata(BaseModel):
    """Metadata about the analysis."""
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)"
    )
    model_version: str = Field(..., description="LLM model version used")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


class AnalyzeResponse(BaseModel):
    """Response model for the /analyze endpoint."""
    summary: str = Field(..., description="AI-generated concise summary")
    insights: List[Insight] = Field(..., description="Extracted key points")
    next_actions: List[NextAction] = Field(..., description="Suggested follow-up actions")
    metadata: Metadata = Field(..., description="Analysis metadata")


class BatchJobStatus(str, Enum):
    """Status of a batch job."""
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchAnalyzeRequest(BaseModel):
    """Request model for batch analyze: list of analyze requests (max 500)."""
    records: List[AnalyzeRequest] = Field(
        ...,
        min_length=1,
        max_length=BATCH_MAX_RECORDS,
        description=f"List of records to analyze (1 to {BATCH_MAX_RECORDS})"
    )


class BatchJobResponse(BaseModel):
    """Response when a batch job is submitted."""
    job_id: str = Field(..., description="Unique job identifier for progress tracking")
    status: BatchJobStatus = Field(..., description="Current job status")
    total_records: int = Field(..., description="Number of records in the batch")
    message: str = Field(
        default="Batch accepted. Use GET /api/v1/batch/{job_id}/status to track progress.",
        description="Human-readable message"
    )


class BatchRecordResult(BaseModel):
    """Result for a single record in a batch (index and response or error)."""
    index: int = Field(..., description="Zero-based index of the record in the batch")
    success: bool = Field(..., description="Whether this record was processed successfully")
    response: Optional[AnalyzeResponse] = Field(None, description="Analysis response when success=True")
    error: Optional[str] = Field(None, description="Error message when success=False")


class BatchStatusResponse(BaseModel):
    """Response for batch job status (progress and optional results)."""
    job_id: str = Field(..., description="Job identifier")
    status: BatchJobStatus = Field(..., description="Current job status")
    total_records: int = Field(..., description="Total records in the batch")
    completed_count: int = Field(..., description="Number of records processed so far")
    failed_count: int = Field(default=0, description="Number of records that failed")
    progress_percent: float = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    total_tokens_used: int = Field(default=0, description="Cost tracking: total tokens used for this batch")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost for this batch (if pricing configured)")
    results: Optional[List[BatchRecordResult]] = Field(
        None,
        description="Partial results: per-record results (available before batch completes)"
    )
    created_at: Optional[datetime] = Field(None, description="When the job was created")
    updated_at: Optional[datetime] = Field(None, description="Last status update")


class BatchJobListItem(BaseModel):
    """Single row for persisted batch jobs table (list endpoint)."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status (accepted/processing/completed/failed)")
    total_records: int = Field(..., description="Total records in the batch")
    completed_count: int = Field(..., description="Records completed successfully")
    failed_count: int = Field(..., description="Records that failed")
    total_tokens_used: int = Field(default=0, description="Total tokens used for the batch")
    created_at: Optional[str] = Field(None, description="Created timestamp (ISO)")
    updated_at: Optional[str] = Field(None, description="Last updated timestamp (ISO)")


class BatchJobListResponse(BaseModel):
    """Response for list of persisted batch jobs."""
    jobs: List[BatchJobListItem] = Field(..., description="List of batch jobs (most recent first)")

