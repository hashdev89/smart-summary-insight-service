"""Pydantic models for API request/response validation."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime


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

