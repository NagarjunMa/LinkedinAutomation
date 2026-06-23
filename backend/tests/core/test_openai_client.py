import pytest

from app.core import openai_client
from app.core.config import settings


def test_openai_client_fails_when_ai_enabled_without_key(monkeypatch):
    openai_client.clear_openai_client_cache()
    monkeypatch.setattr(settings, "ENABLE_AI_FEATURES", True)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

    with pytest.raises(openai_client.OpenAIConfigurationError):
        openai_client.get_openai_client()

    openai_client.clear_openai_client_cache()


def test_openai_client_is_cached(monkeypatch):
    openai_client.clear_openai_client_cache()
    monkeypatch.setattr(settings, "ENABLE_AI_FEATURES", True)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test")

    first = openai_client.get_openai_client()
    second = openai_client.get_openai_client()

    assert first is second
    openai_client.clear_openai_client_cache()
