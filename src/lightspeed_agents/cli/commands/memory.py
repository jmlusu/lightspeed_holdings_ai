import typer

from lightspeed_agents.memory.engine import MemoryEngine


app = typer.Typer(help="View and manage agent memory.")


@app.command("show")
def show_memory(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    memory_type: str = typer.Option("episodic", "--type", "-t", help="Memory type"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of entries"),
):

    engine = MemoryEngine()
    entries = engine.get_entries(memory_type)

    if agent_id != "all":
        entries = [e for e in entries if e.agent_id == agent_id]

    entries = entries[-limit:]

    if not entries:
        typer.echo(f"No {memory_type} entries for '{agent_id}'.")
        return

    for entry in entries:
        ts = entry.created_at[:19].replace("T", " ")
        tags = ",".join(entry.tags) if entry.tags else ""
        typer.echo(
            f"[{ts}] {entry.id} ({tags}) {entry.content[:100]}"
        )


@app.command("search")
def search_memory(
    query: str = typer.Argument(..., help="Search query"),
    memory_type: str = typer.Option(None, "--type", "-t", help="Filter by type"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
):

    engine = MemoryEngine()
    types = [memory_type] if memory_type else None
    results = engine.search(query, memory_types=types, limit=limit)

    if not results:
        typer.echo("No results found.")
        return

    for entry in results:
        ts = entry.created_at[:19].replace("T", " ")
        typer.echo(
            f"[{ts}] {entry.memory_type}/{entry.id} "
            f"(accessed {entry.access_count}x) {entry.content[:100]}"
        )


@app.command("stats")
def memory_stats():

    engine = MemoryEngine()
    stats = engine.get_stats()

    typer.echo("\n  Memory Statistics\n")
    for key, value in stats.items():
        label = key.upper() if key != "total" else "TOTAL"
        typer.echo(f"  {label:<15} {value}")


@app.command("consolidate")
def consolidate_memory():

    engine = MemoryEngine()
    before = engine.get_stats()
    engine.consolidate()
    after = engine.get_stats()

    typer.echo("Consolidation complete.")
    typer.echo(f"  Total entries: {before['total']} -> {after['total']}")


@app.command("prune")
def prune_memory(
    memory_type: str = typer.Option(None, "--type", "-t", help="Type to prune"),
):

    engine = MemoryEngine()
    before = engine.get_stats()
    engine.prune(memory_type)
    after = engine.get_stats()

    typer.echo("Pruning complete.")
    typer.echo(f"  Total entries: {before['total']} -> {after['total']}")


@app.command("clear")
def clear_memory(
    agent_id: str = typer.Option(None, "--agent", "-a", help="Agent ID"),
    memory_type: str = typer.Option(None, "--type", "-t", help="Memory type"),
):

    engine = MemoryEngine()
    engine.clear(memory_type)
    label = memory_type or "all types"
    typer.echo(f"Cleared {label} memory.")


@app.command("record")
def record_entry(
    content: str = typer.Argument(..., help="Content to record"),
    memory_type: str = typer.Option("semantic", "--type", "-t", help="Memory type"),
    agent_id: str = typer.Option("", "--agent", "-a", help="Agent ID"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
):

    engine = MemoryEngine()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    writers = {
        "episodic": lambda: engine.record_task_outcome(
            task_id="manual", agent_id=agent_id, content=content, tags=tag_list,
        ),
        "semantic": lambda: engine.record_knowledge(
            content=content, agent_id=agent_id, tags=tag_list,
        ),
        "procedural": lambda: engine.record_procedure(
            content=content, agent_id=agent_id, tags=tag_list,
        ),
        "relational": lambda: engine.record_relationship(
            content=content, agent_id=agent_id, tags=tag_list,
        ),
        "temporal": lambda: engine.record_temporal(
            content=content, agent_id=agent_id, tags=tag_list,
        ),
    }

    writer = writers.get(memory_type)
    if not writer:
        typer.echo(f"Cannot manually write to '{memory_type}' type.")
        raise typer.Exit(1)

    entry = writer()
    typer.echo(f"Recorded {entry.id} to {memory_type}.")
