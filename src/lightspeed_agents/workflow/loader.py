import os
import yaml
from typing import Optional

from lightspeed_agents.workflow.models import Workflow, WorkflowStep


DEFAULT_WORKFLOWS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "company", "workflows.yaml"
)


def load_workflows(path: str = None) -> list[Workflow]:
    path = path or DEFAULT_WORKFLOWS_PATH
    path = os.path.abspath(path)

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "workflows" not in data:
        return []

    workflows = []
    for wf_raw in data["workflows"]:
        steps = []
        for step_raw in wf_raw.get("steps", []):
            if isinstance(step_raw, str):
                steps.append(WorkflowStep(id=step_raw))
            else:
                steps.append(WorkflowStep(**step_raw))

        workflows.append(Workflow(
            id=wf_raw["id"],
            name=wf_raw.get("name", ""),
            description=wf_raw.get("description", ""),
            owner=wf_raw.get("owner", ""),
            steps=steps,
        ))

    return workflows


def get_workflow(workflow_id: str, path: str = None) -> Optional[Workflow]:
    workflows = load_workflows(path)
    for wf in workflows:
        if wf.id == workflow_id:
            return wf
    return None
