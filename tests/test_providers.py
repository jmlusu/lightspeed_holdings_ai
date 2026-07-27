import pytest
from unittest.mock import patch, MagicMock

from lightspeed_agents.providers.base import LLMProvider
from lightspeed_agents.providers.registry import get_provider, register_provider


class FakeProvider(LLMProvider):
    def complete(self, prompt, system="", model="", temperature=0.7, max_tokens=2048):
        return f"fake response to: {prompt}"


def test_register_and_get_provider():
    register_provider("fake", FakeProvider)
    provider = get_provider("fake")
    assert isinstance(provider, FakeProvider)


def test_get_provider_returns_instance():
    register_provider("fake", FakeProvider)
    p1 = get_provider("fake")
    p2 = get_provider("fake")
    assert p1 is not p2


def test_get_provider_unknown():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("nonexistent")


@patch("lightspeed_agents.providers.ollama.requests")
def test_ollama_provider(mock_requests):
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "hello from ollama"}}
    mock_requests.post.return_value = mock_response

    from lightspeed_agents.providers.ollama import OllamaProvider

    provider = OllamaProvider()
    result = provider.complete("test prompt", model="llama3")

    assert result == "hello from ollama"
    mock_requests.post.assert_called_once()
    call_args = mock_requests.post.call_args
    assert "/api/chat" in call_args[0][0]


@patch("openai.OpenAI")
def test_openai_provider(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    mock_choice = MagicMock()
    mock_choice.message.content = "hello from openai"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    from lightspeed_agents.providers.openai import OpenAIProvider

    provider = OpenAIProvider()
    result = provider.complete("test prompt", model="gpt-4o-mini")

    assert result == "hello from openai"
    mock_client.chat.completions.create.assert_called_once()
