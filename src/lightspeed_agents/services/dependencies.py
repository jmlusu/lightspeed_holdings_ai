from collections.abc import Callable

from fastapi import Depends

from lightspeed_agents.core.cost_tracker import CostTracker
from lightspeed_agents.memory.engine import MemoryEngine
from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.registry.registry import AgentRegistry
from lightspeed_agents.services.config import settings
from lightspeed_agents.workflow.engine import WorkflowEngine

_bus_instance: MessageBus | None = None
_cost_tracker_instance: CostTracker | None = None
_workflow_engine_instance: WorkflowEngine | None = None
_memory_engine_instance: MemoryEngine | None = None
_agent_registry_instance: AgentRegistry | None = None


def get_message_bus() -> MessageBus:
    """Provide a singleton MessageBus instance."""
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = MessageBus()
    return _bus_instance


def get_cost_tracker() -> CostTracker:
    """Provide a singleton CostTracker instance."""
    global _cost_tracker_instance
    if _cost_tracker_instance is None:
        _cost_tracker_instance = CostTracker()
    return _cost_tracker_instance


def get_memory_engine() -> MemoryEngine:
    """Provide a singleton MemoryEngine instance."""
    global _memory_engine_instance
    if _memory_engine_instance is None:
        _memory_engine_instance = MemoryEngine()
    return _memory_engine_instance


def get_workflow_engine(
    bus: MessageBus = Depends(get_message_bus),  # noqa: B008
    memory: MemoryEngine = Depends(get_memory_engine),  # noqa: B008
) -> WorkflowEngine:
    """Provide a singleton WorkflowEngine with injected dependencies."""
    global _workflow_engine_instance
    if _workflow_engine_instance is None:
        _workflow_engine_instance = WorkflowEngine(bus=bus, memory=memory)
    return _workflow_engine_instance


def get_agent_registry() -> AgentRegistry:
    """Provide a singleton AgentRegistry instance."""
    global _agent_registry_instance
    if _agent_registry_instance is None:
        _agent_registry_instance = AgentRegistry()
    return _agent_registry_instance


def get_auth_dependency() -> Callable:
    """Return the appropriate authentication dependency based on current settings.

    When ``AUTH_REQUIRED`` is ``False``, returns a dependency that always
    succeeds with ``"anonymous"``.  Otherwise returns ``verify_api_key``.
    """
    from lightspeed_agents.services.auth import verify_api_key

    if not settings.AUTH_REQUIRED:

        async def _no_auth() -> str:  # type: ignore[misc]
            return "anonymous"

        return _no_auth

    return verify_api_key


def reset_dependencies() -> None:
    """Reset all singleton instances (for testing)."""
    global _bus_instance, _cost_tracker_instance, _workflow_engine_instance, _memory_engine_instance, _agent_registry_instance
    _bus_instance = None
    _cost_tracker_instance = None
    _workflow_engine_instance = None
    _memory_engine_instance = None
    _agent_registry_instance = None
