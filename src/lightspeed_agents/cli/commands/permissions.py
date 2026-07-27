import json
import typer
from typing import Optional

from lightspeed_agents.permissions.checker import PermissionChecker
from lightspeed_agents.permissions.hitl_gate import HITLGate
from lightspeed_agents.permissions.tiers import (
    ActionTier,
    TIER_RISK_LEVELS,
    TIER_APPROVAL_COUNT,
    TIER_TIMEOUT_MINUTES,
    TIER_DESCRIPTIONS,
)
from lightspeed_agents.permissions.tool_registry import ToolRegistry
from lightspeed_agents.permissions.approval import ApprovalStatus
from lightspeed_agents.agents.loader import load_agents

app = typer.Typer(help="Permissions and approval management")


@app.command("check")
def check_permission(
    agent_id: str = typer.Argument(..., help="Agent ID to check"),
    tool: str = typer.Argument(..., help="Tool/action to check"),
):
    load_agents()
    from lightspeed_agents.registry.registry import registry

    agent = registry.find(agent_id)
    if not agent:
        typer.echo(f"Agent '{agent_id}' not found", err=True)
        raise typer.Exit(1)

    checker = PermissionChecker()
    approved, tier, error = checker.validate_action(agent, tool)

    if approved:
        typer.echo(f"[OK] Agent '{agent_id}' can use '{tool}' (tier: {tier.value})")
    else:
        typer.echo(f"[BLOCKED] Agent '{agent_id}' cannot use '{tool}': {error}", err=True)
        raise typer.Exit(1)


@app.command("tiers")
def list_tiers():
    typer.echo("Action Tiers:")
    typer.echo("=" * 60)

    for tier in ActionTier:
        risk = TIER_RISK_LEVELS[tier]
        approvals = TIER_APPROVAL_COUNT[tier]
        timeout = TIER_TIMEOUT_MINUTES[tier]
        desc = TIER_DESCRIPTIONS[tier]

        typer.echo(f"\n{tier.value} - {desc}")
        typer.echo(f"  Risk Level: {risk}")
        typer.echo(f"  Required Approvals: {approvals}")
        typer.echo(f"  Timeout (minutes): {timeout}")


@app.command("tools")
def list_tools():
    registry = ToolRegistry()

    typer.echo("Tool Registry:")
    typer.echo("=" * 60)

    tiers = {}
    for tool, tier in registry.get_all_tools().items():
        if tier not in tiers:
            tiers[tier] = []
        tiers[tier].append(tool)

    for tier in ActionTier:
        if tier in tiers:
            typer.echo(f"\n{tier.value} - {TIER_DESCRIPTIONS[tier]}")
            for tool in sorted(tiers[tier]):
                typer.echo(f"  - {tool}")


@app.command("pending")
def list_pending():
    gate = HITLGate()
    requests = gate.get_pending()

    if not requests:
        typer.echo("No pending approval requests")
        return

    typer.echo(f"Pending Approvals ({len(requests)}):")
    typer.echo("=" * 60)

    for req in requests:
        typer.echo(f"\nID: {req.id}")
        typer.echo(f"  Task: {req.task_id}")
        typer.echo(f"  Agent: {req.agent_id}")
        typer.echo(f"  Tool: {req.tool_name}")
        typer.echo(f"  Tier: {req.tier.value}")
        typer.echo(f"  Required Approvals: {req.required_approvals}")
        typer.echo(f"  Current Approvals: {req.approval_count}")
        typer.echo(f"  Instruction: {req.instruction[:80]}...")
        typer.echo(f"  Created: {req.created_at}")


@app.command("approve")
def approve_request(
    request_id: str = typer.Argument(..., help="Approval request ID"),
    approver: str = typer.Option(..., "--approver", "-a", help="Approver agent ID"),
    note: str = typer.Option("", "--note", "-n", help="Approval note"),
):
    gate = HITLGate()

    try:
        request = gate.approve(request_id, approver, note)
        typer.echo(f"[OK] Approved request '{request_id}'")

        if request.is_fully_approved:
            typer.echo(f"  Task '{request.task_id}' has been unblocked and will resume")
    except ValueError as e:
        typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)


@app.command("reject")
def reject_request(
    request_id: str = typer.Argument(..., help="Approval request ID"),
    approver: str = typer.Option(..., "--approver", "-a", help="Approver agent ID"),
    note: str = typer.Option("", "--note", "-n", help="Rejection reason"),
):
    gate = HITLGate()

    try:
        request = gate.reject(request_id, approver, note)
        typer.echo(f"[OK] Rejected request '{request_id}'")
        typer.echo(f"  Task '{request.task_id}' has been failed")
    except ValueError as e:
        typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)


@app.command("expired")
def check_expired():
    gate = HITLGate()
    expired = gate.check_expired()

    if not expired:
        typer.echo("No expired requests")
        return

    typer.echo(f"Expired Requests ({len(expired)}):")
    typer.echo("=" * 60)

    for req in expired:
        typer.echo(f"\nID: {req.id}")
        typer.echo(f"  Task: {req.task_id}")
        typer.echo(f"  Agent: {req.agent_id}")
        typer.echo(f"  Tool: {req.tool_name}")
        typer.echo(f"  Expires: {req.expires_at}")


@app.command("history")
def audit_history(
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records"),
):
    from lightspeed_agents.message_bus.audit import AuditStore
    audit = AuditStore()
    records = audit.get_recent(limit)

    if not records:
        typer.echo("No audit records found")
        return

    typer.echo(f"Recent Permission Events ({len(records)}):")
    typer.echo("=" * 60)

    for record in records:
        event = record.get("event", "")
        if "permission" in event or "approval" in event or "parked" in event:
            typer.echo(f"\n  {record.get('timestamp', 'N/A')}")
            typer.echo(f"    Event: {event}")
            typer.echo(f"    Task: {record.get('task_id', 'N/A')}")
            typer.echo(f"    Agent: {record.get('agent_id', 'N/A')}")
            details = record.get("details", {})
            if details:
                typer.echo(f"    Details: {json.dumps(details, indent=2)}")
