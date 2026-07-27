import os
import pytest

from lightspeed_agents.core.tool_runner import ToolRunner, ToolPlan, ToolResult, DANGEROUS_TOOLS


@pytest.fixture
def runner(tmp_path):
    return ToolRunner(workspace_dir=str(tmp_path))


@pytest.fixture
def runner_with_workspace(tmp_path):
    (tmp_path / "hello.txt").write_text("Hello, World!")
    (tmp_path / "code.py").write_text("print('hello')")
    os.makedirs(tmp_path / "subdir")
    (tmp_path / "subdir" / "nested.txt").write_text("nested content")
    return ToolRunner(workspace_dir=str(tmp_path))


class TestToolPlan:
    def test_tool_plan_creation(self):
        plan = ToolPlan(tool="read", args={"path": "file.txt"})
        assert plan.tool == "read"
        assert plan.args["path"] == "file.txt"

    def test_tool_plan_default_args(self):
        plan = ToolPlan(tool="list")
        assert plan.args == {}


class TestReadFile:
    def test_read_existing_file(self, runner_with_workspace):
        result = runner_with_workspace.run_plan(
            ToolPlan(tool="read", args={"path": "hello.txt"})
        )
        assert result.success is True
        assert "Hello, World!" in result.output

    def test_read_nonexistent_file(self, runner):
        result = runner.run_plan(
            ToolPlan(tool="read", args={"path": "nope.txt"})
        )
        assert result.success is False
        assert "No such file" in result.error or "not found" in result.error.lower()

    def test_read_no_path(self, runner):
        result = runner.run_plan(ToolPlan(tool="read"))
        assert result.success is False
        assert "No path" in result.error


class TestWriteFile:
    def test_write_new_file(self, runner):
        result = runner.run_plan(
            ToolPlan(tool="write", args={"path": "new.txt", "content": "test data"})
        )
        assert result.success is True
        assert os.path.exists(os.path.join(runner.workspace_dir, "new.txt"))

    def test_write_creates_directories(self, runner):
        result = runner.run_plan(
            ToolPlan(
                tool="write",
                args={"path": "a/b/c/file.txt", "content": "nested"},
            )
        )
        assert result.success is True

    def test_write_blocked_path(self, runner):
        result = runner.run_plan(
            ToolPlan(tool="write", args={"path": ".env", "content": "SECRET=x"})
        )
        assert result.success is False
        assert "not allowed" in result.error.lower()


class TestSearch:
    def test_search_finds_match(self, runner_with_workspace):
        result = runner_with_workspace.run_plan(
            ToolPlan(tool="search", args={"query": "Hello"})
        )
        assert result.success is True
        assert "Hello" in result.output

    def test_search_no_match(self, runner_with_workspace):
        result = runner_with_workspace.run_plan(
            ToolPlan(tool="search", args={"query": "ZZZZNOTFOUND"})
        )
        assert result.success is True
        assert "No matches" in result.output

    def test_search_no_query(self, runner):
        result = runner.run_plan(ToolPlan(tool="search"))
        assert result.success is False


class TestListDirectory:
    def test_list_directory(self, runner_with_workspace):
        result = runner_with_workspace.run_plan(
            ToolPlan(tool="list", args={"path": "."})
        )
        assert result.success is True
        assert "hello.txt" in result.output

    def test_list_subdirectory(self, runner_with_workspace):
        result = runner_with_workspace.run_plan(
            ToolPlan(tool="list", args={"path": "subdir"})
        )
        assert result.success is True
        assert "nested.txt" in result.output


class TestPython:
    def test_run_python(self, runner):
        result = runner.run_plan(
            ToolPlan(tool="python", args={"code": "print(2 + 2)"})
        )
        assert result.success is True
        assert "4" in result.output

    def test_run_python_error(self, runner):
        result = runner.run_plan(
            ToolPlan(tool="python", args={"code": "raise ValueError('test')"})
        )
        assert result.success is False

    def test_run_python_timeout(self, runner):
        result = runner.run_plan(
            ToolPlan(tool="python", args={"code": "import time; time.sleep(120)"})
        )
        assert result.success is False
        assert "timed out" in result.error.lower()


class TestGit:
    def test_run_git_status(self, runner):
        result = runner.run_plan(
            ToolPlan(tool="git", args={"args": "status"})
        )
        assert result.success is True or "not a git" in result.error.lower()


class TestDangerousTools:
    def test_dangerous_tools_blocked(self, runner):
        for tool in DANGEROUS_TOOLS:
            result = runner.run_plan(ToolPlan(tool=tool, args={}))
            assert result.success is False
            assert result.metadata.get("requires_approval") is True


class TestRunSteps:
    def test_run_steps_stops_on_failure(self, runner_with_workspace):
        steps = [
            ToolPlan(tool="read", args={"path": "hello.txt"}),
            ToolPlan(tool="read", args={"path": "nonexistent.txt"}),
            ToolPlan(tool="read", args={"path": "hello.txt"}),
        ]
        results = runner_with_workspace.run_steps(steps)
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False

    def test_run_steps_all_success(self, runner_with_workspace):
        steps = [
            ToolPlan(tool="read", args={"path": "hello.txt"}),
            ToolPlan(tool="list", args={"path": "."}),
        ]
        results = runner_with_workspace.run_steps(steps)
        assert len(results) == 2
        assert all(r.success for r in results)


class TestSafety:
    def test_blocked_git_directory(self, runner):
        result = runner.run_plan(
            ToolPlan(tool="read", args={"path": ".git/config"})
        )
        assert result.success is False
        assert "not allowed" in result.error.lower()

    def test_allowed_tools_filter(self, tmp_path):
        runner = ToolRunner(workspace_dir=str(tmp_path), allowed_tools=["read"])
        result = runner.run_plan(ToolPlan(tool="write", args={"path": "x", "content": "y"}))
        assert result.success is False
        assert "not in allowed" in result.error.lower()
