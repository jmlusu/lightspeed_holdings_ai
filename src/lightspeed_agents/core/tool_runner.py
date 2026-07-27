import os
import subprocess
import json
from dataclasses import dataclass, field


DANGEROUS_TOOLS = {"execute", "shell", "deploy", "docker"}


@dataclass
class ToolResult:
    tool: str
    success: bool
    output: str
    error: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolPlan:
    tool: str
    args: dict = field(default_factory=dict)
    description: str = ""


class ToolRunner:

    def __init__(
        self,
        workspace_dir: str = ".",
        allowed_tools: list[str] = None,
        blocked_paths: list[str] = None,
    ):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.allowed_tools = allowed_tools
        self.blocked_paths = blocked_paths or [
            os.path.join(self.workspace_dir, ".git"),
            os.path.join(self.workspace_dir, ".env"),
        ]

    def run_plan(self, plan: ToolPlan) -> ToolResult:
        if self.allowed_tools and plan.tool not in self.allowed_tools:
            return ToolResult(
                tool=plan.tool,
                success=False,
                output="",
                error=f"Tool '{plan.tool}' not in allowed tools list",
            )

        if plan.tool in DANGEROUS_TOOLS:
            return self._execute_dangerous(plan)

        if plan.tool == "read":
            return self._read_file(plan)
        elif plan.tool == "write":
            return self._write_file(plan)
        elif plan.tool == "edit":
            return self._edit_file(plan)
        elif plan.tool == "search":
            return self._search(plan)
        elif plan.tool == "list":
            return self._list_directory(plan)
        elif plan.tool == "python":
            return self._run_python(plan)
        elif plan.tool == "git":
            return self._run_git(plan)
        else:
            return ToolResult(
                tool=plan.tool,
                success=False,
                output="",
                error=f"Unknown tool: {plan.tool}",
            )

    def run_steps(self, steps: list[ToolPlan]) -> list[ToolResult]:
        results = []
        for step in steps:
            result = self.run_plan(step)
            results.append(result)
            if not result.success:
                break
        return results

    def _read_file(self, plan: ToolPlan) -> ToolResult:
        path = plan.args.get("path", "")
        if not path:
            return ToolResult(tool="read", success=False, output="", error="No path specified")

        full_path = self._resolve_path(path)
        if not self._is_safe_path(full_path):
            return ToolResult(tool="read", success=False, output="", error="Path not allowed")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return ToolResult(tool="read", success=True, output=content)
        except Exception as e:
            return ToolResult(tool="read", success=False, output="", error=str(e))

    def _write_file(self, plan: ToolPlan) -> ToolResult:
        path = plan.args.get("path", "")
        content = plan.args.get("content", "")
        if not path:
            return ToolResult(tool="write", success=False, output="", error="No path specified")

        full_path = self._resolve_path(path)
        if not self._is_safe_path(full_path):
            return ToolResult(tool="write", success=False, output="", error="Path not allowed")

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(
                tool="write",
                success=True,
                output=f"Written {len(content)} bytes to {path}",
            )
        except Exception as e:
            return ToolResult(tool="write", success=False, output="", error=str(e))

    def _edit_file(self, plan: ToolPlan) -> ToolResult:
        path = plan.args.get("path", "")
        old = plan.args.get("old", "")
        new = plan.args.get("new", "")
        if not path:
            return ToolResult(tool="edit", success=False, output="", error="No path specified")

        full_path = self._resolve_path(path)
        if not self._is_safe_path(full_path):
            return ToolResult(tool="edit", success=False, output="", error="Path not allowed")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            if old not in content:
                return ToolResult(tool="edit", success=False, output="", error="old text not found")
            content = content.replace(old, new, 1)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(tool="edit", success=True, output=f"Edited {path}")
        except Exception as e:
            return ToolResult(tool="edit", success=False, output="", error=str(e))

    def _search(self, plan: ToolPlan) -> ToolResult:
        query = plan.args.get("query", "")
        path = plan.args.get("path", ".")
        if not query:
            return ToolResult(tool="search", success=False, output="", error="No query specified")

        full_path = self._resolve_path(path)
        try:
            result = subprocess.run(
                ["rg", "--no-heading", "-n", query, full_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return ToolResult(
                tool="search",
                success=result.returncode == 0,
                output=result.stdout[:10000],
                error=result.stderr[:1000] if result.returncode != 0 else "",
            )
        except FileNotFoundError:
            return self._search_fallback(query, full_path)
        except subprocess.TimeoutExpired:
            return ToolResult(tool="search", success=False, output="", error="Search timed out")

    def _search_fallback(self, query: str, path: str) -> ToolResult:
        results = []
        for root, _dirs, files in os.walk(path):
            if ".git" in root:
                continue
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if query.lower() in line.lower():
                                results.append(f"{fpath}:{i}:{line.rstrip()}")
                                if len(results) >= 50:
                                    break
                    if len(results) >= 50:
                        break
                except Exception:
                    continue
            if len(results) >= 50:
                break
        return ToolResult(
            tool="search",
            success=True,
            output="\n".join(results) if results else "No matches found",
        )

    def _list_directory(self, plan: ToolPlan) -> ToolResult:
        path = plan.args.get("path", ".")
        full_path = self._resolve_path(path)
        if not self._is_safe_path(full_path):
            return ToolResult(tool="list", success=False, output="", error="Path not allowed")

        try:
            entries = os.listdir(full_path)
            lines = []
            for entry in sorted(entries):
                full = os.path.join(full_path, entry)
                prefix = "d" if os.path.isdir(full) else "f"
                lines.append(f"{prefix} {entry}")
            return ToolResult(tool="list", success=True, output="\n".join(lines))
        except Exception as e:
            return ToolResult(tool="list", success=False, output="", error=str(e))

    def _run_python(self, plan: ToolPlan) -> ToolResult:
        code = plan.args.get("code", "")
        if not code:
            return ToolResult(tool="python", success=False, output="", error="No code specified")

        try:
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.workspace_dir,
            )
            return ToolResult(
                tool="python",
                success=result.returncode == 0,
                output=result.stdout[:10000],
                error=result.stderr[:1000] if result.returncode != 0 else "",
            )
        except subprocess.TimeoutExpired:
            return ToolResult(tool="python", success=False, output="", error="Execution timed out")

    def _run_git(self, plan: ToolPlan) -> ToolResult:
        args = plan.args.get("args", "")
        if not args:
            return ToolResult(tool="git", success=False, output="", error="No args specified")

        try:
            result = subprocess.run(
                f"git {args}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.workspace_dir,
            )
            return ToolResult(
                tool="git",
                success=result.returncode == 0,
                output=result.stdout[:10000],
                error=result.stderr[:1000] if result.returncode != 0 else "",
            )
        except subprocess.TimeoutExpired:
            return ToolResult(tool="git", success=False, output="", error="Git command timed out")

    def _execute_dangerous(self, plan: ToolPlan) -> ToolResult:
        return ToolResult(
            tool=plan.tool,
            success=False,
            output="",
            error=f"Dangerous tool '{plan.tool}' requires HITL approval",
            metadata={"requires_approval": True},
        )

    def _resolve_path(self, path: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(self.workspace_dir, path))

    def _is_safe_path(self, full_path: str) -> bool:
        real_path = os.path.realpath(full_path)
        for blocked in self.blocked_paths:
            if real_path.startswith(os.path.realpath(blocked)):
                return False
        return True
