from datetime import datetime, UTC, timedelta

from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.message_bus.file_store import FileStore
from lightspeed_agents.permissions.approval import ApprovalRequest, ApprovalStatus
from lightspeed_agents.permissions.tiers import (
    ActionTier,
    TIER_APPROVAL_COUNT,
    TIER_TIMEOUT_MINUTES,
)
from lightspeed_agents.memory.engine import MemoryEngine

APPROVALS_FILE = "approvals.json"


class HITLGate:

    def __init__(
        self,
        bus: MessageBus = None,
        memory: MemoryEngine = None,
        bus_dir: str = ".opencode",
    ):
        self.bus = bus or MessageBus(bus_dir)
        self.memory = memory or MemoryEngine()
        self.store = FileStore(bus_dir)

    def park_task(
        self,
        task_id: str,
        agent_id: str,
        tool_name: str,
        tier: ActionTier,
        instruction: str = "",
    ) -> ApprovalRequest:
        required = TIER_APPROVAL_COUNT.get(tier, 1)
        timeout_min = TIER_TIMEOUT_MINUTES.get(tier, 30)

        request = ApprovalRequest(
            task_id=task_id,
            agent_id=agent_id,
            tool_name=tool_name,
            tier=tier,
            instruction=instruction,
            required_approvals=required,
            expires_at=(datetime.now(UTC) + timedelta(minutes=timeout_min)).isoformat(),
        )

        self._save_request(request)
        self.bus.park_for_approval(task_id)

        self.memory.record_task_outcome(
            task_id=task_id,
            agent_id=agent_id,
            content=f"Parked for approval: {tool_name} [{tier.value}]",
            status="waiting_approval",
            tags=["hitl", tier.value],
        )

        return request

    def approve(
        self,
        request_id: str,
        approver_id: str,
        note: str = "",
    ) -> ApprovalRequest:
        request = self._get_request(request_id)
        if not request:
            raise ValueError(f"Approval request '{request_id}' not found")

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(
                f"Request '{request_id}' is already {request.status.value}"
            )

        request.add_approval(approver_id, "approved", note)
        self._save_request(request)

        if request.is_fully_approved:
            self.bus.approve_task(request.task_id)

        return request

    def reject(
        self,
        request_id: str,
        approver_id: str,
        note: str = "",
    ) -> ApprovalRequest:
        request = self._get_request(request_id)
        if not request:
            raise ValueError(f"Approval request '{request_id}' not found")

        request.add_approval(approver_id, "rejected", note)
        self._save_request(request)

        self.bus.fail_task(
            request.task_id,
            error=f"Rejected by {approver_id}: {note}",
        )

        return request

    def get_pending(self) -> list[ApprovalRequest]:
        return [r for r in self._load_requests() if r.status == ApprovalStatus.PENDING]

    def get_request(self, request_id: str) -> ApprovalRequest:
        return self._get_request(request_id)

    def get_all(self) -> list[ApprovalRequest]:
        return self._load_requests()

    def get_by_task(self, task_id: str) -> list[ApprovalRequest]:
        return [r for r in self._load_requests() if r.task_id == task_id]

    def check_expired(self) -> list[ApprovalRequest]:
        expired = []
        now = datetime.now(UTC)

        for request in self.get_pending():
            if request.expires_at:
                expires = datetime.fromisoformat(request.expires_at)
                if now > expires:
                    request.status = ApprovalStatus.EXPIRED
                    self._save_request(request)
                    self.bus.fail_task(
                        request.task_id,
                        error=f"Approval expired for {request.tool_name} [{request.tier.value}]",
                    )
                    expired.append(request)

        return expired

    def resume_approved(self) -> list[str]:
        resumed = []
        for request in self.get_pending():
            if request.is_fully_approved:
                self.bus.approve_task(request.task_id)
                resumed.append(request.task_id)
        return resumed

    def _get_request(self, request_id: str) -> ApprovalRequest:
        for r in self._load_requests():
            if r.id == request_id:
                return r
        return None

    def _save_request(self, request: ApprovalRequest):
        requests = self._load_requests()
        for i, existing in enumerate(requests):
            if existing.id == request.id:
                requests[i] = request
                break
        else:
            requests.append(request)
        self.store.save(
            APPROVALS_FILE,
            [r.model_dump(mode="json") for r in requests],
        )

    def _load_requests(self) -> list[ApprovalRequest]:
        raw = self.store.load(APPROVALS_FILE)
        return [ApprovalRequest(**r) for r in raw]
