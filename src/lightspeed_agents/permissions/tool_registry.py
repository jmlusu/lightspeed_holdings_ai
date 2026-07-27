from lightspeed_agents.permissions.tiers import ActionTier


DEFAULT_TOOL_TIERS = {
    "read": ActionTier.T0_AUTO,
    "list": ActionTier.T0_AUTO,
    "grep": ActionTier.T0_AUTO,
    "search": ActionTier.T0_AUTO,
    "dashboard": ActionTier.T0_AUTO,
    "write": ActionTier.T1_SOFT,
    "edit": ActionTier.T1_SOFT,
    "planning": ActionTier.T1_SOFT,
    "reporting": ActionTier.T1_SOFT,
    "finance": ActionTier.T1_SOFT,
    "marketing": ActionTier.T1_SOFT,
    "operations": ActionTier.T1_SOFT,
    "writing": ActionTier.T1_SOFT,
    "python": ActionTier.T2_GATE,
    "git": ActionTier.T2_GATE,
    "javascript": ActionTier.T2_GATE,
    "sql": ActionTier.T2_GATE,
    "llm": ActionTier.T2_GATE,
    "docker": ActionTier.T3_DUAL,
    "shell": ActionTier.T3_DUAL,
    "deploy": ActionTier.T3_DUAL,
    "execute": ActionTier.T3_DUAL,
    "legal": ActionTier.T4_BOARD,
    "budget": ActionTier.T4_BOARD,
    "approve": ActionTier.T4_BOARD,
    "decide": ActionTier.T4_BOARD,
}


class ToolRegistry:

    def __init__(self, custom_tiers: dict[str, ActionTier] = None):
        self.tiers = dict(DEFAULT_TOOL_TIERS)
        if custom_tiers:
            self.tiers.update(custom_tiers)

    def get_tier(self, tool_name: str) -> ActionTier:
        return self.tiers.get(tool_name, ActionTier.T1_SOFT)

    def register_tool(self, tool_name: str, tier: ActionTier):
        self.tiers[tool_name] = tier

    def get_all_tools(self) -> dict[str, ActionTier]:
        return dict(self.tiers)
