import json
import pytest
from pathlib import Path

from lightspeed_agents.agents.loader import load_agents
from lightspeed_agents.registry.registry import registry


@pytest.fixture(autouse=True)
def clean_registry():
    registry.agents = []
    yield
    registry.agents = []


def test_load_agents_from_config():
    load_agents("company/agent-registry.json")
    assert len(registry.list()) == 14


def test_load_agents_ids():
    load_agents("company/agent-registry.json")
    ids = [a.id for a in registry.list()]
    assert "human-ceo" in ids
    assert "cto" in ids
    assert "cfo" in ids
    assert "content-writer" in ids


def test_load_agents_missing_file():
    load_agents("nonexistent.json")
    assert len(registry.list()) == 0


def test_load_agents_from_tmp(tmp_path):
    data = {
        "agents": {
            "agents": [
                {
                    "id": "test-agent",
                    "name": "Test Agent",
                    "role": "Tester",
                    "type": "Specialist",
                    "department": "qa",
                    "reportsTo": None,
                    "tools": ["testing"],
                    "permissions": ["read"],
                }
            ]
        }
    }
    config_file = tmp_path / "test-registry.json"
    config_file.write_text(json.dumps(data), encoding="utf-8")

    load_agents(str(config_file))
    assert len(registry.list()) == 1
    assert registry.list()[0].id == "test-agent"
