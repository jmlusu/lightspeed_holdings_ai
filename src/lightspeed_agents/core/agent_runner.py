from lightspeed_agents.registry.registry import registry
from lightspeed_agents.agents.loader import load_agents
from lightspeed_agents.providers.registry import get_provider
from lightspeed_agents.models.resolver import ModelResolver
from lightspeed_agents.prompts.builder import PromptBuilder
from lightspeed_agents.memory.engine import MemoryEngine


class AgentRunner:

    def __init__(self, memory_dir: str = "memory"):
        load_agents()
        self.resolver = ModelResolver()
        self.prompt_builder = PromptBuilder()
        self.memory = MemoryEngine(memory_dir)

    def run(self, agent_id: str, task: str):

        agent = registry.find(agent_id)

        if not agent:
            raise ValueError(f"Agent '{agent_id}' not found")

        resolved = self.resolver.resolve(
            agent_id,
            fallback_model=agent.model,
        )

        provider = get_provider(resolved.provider)

        system = self.prompt_builder.build(agent)

        context_entries = self.memory.recall_context(
            query=task,
            agent_id=agent_id,
        )

        prompt = task
        if context_entries:
            context_lines = [f"- {e.content[:200]}" for e in context_entries]
            context_text = "\n".join(context_lines)
            prompt = (
                f"Relevant organizational memory:\n{context_text}\n\n"
                f"Current task:\n{task}"
            )

        response = provider.complete(
            prompt=prompt,
            system=system,
            model=resolved.model,
        )

        self.memory.record_task_outcome(
            task_id=f"task-{agent_id}",
            agent_id=agent_id,
            content=f"Task: {task}\nResponse: {response[:500]}",
            status="completed",
            department=agent.department,
            tags=[agent.department, "run"],
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
