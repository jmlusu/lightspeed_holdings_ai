"""Agent API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from lightspeed_agents.models.agent import Agent
from lightspeed_agents.registry.registry import AgentRegistry
from lightspeed_agents.services.dependencies import get_agent_registry
from lightspeed_agents.services.schemas.agents import AgentListResponse, AgentResponse

router = APIRouter(prefix="/agents", tags=["agents"])


def _agent_to_response(agent: Agent) -> AgentResponse:
    """Convert an Agent model to an AgentResponse schema."""
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        department=agent.department,
        tools=agent.tools,
        permissions=agent.permissions,
        reports_to=agent.reports_to,
        created_at=agent.created_at,
    )


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    department: Optional[str] = Query(None, description="Filter by department"),
    registry: AgentRegistry = Depends(get_agent_registry),  # noqa: B008
) -> AgentListResponse:
    """List all agents with optional department filter."""
    agents = registry.list()

    if department is not None:
        agents = [a for a in agents if a.department == department]

    response_agents = [_agent_to_response(a) for a in agents]
    return AgentListResponse(agents=response_agents, total=len(response_agents))
