import uuid
import enum
from datetime import datetime, UTC

from pydantic import BaseModel, Field

from lightspeed_agents.permissions.tiers import ActionTier


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    task_id: str = ""
    agent_id: str = ""
    tool_name: str = ""
    tier: ActionTier = ActionTier.T2_GATE
    instruction: str = ""
    required_approvals: int = 1
    approvals: list[dict] = []
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = ""
    expires_at: str = ""

    def __init__(self, **data):
        now = datetime.now(UTC).isoformat()
        if not data.get("created_at"):
            data["created_at"] = now
        super().__init__(**data)

    @property
    def approval_count(self) -> int:
        return len([a for a in self.approvals if a.get("decision") == "approved"])

    @property
    def rejection_count(self) -> int:
        return len([a for a in self.approvals if a.get("decision") == "rejected"])

    @property
    def is_fully_approved(self) -> bool:
        return self.approval_count >= self.required_approvals

    @property
    def is_rejected(self) -> bool:
        return self.rejection_count > 0

    def add_approval(
        self,
        approver_id: str,
        decision: str,
        note: str = "",
    ):
        self.approvals.append(
            {
                "approver_id": approver_id,
                "decision": decision,
                "note": note,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        if self.is_rejected:
            self.status = ApprovalStatus.REJECTED
        elif self.is_fully_approved:
            self.status = ApprovalStatus.APPROVED
