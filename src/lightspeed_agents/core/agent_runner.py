from lightspeed_agents.registry.registry import registry
from lightspeed_agents.agents.loader import load_agents
from lightspeed_agents.providers.registry import get_provider
from lightspeed_agents.models.resolver import ModelResolver
from lightspeed_agents.prompts.builder import PromptBuilder
from lightspeed_agents.memory.memory import AgentMemory


class AgentRunner:

    def __init__(self, memory_dir: str = "memory"):
        load_agents()
        self.resolver = ModelResolver()
        self.prompt_builder = PromptBuilder()
        self.memory_dir = memory_dir

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

        memory = AgentMemory(agent_id, self.memory_dir)
        context = memory.get_context(limit=10)

        prompt = task
        if context:
            prompt = (
                f"Previous conversation:\n{context}\n\n"
                f"Current task:\n{task}"
            )

        response = provider.complete(
            prompt=prompt,
            system=system,
            model=resolved.model,
        )

        memory.add("user", task)
        memory.add("assistant", response)

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
