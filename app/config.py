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

