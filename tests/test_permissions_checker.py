from lightspeed_agents.models.agent import Agent
from lightspeed_agents.permissions.tiers import ActionTier
from lightspeed_agents.permissions.checker import PermissionChecker
from lightspeed_agents.permissions.tool_registry import ToolRegistry


def make_agent(**kwargs):
    defaults = {
        "id": "test-agent",
        "name": "Test Agent",
        "role": "tester",
        "type": "Specialist",
        "tools": ["read", "write"],
        "permissions": ["read", "edit"],
    }
    defaults.update(kwargs)
    return Agent(**defaults)


class TestPermissionChecker:

    def test_check_tool_permission_granted(self):
        checker = PermissionChecker()
        agent = make_agent(tools=["read", "write"])
        ok, tier, error = checker.check_tool_permission(agent, "read")
        assert ok is True
        assert tier == ActionTier.T0_AUTO

    def test_check_tool_permission_denied(self):
        checker = PermissionChecker()
        agent = make_agent(tools=["read"])
        ok, tier, error = checker.check_tool_permission(agent, "shell")
        assert ok is False
        assert "does not have access" in error

    def test_check_tool_permission_via_permissions_field(self):
        checker = PermissionChecker()
        agent = make_agent(tools=[], permissions=["python"])
        ok, tier, error = checker.check_tool_permission(agent, "python")
        assert ok is True

    def test_check_action_tier_within_agent_limit(self):
        checker = PermissionChecker()
        agent = make_agent(type="Executive", permissions=["edit", "coordinate"])
        ok, error = checker.check_action_tier(agent, ActionTier.T2_GATE)
        assert ok is True

    def test_check_action_tier_exceeds_agent_limit(self):
        checker = PermissionChecker()
        agent = make_agent(type="Specialist", permissions=["read"])
        ok, error = checker.check_action_tier(agent, ActionTier.T3_DUAL)
        assert ok is False
        assert "cannot perform" in error

    def test_ceo_can_do_t3(self):
        checker = PermissionChecker()
        agent = make_agent(id="human-ceo", type="Executive")
        ok, error = checker.check_action_tier(agent, ActionTier.T3_DUAL)
        assert ok is True

    def test_ceo_max_tier(self):
        checker = PermissionChecker()
        agent = make_agent(id="human-ceo", type="Executive")
        ok, error = checker.check_action_tier(agent, ActionTier.T4_BOARD)
        assert ok is False

    def test_requires_approval_t0_no(self):
        checker = PermissionChecker()
        agent = make_agent(tools=["read"], permissions=["read"])
        needs, tier = checker.requires_approval(agent, "read")
        assert needs is False

    def test_requires_approval_t2_yes(self):
        checker = PermissionChecker()
        agent = make_agent(tools=["python"], permissions=["read"])
        needs, tier = checker.requires_approval(agent, "python")
        assert needs is True
        assert tier == ActionTier.T2_GATE

    def test_requires_approval_t3_yes(self):
        checker = PermissionChecker()
        agent = make_agent(tools=["shell"], permissions=["read", "coordinate"])
        needs, tier = checker.requires_approval(agent, "shell")
        assert needs is True
        assert tier == ActionTier.T3_DUAL

    def test_requires_approval_denied_still_needs_approval(self):
        checker = PermissionChecker()
        agent = make_agent(tools=["read"])
        needs, tier = checker.requires_approval(agent, "shell")
        assert needs is True

    def test_validate_action_full_success(self):
        checker = PermissionChecker()
        agent = make_agent(tools=["read", "python"], permissions=["read"])
        ok, tier, error = checker.validate_action(agent, "read")
        assert ok is True
        assert tier == ActionTier.T0_AUTO

    def test_validate_action_permission_denied(self):
        checker = PermissionChecker()
        agent = make_agent(tools=["read"])
        ok, tier, error = checker.validate_action(agent, "shell")
        assert ok is False
        assert "does not have access" in error

    def test_validate_action_tier_exceeded(self):
        checker = PermissionChecker()
        agent = make_agent(
            id="human-ceo",
            type="Executive",
            tools=["approve"],
            permissions=["approve"],
        )
        ok, tier, error = checker.validate_action(agent, "approve")
        assert ok is False
        assert "cannot perform" in error

    def test_custom_tool_registry(self):
        custom = {"my_tool": ActionTier.T0_AUTO}
        registry = ToolRegistry(custom_tiers=custom)
        checker = PermissionChecker(tool_registry=registry)
        agent = make_agent(tools=["my_tool"], permissions=["read"])
        ok, tier, error = checker.validate_action(agent, "my_tool")
        assert ok is True
        assert tier == ActionTier.T0_AUTO
