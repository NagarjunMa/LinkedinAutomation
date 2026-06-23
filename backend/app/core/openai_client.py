from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import settings


class OpenAIConfigurationError(RuntimeError):
    """Raised when an AI feature is called without usable OpenAI settings."""


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    if settings.ENABLE_AI_FEATURES and not settings.OPENAI_API_KEY:
        raise OpenAIConfigurationError("OPENAI_API_KEY is required when AI features are enabled")
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def clear_openai_client_cache() -> None:
    get_openai_client.cache_clear()
