import typer

from lightspeed_agents.core.agent_runner import AgentRunner

app = typer.Typer(invoke_without_command=True)


@app.callback()
def execute(
    ctx: typer.Context,
    agent: str = typer.Option(
        None, "--agent", "-a", help="Agent ID (e.g. cto, cfo, lead-engineer)"
    ),
    task: str = typer.Option(None, "--task", "-t", help="Task to execute"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show model resolution info"
    ),
):

    if agent and task:

        runner = AgentRunner()

        result = runner.run(agent, task)

        if verbose:
            info = result["model_info"]
            typer.echo(f"[{info['tier']}] {info['provider']}/{info['model']}")
            typer.echo("---")

        typer.echo(result["response"])
