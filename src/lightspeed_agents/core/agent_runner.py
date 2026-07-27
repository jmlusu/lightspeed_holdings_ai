from lightspeed_agents.registry.registry import registry
from lightspeed_agents.agents.loader import load_agents
from lightspeed_agents.providers.registry import get_provider
from lightspeed_agents.models.resolver import ModelResolver
from lightspeed_agents.prompts.builder import PromptBuilder


class AgentRunner:

    def __init__(self):
        load_agents()
        self.resolver = ModelResolver()
        self.prompt_builder = PromptBuilder()

    def run(self, agent_id: str, task: str):

        agent = registry.find(agent_id)

        if not agent:
            raise ValueError(
                f"Agent '{agent_id}' not found"
            )

        resolved = self.resolver.resolve(
            agent_id,
            fallback_model=agent.model,
        )

        provider = get_provider(resolved.provider)

        system = self.prompt_builder.build(agent)

        response = provider.complete(
            prompt=task,
            system=system,
            model=resolved.model,
        )

        return {
            "agent": agent.id,
            "name": agent.name,
            "role": agent.role,
            "task": task,
            "response": response,
            "model_info": {
                "provider": resolved.provider,
                "model": resolved.model,
                "tier": resolved.tier,
            },
        }
