"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI app
app = FastAPI(
    title="Smart Summary & Insight Service",
    description="AI-powered assistant for analyzing structured data and unstructured notes",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["analysis"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Smart Summary & Insight Service",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/api/v1/analyze",
            "batch_analyze": "/api/v1/batch/analyze",
            "batch_status": "/api/v1/batch/{job_id}/status",
            "health": "/api/v1/health",
            "ready": "/api/v1/ready",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )

