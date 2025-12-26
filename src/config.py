"""Configuration management using Pydantic settings."""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration
    LLM_PROVIDER: Literal["claude", "openai"] = Field(
        default="claude",
        description="LLM provider to use (claude or openai)"
    )
    ANTHROPIC_API_KEY: str | None = Field(
        default=None,
        description="Anthropic API key for Claude"
    )
    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="OpenAI API key for GPT-4"
    )
    
    # Model Configuration
    CLAUDE_MODEL: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Claude model version to use"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4",
        description="OpenAI model version to use"
    )
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite:///./fitness_pal.db",
        description="Database connection URL"
    )
    
    # API Configuration
    API_HOST: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    API_PORT: int = Field(
        default=8000,
        description="API server port"
    )
    DEBUG: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    
    # Application Settings
    MIN_CALORIE_FLOOR: int = Field(
        default=1200,
        description="Minimum daily calorie intake for safety"
    )
    MAX_CALORIE_DEFICIT: int = Field(
        default=1000,
        description="Maximum daily calorie deficit for safety"
    )
    MAX_CALORIE_SURPLUS: int = Field(
        default=500,
        description="Maximum daily calorie surplus for safety"
    )
    
    def validate_llm_config(self) -> None:
        """Validate that required API key is present for selected provider."""
        if self.LLM_PROVIDER == "claude" and not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when using Claude")
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI")


# Create global settings instance
settings = Settings()

# Validate configuration on import
try:
    settings.validate_llm_config()
except ValueError as e:
    # Only warn during development, don't crash
    if settings.DEBUG:
        print(f"Warning: {e}")

