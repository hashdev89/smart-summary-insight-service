"""Configuration management for the application."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Anthropic API Configuration
    anthropic_api_key: str = ""  # Will be loaded from .env file
    claude_model: str = "claude-3-5-haiku-20241022"
    max_tokens: int = 1200  # Reduced for faster responses
    temperature: float = 0.3  # Lower for faster, more deterministic responses
    
    # Cache Configuration
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600

    # Batch processing (enterprise rules)
    # Claude API rate limit: 50 requests/minute — we throttle to this
    claude_requests_per_minute: int = 50
    # Maximum concurrent LLM calls per batch (configurable; lower = safer for rate limits)
    batch_max_concurrent_llm_calls: int = 5
    # Persistence: "memory" (dev) | "file" (JSON files) | "sqlite" (table persistence)
    batch_persistence_backend: str = "memory"
    # Directory for file persistence (used when batch_persistence_backend=file)
    batch_job_storage_path: str = "data/batch_jobs"
    # SQLite DB path for table persistence (used when batch_persistence_backend=sqlite)
    batch_sqlite_path: str = "data/batch.db"
    # Retries per record before marking failed (graceful failure: one bad record doesn't fail batch)
    batch_record_retry_count: int = 1
    # Optional: cost per 1K input/output tokens for cost tracking (Anthropic pricing; set for estimated_cost)
    batch_cost_per_1k_input_tokens: Optional[float] = None
    batch_cost_per_1k_output_tokens: Optional[float] = None

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        """Initialize settings and validate required fields."""
        super().__init__(**kwargs)
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. Please set it in your .env file."
            )


# Global settings instance
settings = Settings()

