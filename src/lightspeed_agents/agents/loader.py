import json
from pathlib import Path

from lightspeed_agents.models.agent import Agent
from lightspeed_agents.registry.registry import registry


def load_agents(config_path: str = "company/agent-registry.json"):

    path = Path(config_path)

    if not path.exists():
        return registry

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for entry in data["agents"]["agents"]:
        agent = Agent(**entry)
        registry.register(agent)

    return registry
