import pytest
from lightspeed_agents.permissions.tiers import ActionTier
from lightspeed_agents.permissions.approval import ApprovalRequest, ApprovalStatus


class TestApprovalRequest:

    def test_create_request(self):
        req = ApprovalRequest(
            task_id="t1",
            agent_id="agent-a",
            tool_name="python",
            tier=ActionTier.T2_GATE,
            required_approvals=1,
        )
        assert req.task_id == "t1"
        assert req.agent_id == "agent-a"
        assert req.tool_name == "python"
        assert req.tier == ActionTier.T2_GATE
        assert req.status == ApprovalStatus.PENDING

    def test_auto_generates_id(self):
        req = ApprovalRequest()
        assert len(req.id) == 12

    def test_auto_sets_created_at(self):
        req = ApprovalRequest()
        assert len(req.created_at) > 0

    def test_approval_count_empty(self):
        req = ApprovalRequest()
        assert req.approval_count == 0

    def test_add_single_approval(self):
        req = ApprovalRequest(required_approvals=1)
        req.add_approval("approver-1", "approved", "Looks good")
        assert req.approval_count == 1
        assert req.is_fully_approved is True
        assert req.status == ApprovalStatus.APPROVED

    def test_add_dual_approval(self):
        req = ApprovalRequest(required_approvals=2)
        req.add_approval("approver-1", "approved")
        assert req.approval_count == 1
        assert req.is_fully_approved is False

        req.add_approval("approver-2", "approved")
        assert req.approval_count == 2
        assert req.is_fully_approved is True
        assert req.status == ApprovalStatus.APPROVED

    def test_add_rejection(self):
        req = ApprovalRequest(required_approvals=1)
        req.add_approval("approver-1", "rejected", "Too risky")
        assert req.is_rejected is True
        assert req.status == ApprovalStatus.REJECTED

    def test_rejection_overrides_approval(self):
        req = ApprovalRequest(required_approvals=2)
        req.add_approval("approver-1", "approved")
        req.add_approval("approver-2", "rejected")
        assert req.is_rejected is True
        assert req.status == ApprovalStatus.REJECTED

    def test_rejection_count(self):
        req = ApprovalRequest()
        req.add_approval("a1", "rejected")
        req.add_approval("a2", "approved")
        req.add_approval("a3", "rejected")
        assert req.rejection_count == 2

    def test_board_approval(self):
        req = ApprovalRequest(required_approvals=3)
        req.add_approval("cfo", "approved")
        req.add_approval("cto", "approved")
        assert req.is_fully_approved is False

        req.add_approval("ceo", "approved")
        assert req.is_fully_approved is True
        assert req.status == ApprovalStatus.APPROVED

    def test_model_dump(self):
        req = ApprovalRequest(
            task_id="t1",
            tool_name="python",
            tier=ActionTier.T2_GATE,
        )
        data = req.model_dump(mode="json")
        assert data["task_id"] == "t1"
        assert data["tier"] == "T2"
        assert "id" in data
        assert "created_at" in data
