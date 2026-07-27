import json
from pathlib import Path

import yaml


class PromptBuilder:

    def __init__(self, config_dir: str = "company"):
        self.config_dir = Path(config_dir)
        self._departments = None
        self._workflows = None
        self._kpis = None

    def build(self, agent) -> str:
        sections = [
            self._identity(agent),
            self._role_context(agent),
            self._department_context(agent),
            self._kpi_context(agent),
            self._workflow_context(agent),
            self._hierarchy_context(agent),
            self._guidelines(),
        ]

        return "\n\n".join(s for s in sections if s)

    def _identity(self, agent) -> str:
        return (
            f"# System Prompt\n\n"
            f"You are {agent.name}, serving as {agent.role} "
            f"at LightSpeed Holdings."
        )

    def _role_context(self, agent) -> str:
        lines = ["## Role & Responsibilities"]

        lines.append(f"- **Type:** {agent.type}")
        lines.append(f"- **Department:** {agent.department}")

        if agent.tools:
            lines.append(f"- **Tools:** {', '.join(agent.tools)}")

        if agent.permissions:
            lines.append(f"- **Permissions:** {', '.join(agent.permissions)}")

        return "\n".join(lines)

    def _department_context(self, agent) -> str:
        departments = self._load_departments()
        dept = departments.get(agent.department)

        if not dept:
            return ""

        lines = [f"## Department: {dept['name']}"]

        if dept.get("executive"):
            lines.append(f"- **Executive:** {dept['executive']}")

        if dept.get("agents"):
            teammates = [a for a in dept["agents"] if a != agent.id]
            if teammates:
                lines.append(f"- **Team:** {', '.join(teammates)}")

        return "\n".join(lines)

    def _kpi_context(self, agent) -> str:
        kpis = self._load_kpis()
        dept_kpis = kpis.get(agent.department)

        if not dept_kpis:
            return ""

        lines = [f"## Department KPIs"]

        for kpi in dept_kpis.get("kpis", []):
            lines.append(
                f"- **{kpi['name']}:** target {kpi['target']}{kpi['unit']} "
                f"({kpi['frequency']})"
            )

        return "\n".join(lines)

    def _workflow_context(self, agent) -> str:
        workflows = self._load_workflows()
        owned = [w for w in workflows if w.get("owner") == agent.id]

        if not owned:
            return ""

        lines = ["## Owned Workflows"]

        for wf in owned:
            raw_steps = wf.get("steps", [])
            step_ids = []
            for s in raw_steps:
                if isinstance(s, dict):
                    step_ids.append(s.get("id", ""))
                else:
                    step_ids.append(str(s))
            steps = " -> ".join(step_ids)
            lines.append(f"- **{wf['name']}:** {steps}")

        return "\n".join(lines)

    def _hierarchy_context(self, agent) -> str:
        if not agent.reports_to:
            return (
                "## Organizational Position\n\n"
                "You are at the top of the organization chart."
            )

        return (
            "## Organizational Position\n\n"
            f"- **Reports to:** {agent.reports_to}"
        )

    def _guidelines(self) -> str:
        return (
            "## Guidelines\n\n"
            "- Be concise and actionable in your responses.\n"
            "- Reference your KPIs when prioritizing work.\n"
            "- Escalate blockers to your reporting line.\n"
            "- Use your tools and permissions appropriately."
        )

    def _load_departments(self) -> dict:
        if self._departments is None:
            raw = self._load_yaml("departments.yaml")
            dept_list = raw.get("departments", [])
            if isinstance(dept_list, list):
                self._departments = {d["name"]: d for d in dept_list}
            else:
                self._departments = dept_list
        return self._departments

    def _load_kpis(self) -> dict:
        if self._kpis is None:
            self._kpis = self._load_yaml("config/kpis.yaml")
        return self._kpis.get("departments", {})

    def _load_workflows(self) -> list:
        if self._workflows is None:
            self._workflows = self._load_yaml("workflows.yaml")
        return self._workflows.get("workflows", [])

    def _load_yaml(self, filename: str) -> dict:
        path = self.config_dir / filename

        if not path.exists():
            return {}

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
