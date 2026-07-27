from lightspeed_agents.models.agent import Agent


class AgentRegistry:

    def __init__(self):
        self.agents: list[Agent] = []

    def register(self, agent: Agent):
        self.agents.append(agent)

    def list(self):
        return self.agents

    def find(self, identifier: str) -> Agent | None:
        for agent in self.agents:
            if agent.id == identifier or agent.name.lower() == identifier.lower():
                return agent
        return None


registry = AgentRegistry()
