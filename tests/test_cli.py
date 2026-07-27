from typer.testing import CliRunner

from lightspeed_agents.cli.main import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "LightSpeed Agents" in result.output


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_agents_list():
    result = runner.invoke(app, ["agents", "list"])
    assert result.exit_code == 0
    assert "cto" in result.output
    assert "cfo" in result.output
    assert "Human CEO" in result.output


def test_agents_list_dept_filter():
    result = runner.invoke(app, ["agents", "list", "--dept", "engineering"])
    assert result.exit_code == 0
    assert "cto" in result.output
    assert "cfo" not in result.output


def test_agents_show():
    result = runner.invoke(app, ["agents", "show", "cto"])
    assert result.exit_code == 0
    assert "Chief Technology Officer" in result.output
    assert "engineering" in result.output


def test_agents_show_not_found():
    result = runner.invoke(app, ["agents", "show", "nonexistent"])
    assert result.exit_code == 1


def test_models_list():
    result = runner.invoke(app, ["models", "list"])
    assert result.exit_code == 0
    assert "FAST" in result.output
    assert "STANDARD" in result.output
    assert "PREMIUM" in result.output


def test_models_overrides():
    result = runner.invoke(app, ["models", "overrides"])
    assert result.exit_code == 0
    assert "cto" in result.output
    assert "premium" in result.output


def test_memory_show_empty():
    result = runner.invoke(app, ["memory", "show", "nonexistent-agent"])
    assert result.exit_code == 0
    assert "No episodic entries" in result.output


def test_memory_clear():
    result = runner.invoke(app, ["memory", "clear"])
    assert result.exit_code == 0
    assert "Cleared all types memory" in result.output


def test_prompts_show():
    result = runner.invoke(app, ["prompts", "show", "cto"])
    assert result.exit_code == 0
    assert "System Prompt" in result.output
    assert "Chief Technology Officer" in result.output


def test_tasks_send():
    result = runner.invoke(app, ["tasks", "send", "deploy API", "--to", "cto"])
    assert result.exit_code == 0
    assert "sent to cto" in result.output


def test_tasks_list_empty():
    result = runner.invoke(app, ["tasks", "list"])
    assert result.exit_code == 0


def test_tasks_list_with_tasks():
    runner.invoke(app, ["tasks", "send", "task 1", "--to", "cto"])
    runner.invoke(app, ["tasks", "send", "task 2", "--to", "cfo"])
    result = runner.invoke(app, ["tasks", "list"])
    assert result.exit_code == 0
    assert "cto" in result.output
    assert "cfo" in result.output


def test_workflows_list():
    result = runner.invoke(app, ["workflows", "list"])
    assert result.exit_code == 0
    assert "daily-executive-briefing" in result.output
    assert "software-development" in result.output


def test_workflows_show():
    result = runner.invoke(app, ["workflows", "show", "software-development"])
    assert result.exit_code == 0
    assert "Software Development" in result.output
    assert "create_task" in result.output


def test_workflows_show_not_found():
    result = runner.invoke(app, ["workflows", "show", "nonexistent"])
    assert result.exit_code == 1
