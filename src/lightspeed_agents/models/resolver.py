from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ResolvedModel:
    provider: str
    model: str
    tier: str
    description: str


_AVAILABLE_PROVIDERS = {"ollama", "openai"}


class ModelResolver:

    def __init__(self, config_path: str = "company/models.yaml"):
        path = Path(config_path)

        if not path.exists():
            self.tiers = {}
            self.overrides = {}
            return

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        self.tiers = data.get("tiers", {})
        self.overrides = data.get("agent_overrides", {})

    def resolve(self, agent_id: str, fallback_model: str = "ollama") -> ResolvedModel:
        tier_name = self.overrides.get(agent_id)

        if not tier_name or tier_name not in self.tiers:
            return ResolvedModel(
                provider=fallback_model,
                model=fallback_model,
                tier="default",
                description="Default model",
            )

        tier = self.tiers[tier_name]
        providers = tier.get("providers", [])

        for entry in providers:
            if entry["provider"] in _AVAILABLE_PROVIDERS:
                return ResolvedModel(
                    provider=entry["provider"],
                    model=entry["model"],
                    tier=tier_name,
                    description=tier.get("description", ""),
                )

        if providers:
            first = providers[0]
            return ResolvedModel(
                provider=first["provider"],
                model=first["model"],
                tier=tier_name,
                description=tier.get("description", ""),
            )

        return ResolvedModel(
            provider=fallback_model,
            model=fallback_model,
            tier=tier_name,
            description=tier.get("description", ""),
        )
