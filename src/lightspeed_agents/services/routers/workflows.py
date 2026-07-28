"""Workflows API router — D5-020 List Workflows."""

from fastapi import APIRouter, Depends

from lightspeed_agents.services.dependencies import get_workflow_engine
from lightspeed_agents.services.schemas.workflows import (
    WorkflowListResponse,
    WorkflowResponse,
)
from lightspeed_agents.workflow.engine import WorkflowEngine

workflows_router = APIRouter(prefix="/workflows", tags=["workflows"])


@workflows_router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    engine: WorkflowEngine = Depends(get_workflow_engine),  # noqa: B008
) -> WorkflowListResponse:
    """List all available workflows with step counts."""
    workflows = engine.list_workflows()
    items = [WorkflowResponse.from_workflow(wf) for wf in workflows]
    return WorkflowListResponse(workflows=items, total=len(items))
