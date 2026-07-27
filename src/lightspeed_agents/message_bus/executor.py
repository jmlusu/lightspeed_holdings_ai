import time
from typing import Callable, Optional

from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.message_bus.task import Task
from lightspeed_agents.message_bus.task_status import TaskStatus
from lightspeed_agents.message_bus.audit import AuditStore
from lightspeed_agents.message_bus.dead_letter import DeadLetterQueue
from lightspeed_agents.memory.engine import MemoryEngine


class Executor:

    def __init__(
        self,
        bus: MessageBus = None,
        memory: MemoryEngine = None,
        audit: AuditStore = None,
        agent_runner_fn: Callable = None,
        poll_interval: int = 5,
    ):
        self.bus = bus or MessageBus()
        self.memory = memory or MemoryEngine()
        self.audit = audit or AuditStore()
        self.dlq = DeadLetterQueue(self.bus)
        self.agent_runner_fn = agent_runner_fn
        self.poll_interval = poll_interval
        self._running = False

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

            if self.agent_runner_fn:
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
