import time
from typing import Callable, Optional

from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.message_bus.task import Task
from lightspeed_agents.message_bus.audit import AuditStore
from lightspeed_agents.message_bus.dead_letter import DeadLetterQueue
from lightspeed_agents.memory.engine import MemoryEngine
from lightspeed_agents.permissions.checker import PermissionChecker


class Executor:

    def __init__(
        self,
        bus: MessageBus = None,
        memory: MemoryEngine = None,
        audit: AuditStore = None,
        agent_runner_fn: Callable = None,
        agent_loop: object = None,
        poll_interval: int = 5,
        permission_checker: PermissionChecker = None,
        hitl_gate: object = None,
        agent_lookup_fn: Callable = None,
    ):
        self.bus = bus or MessageBus()
        self.memory = memory or MemoryEngine()
        self.audit = audit or AuditStore()
        self.dlq = DeadLetterQueue(self.bus)
        self.agent_runner_fn = agent_runner_fn
        self.agent_loop = agent_loop
        self.poll_interval = poll_interval
        self._running = False
        self.permission_checker = permission_checker or PermissionChecker()
        self.hitl_gate = hitl_gate
        self.agent_lookup_fn = agent_lookup_fn

    def _ensure_hitl_gate(self):
        if self.hitl_gate is None:
            from lightspeed_agents.permissions.hitl_gate import HITLGate

            self.hitl_gate = HITLGate(self.bus, self.memory)
        return self.hitl_gate

    def tick(self) -> list[Task]:
        processed = []

        self.dlq.process()

        pending = self.bus.get_pending_tasks()

        for task in pending:
            result = self._process_task(task)
            if result:
                processed.append(result)

        return processed

    def _process_task(self, task: Task) -> Optional[Task]:
        try:
            task = self.bus.claim_task(task.id)
            self.audit.record(
                task_id=task.id,
                event="task_claimed",
                agent_id=task.receiver_id,
            )

            self.memory.record_task_outcome(
                task_id=task.id,
                agent_id=task.receiver_id,
                content=f"Claimed: {task.instruction[:200]}",
                status="in_progress",
            )

            tool_name = task.metadata.get("tool", task.metadata.get("tool_name", ""))
            agent = None
            if self.agent_lookup_fn and task.receiver_id:
                agent = self.agent_lookup_fn(task.receiver_id)

            if agent and tool_name:
                approved, tier, error = self.permission_checker.validate_action(
                    agent, tool_name
                )
                if not approved:
                    self.bus.fail_task(task.id, error=error)
                    self.audit.log_permission_check(
                        task_id=task.id,
                        agent_id=task.receiver_id,
                        tool=tool_name,
                        approved=False,
                        tier=tier.value if tier else "",
                        reason=error,
                        correlation_id=task.id,
                    )
                    self.memory.record_task_outcome(
                        task_id=task.id,
                        agent_id=task.receiver_id,
                        content=f"Permission denied: {error}",
                        status="failed",
                        tags=["permission_denied", tier.value if tier else ""],
                    )
                    return self.bus.get_task(task.id)

                needs_approval, tier = self.permission_checker.requires_approval(
                    agent, tool_name
                )
                if needs_approval:
                    gate = self._ensure_hitl_gate()
                    approval_request = gate.park_task(
                        task_id=task.id,
                        agent_id=task.receiver_id,
                        tool_name=tool_name,
                        tier=tier,
                        instruction=task.instruction[:200],
                    )
                    self.audit.record(
                        task_id=task.id,
                        event="task_parked_approval",
                        agent_id=task.receiver_id,
                        details={
                            "tool": tool_name,
                            "tier": tier.value,
                            "approval_request_id": approval_request.id,
                        },
                    )
                    return self.bus.get_task(task.id)

            if self.agent_loop:
                result = self._execute_with_loop(task)
            elif self.agent_runner_fn:
                result = self.agent_runner_fn(task)
                self.bus.complete_task(task.id, result=str(result))
                self.audit.record(
                    task_id=task.id,
                    event="task_completed",
                    agent_id=task.receiver_id,
                    details={"result": str(result)[:500]},
                )
                self.memory.record_task_outcome(
                    task_id=task.id,
                    agent_id=task.receiver_id,
                    content=f"Completed: {task.instruction[:200]}\nResult: {str(result)[:500]}",
                    status="completed",
                )
            else:
                self.bus.complete_task(
                    task.id,
                    result="No executor function configured",
                )

            return self.bus.get_task(task.id)

        except Exception as e:
            self.bus.fail_task(task.id, error=str(e))
            self.audit.record(
                task_id=task.id,
                event="task_failed",
                agent_id=task.receiver_id,
                details={"error": str(e)},
            )
            return self.bus.get_task(task.id)

    def _execute_with_loop(self, task: Task) -> str:
        model = task.metadata.get("model", "")
        system_prompt = task.metadata.get("system_prompt", "")

        loop_result = self.agent_loop.run(
            task=task.instruction,
            system_prompt=system_prompt,
            agent_id=task.receiver_id,
            task_id=task.id,
            model=model,
        )

        for iteration in loop_result.iteration_history:
            self.audit.log_iteration(
                task_id=task.id,
                agent_id=task.receiver_id,
                iteration=iteration.iteration,
                thought=iteration.thought,
                action=iteration.action,
                observation=iteration.observation,
                correlation_id=task.id,
            )

        if loop_result.total_cost_usd > 0:
            self.audit.log_cost(
                task_id=task.id,
                agent_id=task.receiver_id,
                model=model or "unknown",
                tokens=0,
                cost_usd=loop_result.total_cost_usd,
                correlation_id=task.id,
            )

        if loop_result.success:
            self.bus.complete_task(task.id, result=loop_result.response)
            self.audit.record(
                task_id=task.id,
                event="task_completed",
                agent_id=task.receiver_id,
                details={
                    "result": loop_result.response[:500],
                    "iterations": loop_result.iterations,
                    "tool_calls": loop_result.tool_calls,
                    "cost_usd": loop_result.total_cost_usd,
                },
            )
            self.memory.record_task_outcome(
                task_id=task.id,
                agent_id=task.receiver_id,
                content=(
                    f"Completed: {task.instruction[:200]}\n"
                    f"Result: {loop_result.response[:500]}\n"
                    f"Iterations: {loop_result.iterations}, "
                    f"Tool calls: {loop_result.tool_calls}"
                ),
                status="completed",
            )
        else:
            self.bus.fail_task(task.id, error=loop_result.error)
            self.audit.record(
                task_id=task.id,
                event="task_failed",
                agent_id=task.receiver_id,
                details={"error": loop_result.error},
            )
            self.memory.record_task_outcome(
                task_id=task.id,
                agent_id=task.receiver_id,
                content=f"Failed: {loop_result.error}",
                status="failed",
            )

        return loop_result.response

    def run_loop(self, max_ticks: int = None):
        self._running = True
        ticks = 0

        while self._running:
            processed = self.tick()

            ticks += 1
            if max_ticks and ticks >= max_ticks:
                break

            if not processed:
                time.sleep(self.poll_interval)

    def stop(self):
        self._running = False
