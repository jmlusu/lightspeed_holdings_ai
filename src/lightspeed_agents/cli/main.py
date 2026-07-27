import typer

from lightspeed_agents.version import __version__
from lightspeed_agents.cli.commands.agents import app as agents_app
from lightspeed_agents.cli.commands.company import app as company_app
from lightspeed_agents.cli.commands.run import app as run_app
from lightspeed_agents.cli.commands.models import app as models_app
from lightspeed_agents.cli.commands.prompts import app as prompts_app
from lightspeed_agents.cli.commands.memory import app as memory_app
from lightspeed_agents.cli.commands.tasks import app as tasks_app
from lightspeed_agents.cli.commands.workflows import app as workflows_app

app = typer.Typer(
    name="lightspeed",
    help="LightSpeed Agents — AI agent orchestration framework.",
    no_args_is_help=True,
)

app.add_typer(agents_app, name="agents", help="Manage and list agents.")
app.add_typer(company_app, name="company", help="Build and manage the AI company.")
app.add_typer(run_app, name="run", help="Run a task with an agent.")
app.add_typer(models_app, name="models", help="View model tiers and agent overrides.")
app.add_typer(prompts_app, name="prompts", help="Preview agent system prompts.")
app.add_typer(memory_app, name="memory", help="View and manage agent memory.")
app.add_typer(tasks_app, name="tasks", help="Manage inter-agent task messaging.")
app.add_typer(workflows_app, name="workflows", help="Manage and execute workflows.")


@app.command()
def version():
    typer.echo(f"lightspeed-agents v{__version__}")
