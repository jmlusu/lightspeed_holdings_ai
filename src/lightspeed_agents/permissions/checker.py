from lightspeed_agents.models.agent import Agent
from lightspeed_agents.permissions.tiers import ActionTier, TIER_RISK_LEVELS
from lightspeed_agents.permissions.tool_registry import ToolRegistry


class PermissionChecker:

    def __init__(self, tool_registry: ToolRegistry = None):
        self.tool_registry = tool_registry or ToolRegistry()

    def check_tool_permission(
        self,
        agent: Agent,
        tool_name: str,
    ) -> tuple[bool, ActionTier, str]:
        tool_tier = self.tool_registry.get_tier(tool_name)

        if tool_name not in agent.tools and tool_name not in agent.permissions:
            return (
                False,
                tool_tier,
                (f"Agent '{agent.id}' does not have access to tool '{tool_name}'"),
            )

        return True, tool_tier, ""

    def check_action_tier(
        self,
        agent: Agent,
        tier: ActionTier,
    ) -> tuple[bool, str]:
        agent_max_tier = self._get_agent_max_tier(agent)

        if TIER_RISK_LEVELS[tier] > TIER_RISK_LEVELS[agent_max_tier]:
            return False, (
                f"Agent '{agent.id}' (max tier {agent_max_tier.value}) "
                f"cannot perform T{tier.value[-1]} actions"
            )

        return True, ""

    def requires_approval(
        self,
        agent: Agent,
        tool_name: str,
    ) -> tuple[bool, ActionTier]:
        has_permission, tier, _ = self.check_tool_permission(agent, tool_name)

        if not has_permission:
            return True, tier

        if TIER_RISK_LEVELS[tier] >= TIER_RISK_LEVELS[ActionTier.T2_GATE]:
            return True, tier

        return False, tier

    def validate_action(
        self,
        agent: Agent,
        tool_name: str,
    ) -> tuple[bool, ActionTier, str]:
        has_tool, tier, error = self.check_tool_permission(agent, tool_name)
        if not has_tool:
            return False, tier, error

        tier_ok, tier_error = self.check_action_tier(agent, tier)
        if not tier_ok:
            return False, tier, tier_error

        return True, tier, ""

    def _get_agent_max_tier(self, agent: Agent) -> ActionTier:
        if agent.type == "Executive":
            return ActionTier.T3_DUAL

        if agent.id == "human-ceo":
            return ActionTier.T4_BOARD

        permission_tiers = []
        for perm in agent.permissions:
            if perm == "approve":
                permission_tiers.append(ActionTier.T2_GATE)
            elif perm == "decide":
                permission_tiers.append(ActionTier.T4_BOARD)
            elif perm == "edit":
                permission_tiers.append(ActionTier.T2_GATE)
            elif perm == "coordinate":
                permission_tiers.append(ActionTier.T3_DUAL)
            elif perm == "read":
                permission_tiers.append(ActionTier.T0_AUTO)

        if permission_tiers:
            return max(permission_tiers, key=lambda t: TIER_RISK_LEVELS[t])

        return ActionTier.T1_SOFT
