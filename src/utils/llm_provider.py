"""LLM provider abstraction for Claude and OpenAI."""

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from src.config import settings


def get_chat_model(temperature: float = 0.7) -> BaseChatModel:
    """
    Get the configured chat model based on settings.
    
    Args:
        temperature: Model temperature for response randomness (0-1)
        
    Returns:
        Configured chat model instance
        
    Raises:
        ValueError: If provider is not configured properly
    """
    if settings.LLM_PROVIDER == "claude":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return ChatAnthropic(
            model=settings.CLAUDE_MODEL,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=temperature
        )
    elif settings.LLM_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=temperature
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")

