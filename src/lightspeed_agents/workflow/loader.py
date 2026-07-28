import os
import yaml
from typing import Optional

from lightspeed_agents.workflow.models import Workflow, WorkflowStep
from lightspeed_agents.workflow.retry import RetryPolicy

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
                step_data = dict(step_raw)
                if "retry" in step_data and isinstance(step_data["retry"], dict):
                    step_data["retry_policy"] = RetryPolicy(**step_data.pop("retry"))
                elif "retry" in step_data:
                    step_data.pop("retry")
                steps.append(WorkflowStep(**step_data))

        workflows.append(
            Workflow(
                id=wf_raw["id"],
                name=wf_raw.get("name", ""),
                description=wf_raw.get("description", ""),
                owner=wf_raw.get("owner", ""),
                version=wf_raw.get("version", "1.0"),
                steps=steps,
            )
        )

    return workflows


def get_workflow(workflow_id: str, path: str = None) -> Optional[Workflow]:
    workflows = load_workflows(path)
    for wf in workflows:
        if wf.id == workflow_id:
            return wf
    return None
