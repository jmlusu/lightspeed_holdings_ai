from datetime import datetime, timezone, timedelta

from lightspeed_agents.message_bus.message_bus import MessageBus, INBOX_FILE
from lightspeed_agents.message_bus.task import Task
from lightspeed_agents.message_bus.task_status import TaskStatus


class DeadLetterQueue:

    def __init__(self, bus: MessageBus, stale_minutes: int = 30):
        self.bus = bus
        self.stale_timeout = timedelta(minutes=stale_minutes)

    def detect_stale_tasks(self) -> list[Task]:
        stale = []
        now = datetime.now(timezone.utc)

        for task in self.bus.get_tasks_by_status(TaskStatus.IN_PROGRESS):
            if not task.claimed_at:
                continue
            claimed = datetime.fromisoformat(task.claimed_at)
            if now - claimed > self.stale_timeout:
                stale.append(task)

        return stale

    def move_to_dlq(self, task: Task):
        self.bus.fail_task(
            task.id,
            error="Stale task: exceeded time limit in IN_PROGRESS",
        )

    def process(self) -> list[Task]:
        stale = self.detect_stale_tasks()
        for task in stale:
            self.move_to_dlq(task)
        return stale

    def get_dlq_tasks(self) -> list[Task]:
        return self.bus.get_tasks_by_status(TaskStatus.FAILED)
