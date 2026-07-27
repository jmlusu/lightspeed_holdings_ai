from datetime import datetime, UTC
from typing import Optional

from lightspeed_agents.message_bus.task import Task
from lightspeed_agents.message_bus.task_status import (
    TaskStatus,
    TaskPriority,
    PRIORITY_ORDER,
)
from lightspeed_agents.message_bus.file_store import FileStore

INBOX_FILE = "inbox.json"


class MessageBus:

    def __init__(self, bus_dir: str = ".opencode"):
        self.store = FileStore(bus_dir)
        self._broadcast_callback = None

    def set_broadcast_callback(self, callback):
        self._broadcast_callback = callback

    def _broadcast(self, task: Task, event: str):
        if self._broadcast_callback:
            self._broadcast_callback(task, event)

    def send_task(
        self,
        instruction: str,
        assignee: str = "",
        sender_id: str = "",
        receiver_id: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        parent_task_id: str = "",
        tags: list[str] = None,
        metadata: dict = None,
    ) -> Task:
        task = Task(
            instruction=instruction,
            assignee=assignee or receiver_id,
            sender_id=sender_id,
            receiver_id=receiver_id or assignee,
            priority=priority,
            parent_task_id=parent_task_id,
            tags=tags or [],
            metadata=metadata or {},
        )

        self.store.append(INBOX_FILE, task.model_dump(mode="json"))
        self._broadcast(task, "task_created")
        return task

    def get_all_tasks(self) -> list[Task]:
        raw = self.store.load(INBOX_FILE)
        return [Task(**r) for r in raw]

    def get_task(self, task_id: str) -> Optional[Task]:
        for task in self.get_all_tasks():
            if task.id == task_id:
                return task
        return None

    def get_pending_tasks(self) -> list[Task]:
        tasks = [t for t in self.get_all_tasks() if t.status == TaskStatus.PENDING]
        tasks.sort(key=lambda t: PRIORITY_ORDER.get(t.priority, 99))
        return tasks

    def get_tasks_by_receiver(self, receiver_id: str) -> list[Task]:
        return [
            t
            for t in self.get_all_tasks()
            if t.receiver_id == receiver_id or t.assignee == receiver_id
        ]

    def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        return [t for t in self.get_all_tasks() if t.status == status]

    def get_subtasks(self, parent_task_id: str) -> list[Task]:
        return [t for t in self.get_all_tasks() if t.parent_task_id == parent_task_id]

    def claim_task(self, task_id: str) -> Task:
        task = self._update_status(
            task_id,
            TaskStatus.IN_PROGRESS,
            extra={"claimed_at": datetime.now(UTC).isoformat()},
        )
        self._broadcast(task, "task_claimed")
        return task

    def complete_task(self, task_id: str, result: str = "") -> Task:
        task = self._update_status(
            task_id,
            TaskStatus.COMPLETED,
            extra={
                "result": result,
                "completed_at": datetime.now(UTC).isoformat(),
            },
        )
        self._broadcast(task, "task_completed")
        return task

    def fail_task(self, task_id: str, error: str = "") -> Task:
        task = self._update_status(
            task_id,
            TaskStatus.FAILED,
            extra={
                "error": error,
                "completed_at": datetime.now(UTC).isoformat(),
            },
        )
        self._broadcast(task, "task_failed")
        return task

    def escalate_task(self, task_id: str) -> Task:
        task = self._update_status(task_id, TaskStatus.ESCALATED)
        self._broadcast(task, "task_escalated")
        return task

    def cancel_task(self, task_id: str) -> Task:
        task = self._update_status(task_id, TaskStatus.CANCELLED)
        self._broadcast(task, "task_cancelled")
        return task

    def approve_task(self, task_id: str) -> Task:
        task = self._update_status(task_id, TaskStatus.IN_PROGRESS)
        self._broadcast(task, "task_approved")
        return task

    def park_for_approval(self, task_id: str) -> Task:
        task = self._update_status(task_id, TaskStatus.WAITING_APPROVAL)
        self._broadcast(task, "task_parked")
        return task

    def delegate(
        self,
        parent_task_id: str,
        instruction: str,
        receiver_id: str,
        sender_id: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Task:
        return self.send_task(
            instruction=instruction,
            receiver_id=receiver_id,
            sender_id=sender_id or parent_task_id,
            priority=priority,
            parent_task_id=parent_task_id,
        )

    def _update_status(
        self,
        task_id: str,
        status: TaskStatus,
        extra: dict = None,
    ) -> Task:
        updates = {
            "status": status.value,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        if extra:
            updates.update(extra)

        self.store.update_entry(INBOX_FILE, task_id, updates)

        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")
        return task
