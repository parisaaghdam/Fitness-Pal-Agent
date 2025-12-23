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
    if settings.llm_provider == "claude":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return ChatAnthropic(
            model=settings.claude_model,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=temperature
        )
    elif settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        return ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            temperature=temperature
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")

