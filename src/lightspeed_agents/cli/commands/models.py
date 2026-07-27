import typer

from lightspeed_agents.models.resolver import ModelResolver, _AVAILABLE_PROVIDERS

app = typer.Typer(help="View model tiers and agent overrides.")


@app.command("list")
def list_tiers():

    resolver = ModelResolver()

    if not resolver.tiers:
        typer.echo("No model tiers configured.")
        return

    for name, tier in resolver.tiers.items():
        desc = tier.get("description", "")
        providers = tier.get("providers", [])

        typer.echo(f"\n  {name.upper()}: {desc}")

        for p in providers:
            avail = "+" if p["provider"] in _AVAILABLE_PROVIDERS else " "
            typer.echo(f"    [{avail}] {p['provider']}/{p['model']}")


@app.command("overrides")
def list_overrides():

    resolver = ModelResolver()

    if not resolver.overrides:
        typer.echo("No agent overrides configured.")
        return

    for agent_id, tier in resolver.overrides.items():
        typer.echo(f"  {agent_id:<22} -> {tier}")
