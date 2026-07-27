import pytest
from lightspeed_agents.permissions.tiers import ActionTier
from lightspeed_agents.permissions.tool_registry import ToolRegistry, DEFAULT_TOOL_TIERS


class TestToolRegistry:

    def test_default_tiers_loaded(self):
        registry = ToolRegistry()
        tools = registry.get_all_tools()
        assert len(tools) >= 10

    def test_read_is_t0(self):
        registry = ToolRegistry()
        assert registry.get_tier("read") == ActionTier.T0_AUTO

    def test_write_is_t1(self):
        registry = ToolRegistry()
        assert registry.get_tier("write") == ActionTier.T1_SOFT

    def test_python_is_t2(self):
        registry = ToolRegistry()
        assert registry.get_tier("python") == ActionTier.T2_GATE

    def test_shell_is_t3(self):
        registry = ToolRegistry()
        assert registry.get_tier("shell") == ActionTier.T3_DUAL

    def test_approve_is_t4(self):
        registry = ToolRegistry()
        assert registry.get_tier("approve") == ActionTier.T4_BOARD

    def test_unknown_tool_defaults_to_t1(self):
        registry = ToolRegistry()
        assert registry.get_tier("unknown_tool") == ActionTier.T1_SOFT

    def test_register_custom_tool(self):
        registry = ToolRegistry()
        registry.register_tool("custom_db", ActionTier.T3_DUAL)
        assert registry.get_tier("custom_db") == ActionTier.T3_DUAL

    def test_override_existing_tool(self):
        registry = ToolRegistry()
        registry.register_tool("read", ActionTier.T4_BOARD)
        assert registry.get_tier("read") == ActionTier.T4_BOARD

    def test_custom_tiers_at_init(self):
        custom = {"my_tool": ActionTier.T2_GATE}
        registry = ToolRegistry(custom_tiers=custom)
        assert registry.get_tier("my_tool") == ActionTier.T2_GATE

    def test_all_tools_returns_copy(self):
        registry = ToolRegistry()
        tools1 = registry.get_all_tools()
        tools2 = registry.get_all_tools()
        assert tools1 == tools2
        assert tools1 is not tools2

    def test_readme_example_tools(self):
        registry = ToolRegistry()
        assert registry.get_tier("read") == ActionTier.T0_AUTO
        assert registry.get_tier("write") == ActionTier.T1_SOFT
        assert registry.get_tier("python") == ActionTier.T2_GATE
        assert registry.get_tier("shell") == ActionTier.T3_DUAL
        assert registry.get_tier("approve") == ActionTier.T4_BOARD
