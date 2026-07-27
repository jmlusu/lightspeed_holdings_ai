import typer

from lightspeed_agents.registry.registry import registry
from lightspeed_agents.agents.loader import load_agents
from lightspeed_agents.prompts.builder import PromptBuilder

app = typer.Typer(help="Preview agent system prompts.")


@app.command("show")
def show_prompt(
    agent_id: str = typer.Argument(..., help="Agent ID"),
):

    load_agents()
    agent = registry.find(agent_id)

    if not agent:
        typer.echo(f"Agent '{agent_id}' not found.")
        raise typer.Exit(1)

    builder = PromptBuilder()
    prompt = builder.build(agent)

    typer.echo(prompt)
