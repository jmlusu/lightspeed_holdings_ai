import typer

from lightspeed_agents.message_bus.message_bus import MessageBus
from lightspeed_agents.message_bus.task_status import TaskStatus, TaskPriority
from lightspeed_agents.message_bus.audit import AuditStore
from lightspeed_agents.message_bus.dead_letter import DeadLetterQueue

app = typer.Typer(help="Manage inter-agent task messaging.")


@app.command("send")
def send_task(
    instruction: str = typer.Argument(..., help="Task instruction"),
    receiver: str = typer.Option(..., "--to", "-r", help="Receiver agent ID"),
    sender: str = typer.Option("", "--from", "-s", help="Sender agent ID"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority: low, medium, high, critical"),
):
    bus = MessageBus()
    try:
        pri = TaskPriority(priority)
    except ValueError:
        typer.echo(f"Invalid priority: {priority}")
        raise typer.Exit(1)

    task = bus.send_task(
        instruction=instruction,
        receiver_id=receiver,
        sender_id=sender,
        priority=pri,
    )
    typer.echo(f"Task {task.id} sent to {receiver} [{priority}]")


@app.command("list")
def list_tasks(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    receiver: str = typer.Option(None, "--to", "-r", help="Filter by receiver"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
):
    bus = MessageBus()

    if status:
        try:
            st = TaskStatus(status)
            tasks = bus.get_tasks_by_status(st)
        except ValueError:
            typer.echo(f"Invalid status: {status}")
            raise typer.Exit(1)
    elif receiver:
        tasks = bus.get_tasks_by_receiver(receiver)
    else:
        tasks = bus.get_all_tasks()

    tasks = tasks[-limit:]

    if not tasks:
        typer.echo("No tasks found.")
        return

    for task in tasks:
        assignee = task.receiver_id or task.assignee or "unassigned"
        pri = task.priority.value.upper()
        ts = task.created_at[:19].replace("T", " ")
        typer.echo(
            f"[{task.status.value:>18}] {task.id} {pri:>8} -> {assignee:<20} {task.instruction[:60]}"
        )


@app.command("status")
def task_status(
    task_id: str = typer.Argument(..., help="Task ID"),
):
    bus = MessageBus()
    task = bus.get_task(task_id)

    if not task:
        typer.echo(f"Task '{task_id}' not found.")
        raise typer.Exit(1)

    typer.echo(f"\n  Task: {task.id}")
    typer.echo(f"  Status: {task.status.value}")
    typer.echo(f"  Priority: {task.priority.value}")
    typer.echo(f"  Assignee: {task.receiver_id or task.assignee or 'unassigned'}")
    typer.echo(f"  Sender: {task.sender_id or 'system'}")
    typer.echo(f"  Instruction: {task.instruction}")
    if task.result:
        typer.echo(f"  Result: {task.result[:200]}")
    if task.error:
        typer.echo(f"  Error: {task.error}")
    typer.echo(f"  Created: {task.created_at[:19].replace('T', ' ')}")
    if task.parent_task_id:
        typer.echo(f"  Parent: {task.parent_task_id}")


@app.command("claim")
def claim_task(
    task_id: str = typer.Argument(..., help="Task ID to claim"),
):
    bus = MessageBus()
    try:
        task = bus.claim_task(task_id)
        typer.echo(f"Task {task.id} claimed -> IN_PROGRESS")
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command("complete")
def complete_task(
    task_id: str = typer.Argument(..., help="Task ID to complete"),
    result: str = typer.Option("", "--result", "-r", help="Result message"),
):
    bus = MessageBus()
    try:
        task = bus.complete_task(task_id, result=result)
        typer.echo(f"Task {task.id} completed")
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command("fail")
def fail_task(
    task_id: str = typer.Argument(..., help="Task ID to fail"),
    error: str = typer.Option("", "--error", "-e", help="Error message"),
):
    bus = MessageBus()
    try:
        task = bus.fail_task(task_id, error=error)
        typer.echo(f"Task {task.id} marked as FAILED")
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command("approve")
def approve_task(
    task_id: str = typer.Argument(..., help="Task ID to approve"),
):
    bus = MessageBus()
    try:
        task = bus.approve_task(task_id)
        typer.echo(f"Task {task.id} approved -> IN_PROGRESS")
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command("cancel")
def cancel_task(
    task_id: str = typer.Argument(..., help="Task ID to cancel"),
):
    bus = MessageBus()
    try:
        task = bus.cancel_task(task_id)
        typer.echo(f"Task {task.id} cancelled")
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command("delegate")
def delegate_task(
    parent_id: str = typer.Argument(..., help="Parent task ID"),
    instruction: str = typer.Argument(..., help="Delegation instruction"),
    receiver: str = typer.Option(..., "--to", "-r", help="Receiver agent ID"),
):
    bus = MessageBus()
    task = bus.delegate(
        parent_task_id=parent_id,
        instruction=instruction,
        receiver_id=receiver,
    )
    typer.echo(f"Subtask {task.id} delegated to {receiver}")


@app.command("audit")
def audit_log(
    task_id: str = typer.Option(None, "--task", "-t", help="Filter by task ID"),
    agent_id: str = typer.Option(None, "--agent", "-a", help="Filter by agent ID"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max entries"),
):
    audit = AuditStore()
    entries = audit.get_entries(
        task_id=task_id,
        agent_id=agent_id,
        limit=limit,
    )

    if not entries:
        typer.echo("No audit entries found.")
        return

    for entry in entries:
        ts = entry["timestamp"][:19].replace("T", " ")
        typer.echo(
            f"[{ts}] {entry['event']:<16} task={entry['task_id']} agent={entry.get('agent_id', '')}"
        )


@app.command("stale")
def stale_tasks():
    bus = MessageBus()
    dlq = DeadLetterQueue(bus)
    stale = dlq.detect_stale_tasks()

    if not stale:
        typer.echo("No stale tasks.")
        return

    for task in stale:
        typer.echo(f"  STALE: {task.id} claimed at {task.claimed_at[:19].replace('T', ' ')}")
