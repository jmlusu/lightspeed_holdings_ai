import typer
from pathlib import Path

from lightspeed_agents.builder.builder import CompanyBuilder

app = typer.Typer(help="AI Company Builder commands")


@app.command()
def run(
    config_dir: Path = typer.Option(Path("company"), help="Configuration directory"),
    output_dir: Path = typer.Option(Path(".opencode"), help="Output directory"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes only"),
):
    builder = CompanyBuilder(
        config_dir=str(config_dir),
        output_dir=str(output_dir),
        dry_run=dry_run,
    )

    builder.run()
