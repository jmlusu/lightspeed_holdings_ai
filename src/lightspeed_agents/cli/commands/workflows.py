import typer

from lightspeed_agents.workflow.engine import WorkflowEngine
from lightspeed_agents.workflow.loader import load_workflows

app = typer.Typer(help="Manage and execute workflows.")


@app.command("list")
def list_workflows():
    workflows = load_workflows()

    if not workflows:
        typer.echo("No workflows defined.")
        return

    for wf in workflows:
        step_count = len(wf.steps)
        typer.echo(f"  {wf.id:<30} {wf.name:<40} {step_count} steps  owner={wf.owner}")


@app.command("show")
def show_workflow(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
):
    engine = WorkflowEngine()
    wf = engine.get_workflow(workflow_id)

    if not wf:
        typer.echo(f"Workflow '{workflow_id}' not found.")
        raise typer.Exit(1)

    typer.echo(f"\n  Workflow: {wf.name}")
    typer.echo(f"  ID: {wf.id}")
    typer.echo(f"  Description: {wf.description}")
    typer.echo(f"  Owner: {wf.owner}")
    typer.echo(f"\n  Steps:")

    for i, step in enumerate(wf.steps):
        deps = f" (depends: {', '.join(step.depends_on)})" if step.depends_on else ""
        approve = " [APPROVAL REQUIRED]" if step.requires_approval else ""
        typer.echo(
            f"    {i+1}. {step.id:<25} {step.assignee:<20} {step.tier}{approve}{deps}"
        )
        if step.instruction:
            typer.echo(f"       {step.instruction}")


@app.command("start")
def start_workflow(
    workflow_id: str = typer.Argument(..., help="Workflow ID to start"),
):
    engine = WorkflowEngine()
    try:
        run = engine.start_workflow(workflow_id)
        typer.echo(f"Workflow '{workflow_id}' started. Run ID: {run.id}")
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command("runs")
def list_runs(
    workflow_id: str = typer.Option(None, "--workflow", "-w", help="Filter by workflow ID"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
):
    engine = WorkflowEngine()

    if workflow_id:
        runs = engine.get_runs_by_workflow(workflow_id)
    else:
        runs = engine.get_all_runs()

    runs = runs[-limit:]

    if not runs:
        typer.echo("No workflow runs found.")
        return

    for run in runs:
        ts = run.created_at[:19].replace("T", " ")
        typer.echo(
            f"  [{run.status.value:>12}] {run.id}  workflow={run.workflow_id}  started={ts}"
        )


@app.command("status")
def run_status(
    run_id: str = typer.Argument(..., help="Run ID"),
):
    engine = WorkflowEngine()
    run = engine.get_run(run_id)

    if not run:
        typer.echo(f"Run '{run_id}' not found.")
        raise typer.Exit(1)

    wf = engine.get_workflow(run.workflow_id)
    wf_name = wf.name if wf else run.workflow_id

    typer.echo(f"\n  Run: {run.id}")
    typer.echo(f"  Workflow: {wf_name} ({run.workflow_id})")
    typer.echo(f"  Status: {run.status.value}")
    typer.echo(f"  Started: {run.started_at[:19].replace('T', ' ') if run.started_at else 'N/A'}")

    if run.completed_at:
        typer.echo(f"  Completed: {run.completed_at[:19].replace('T', ' ')}")

    typer.echo(f"\n  Step Results:")

    if wf:
        for step in wf.steps:
            result = run.step_results.get(step.id, {})
            status = result.get("status", "pending")
            icon = {
                "completed": "[OK]",
                "failed": "[FAIL]",
                "in_progress": "[...]",
                "waiting_approval": "[APPROVE]",
                "pending": "[--]",
            }.get(status, "[??]")
            typer.echo(f"    {icon} {step.id:<25} {status}")
            if result.get("result"):
                typer.echo(f"       Result: {result['result'][:100]}")
            if result.get("error"):
                typer.echo(f"       Error: {result['error'][:100]}")


@app.command("approve")
def approve_step(
    run_id: str = typer.Argument(..., help="Run ID"),
    step_id: str = typer.Argument(..., help="Step ID to approve"),
):
    engine = WorkflowEngine()
    try:
        run = engine.approve_step(run_id, step_id)
        typer.echo(f"Step '{step_id}' approved in run {run_id}")
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command("complete")
def complete_step(
    run_id: str = typer.Argument(..., help="Run ID"),
    step_id: str = typer.Argument(..., help="Step ID to complete"),
    result: str = typer.Option("", "--result", "-r", help="Result message"),
):
    engine = WorkflowEngine()
    try:
        run = engine.complete_step(run_id, step_id, result=result)
        typer.echo(f"Step '{step_id}' completed in run {run_id}")
        if run.status.value == "completed":
            typer.echo(f"Workflow completed!")
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command("cancel")
def cancel_workflow(
    run_id: str = typer.Argument(..., help="Run ID to cancel"),
):
    engine = WorkflowEngine()
    try:
        run = engine.cancel_workflow(run_id)
        typer.echo(f"Workflow run {run_id} cancelled.")
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)
