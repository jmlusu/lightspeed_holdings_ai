from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Department(str, Enum):
    EXECUTIVE = "executive"
    ENGINEERING = "engineering"
    OPERATIONS = "operations"
    PRODUCT = "product"


DEPARTMENT_AGENTS: dict[Department, list[str]] = {
    Department.EXECUTIVE: [
        "human-ceo", "ceo-advisor", "chief-of-staff", "cto", "cfo", "coo",
    ],
    Department.ENGINEERING: [
        "chief-architect", "lead-engineer", "backend-engineer",
        "frontend-engineer", "ai-engineer", "data-engineer",
    ],
    Department.OPERATIONS: [
        "devops-engineer", "security-engineer",
    ],
    Department.PRODUCT: [
        "product-manager", "technical-writer", "qa-engineer",
    ],
}

_AGENT_TO_DEPARTMENT: dict[str, Department] = {}
for _dept, _agents in DEPARTMENT_AGENTS.items():
    for _agent in _agents:
        _AGENT_TO_DEPARTMENT[_agent] = _dept


class EscalationLevel(str, Enum):
    DEPARTMENT = "department"
    CROSS_DEPARTMENT = "cross_department"
    BUSINESS_CRITICAL = "business_critical"


class HandoffStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    FAILED = "failed"


class HandoffContext(BaseModel):
    from_dept: Department
    to_dept: Department
    payload: dict = {}
    timestamp: str = ""
    status: HandoffStatus = HandoffStatus.PENDING
    sender_agent: str = ""
    receiver_agent: str = ""


CROSS_DEPT_HANDOFFS: dict[tuple[Department, Department], bool] = {
    (Department.EXECUTIVE, Department.ENGINEERING): True,
    (Department.EXECUTIVE, Department.OPERATIONS): True,
    (Department.EXECUTIVE, Department.PRODUCT): True,
    (Department.ENGINEERING, Department.EXECUTIVE): True,
    (Department.ENGINEERING, Department.OPERATIONS): True,
    (Department.ENGINEERING, Department.PRODUCT): True,
    (Department.OPERATIONS, Department.EXECUTIVE): True,
    (Department.OPERATIONS, Department.ENGINEERING): True,
    (Department.OPERATIONS, Department.PRODUCT): True,
    (Department.PRODUCT, Department.EXECUTIVE): True,
    (Department.PRODUCT, Department.ENGINEERING): True,
    (Department.PRODUCT, Department.OPERATIONS): True,
}


def get_department(agent_id: str) -> Department:
    return _AGENT_TO_DEPARTMENT.get(agent_id, Department.EXECUTIVE)


def get_department_agents(department: Department) -> list[str]:
    return list(DEPARTMENT_AGENTS.get(department, []))


def can_handoff(from_dept: Department, to_dept: Department) -> bool:
    return CROSS_DEPT_HANDOFFS.get((from_dept, to_dept), False)


def get_escalation_level(
    from_dept: Department,
    to_dept: Department,
) -> EscalationLevel:
    if from_dept == to_dept:
        return EscalationLevel.DEPARTMENT
    if to_dept == Department.EXECUTIVE:
        return EscalationLevel.CROSS_DEPARTMENT
    return EscalationLevel.CROSS_DEPARTMENT


CROSS_DEPT_PATTERNS = [
    {
        "id": "sequential_handoff",
        "name": "Sequential Handoff",
        "description": "Department A finishes work, then Department B starts",
        "steps": [
            {"department": "trigger", "instruction": "Trigger workflow", "assignee": "chief-of-staff"},
            {"department": "source", "instruction": "Complete department work", "assignee": "lead-engineer", "depends_on": ["trigger"]},
            {"department": "target", "instruction": "Receive and continue", "assignee": "product-manager", "depends_on": ["source"]},
        ],
    },
    {
        "id": "parallel_execution",
        "name": "Parallel Execution",
        "description": "Multiple departments work simultaneously, merge at join point",
        "steps": [
            {"department": "trigger", "instruction": "Trigger workflow", "assignee": "chief-of-staff"},
            {"department": "engineering", "instruction": "Engineering implementation", "assignee": "backend-engineer", "depends_on": ["trigger"]},
            {"department": "product", "instruction": "Product specifications", "assignee": "product-manager", "depends_on": ["trigger"]},
            {"department": "merge", "instruction": "Merge and validate", "assignee": "qa-engineer", "depends_on": ["engineering", "product"]},
        ],
    },
    {
        "id": "review_gate",
        "name": "Review Gate",
        "description": "Department A produces, Department B reviews, then implementation proceeds",
        "steps": [
            {"department": "trigger", "instruction": "Trigger workflow", "assignee": "product-manager"},
            {"department": "source", "instruction": "Produce deliverable", "assignee": "lead-engineer", "depends_on": ["trigger"]},
            {"department": "reviewer", "instruction": "Review and approve", "assignee": "security-engineer", "depends_on": ["source"]},
            {"department": "implementer", "instruction": "Implement approved changes", "assignee": "backend-engineer", "depends_on": ["reviewer"]},
        ],
    },
    {
        "id": "incident_response",
        "name": "Incident Response",
        "description": "Operations detects, engineering investigates, security reviews",
        "steps": [
            {"department": "operations", "instruction": "Detect and classify incident", "assignee": "devops-engineer"},
            {"department": "executive", "instruction": "Notify stakeholders", "assignee": "chief-of-staff", "depends_on": ["operations"]},
            {"department": "engineering", "instruction": "Investigate root cause", "assignee": "backend-engineer", "depends_on": ["executive"]},
            {"department": "engineering", "instruction": "Implement fix", "assignee": "backend-engineer", "depends_on": ["investigate"]},
            {"department": "operations", "instruction": "Verify resolution", "assignee": "qa-engineer", "depends_on": ["implement_fix"]},
        ],
    },
]


def get_cross_dept_workflows() -> list[dict]:
    return CROSS_DEPT_PATTERNS
