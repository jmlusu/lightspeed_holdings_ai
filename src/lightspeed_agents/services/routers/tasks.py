"""Tasks router with protected write endpoints.

Provides a placeholder tasks router that demonstrates API key authentication.
"""

from fastapi import APIRouter, Depends

from lightspeed_agents.services.auth import verify_api_key

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/")
async def list_tasks(auth: str = Depends(verify_api_key)):
    """List tasks (GET is public by convention; auth here for demonstration)."""
    return {"tasks": [], "auth": auth}


@router.post("/")
async def create_task(auth: str = Depends(verify_api_key)):
    """Create a task (write endpoint -- requires authentication)."""
    return {"message": "Task created", "auth": auth}


@router.patch("/{task_id}")
async def update_task(task_id: str, auth: str = Depends(verify_api_key)):
    """Update a task (write endpoint -- requires authentication)."""
    return {"message": f"Task {task_id} updated", "auth": auth}


@router.delete("/{task_id}")
async def delete_task(task_id: str, auth: str = Depends(verify_api_key)):
    """Delete a task (write endpoint -- requires authentication)."""
    return {"message": f"Task {task_id} deleted", "auth": auth}
