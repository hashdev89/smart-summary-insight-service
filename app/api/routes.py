"""API route handlers."""
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.ai_service import AIService, AIServiceError
from app.services.cache_service import cache_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
ai_service = AIService()


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


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Smart Summary & Insight Service",
        "version": "1.0.0"
    }

