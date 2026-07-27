import pytest
from pathlib import Path

from lightspeed_agents.models.resolver import ModelResolver


@pytest.fixture
def resolver():
    return ModelResolver("company/models.yaml")


def test_resolve_cto_premium(resolver):
    resolved = resolver.resolve("cto")
    assert resolved.tier == "premium"
    assert resolved.provider == "openai"
    assert resolved.model == "gpt-4o"


def test_resolve_cfo_premium(resolver):
    resolved = resolver.resolve("cfo")
    assert resolved.tier == "premium"


def test_resolve_coo_standard(resolver):
    resolved = resolver.resolve("coo")
    assert resolved.tier == "standard"
    assert resolved.model == "gpt-4o-mini"


def test_resolve_content_writer_fast(resolver):
    resolved = resolver.resolve("content-writer")
    assert resolved.tier == "fast"
    assert resolved.provider == "ollama"


def test_resolve_no_override_fallback(resolver):
    resolved = resolver.resolve("human-ceo")
    assert resolved.tier == "default"
    assert resolved.provider == "ollama"


def test_resolve_custom_fallback():
    resolver = ModelResolver("nonexistent.yaml")
    resolved = resolver.resolve("any-agent", fallback_model="openai")
    assert resolved.tier == "default"
    assert resolved.provider == "openai"
    assert resolved.model == "openai"


def test_resolver_empty_config(tmp_path):
    config = tmp_path / "empty.yaml"
    config.write_text("tiers: {}\nagent_overrides: {}\n", encoding="utf-8")
    resolver = ModelResolver(str(config))
    resolved = resolver.resolve("agent")
    assert resolved.tier == "default"
