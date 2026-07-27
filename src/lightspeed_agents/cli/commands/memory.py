import typer

from lightspeed_agents.memory.memory import AgentMemory


app = typer.Typer(help="View and manage agent conversation memory.")


@app.command("show")
def show_memory(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of entries to show"),
):

    memory = AgentMemory(agent_id)
    entries = memory.get_history(limit)

    if not entries:
        typer.echo(f"No memory entries for '{agent_id}'.")
        return

    for entry in entries:
        ts = entry.timestamp[:19].replace("T", " ")
        typer.echo(f"[{ts}] {entry.role}: {entry.content[:100]}")


@app.command("clear")
def clear_memory(
    agent_id: str = typer.Argument(..., help="Agent ID"),
):

    memory = AgentMemory(agent_id)
    memory.clear()
    typer.echo(f"Memory cleared for '{agent_id}'.")
