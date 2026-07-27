from lightspeed_agents.providers.base import LLMProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {}


def register_provider(name: str, cls: type[LLMProvider]):
    _PROVIDERS[name] = cls


def get_provider(name: str) -> LLMProvider:
    if name not in _PROVIDERS:
        _lazy_load(name)

    if name not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {name}")

    return _PROVIDERS[name]()


def _lazy_load(name: str):
    if name == "ollama":
        from lightspeed_agents.providers.ollama import OllamaProvider

        register_provider("ollama", OllamaProvider)
    elif name == "openai":
        from lightspeed_agents.providers.openai import OpenAIProvider

        register_provider("openai", OpenAIProvider)
