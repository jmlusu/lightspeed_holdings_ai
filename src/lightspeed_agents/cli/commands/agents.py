import typer

from lightspeed_agents.agents.loader import load_agents

app = typer.Typer()


@app.command("list")
def list_agents(
    department: str = typer.Option(None, "--dept", "-d", help="Filter by department"),
):

    registry = load_agents()
    agents = registry.list()

    if department:
        agents = [a for a in agents if a.department == department]

    if not agents:
        typer.echo("No agents found.")
        return

    for agent in agents:
        reports = agent.reports_to or "-"
        typer.echo(
            f"  {agent.id:<20} {agent.name:<30} {agent.department:<15} -> {reports}"
        )


@app.command("show")
def show_agent(
    agent_id: str = typer.Argument(..., help="Agent ID"),
):

    registry = load_agents()
    agent = registry.find(agent_id)

    if not agent:
        typer.echo(f"Agent '{agent_id}' not found.")
        raise typer.Exit(1)

    typer.echo(f"  ID:          {agent.id}")
    typer.echo(f"  Name:        {agent.name}")
    typer.echo(f"  Role:        {agent.role}")
    typer.echo(f"  Type:        {agent.type}")
    typer.echo(f"  Department:  {agent.department}")
    typer.echo(f"  Reports to:  {agent.reports_to or '-'}")
    typer.echo(f"  Tools:       {', '.join(agent.tools) if agent.tools else '-'}")
    typer.echo(
        f"  Permissions: {', '.join(agent.permissions) if agent.permissions else '-'}"
    )
    typer.echo(f"  Model:       {agent.model}")
