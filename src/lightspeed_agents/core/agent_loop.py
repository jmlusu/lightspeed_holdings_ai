import json
import re
from dataclasses import dataclass, field
from typing import Optional

from lightspeed_agents.providers.base import LLMProvider
from lightspeed_agents.core.tool_runner import ToolRunner, ToolPlan, ToolResult
from lightspeed_agents.core.cost_tracker import CostTracker, BudgetConfig


@dataclass
class LoopConfig:
    max_iterations: int = 10
    max_tokens_per_call: int = 2048
    temperature: float = 0.7
    budget: BudgetConfig = None


@dataclass
class IterationResult:
    iteration: int
    thought: str
    action: str
    action_input: dict
    observation: str
    done: bool


@dataclass
class LoopResult:
    response: str
    iterations: int
    total_cost_usd: float
    iteration_history: list[IterationResult] = field(default_factory=list)
    success: bool = True
    error: str = ""

    @property
    def tool_calls(self) -> int:
        return sum(1 for i in self.iteration_history if i.action != "finish")


class AgentLoop:

    def __init__(
        self,
        provider: LLMProvider,
        tool_runner: ToolRunner,
        cost_tracker: CostTracker = None,
        config: LoopConfig = None,
    ):
        self.provider = provider
        self.tool_runner = tool_runner
        self.cost_tracker = cost_tracker or CostTracker()
        self.config = config or LoopConfig()

    def run(
        self,
        task: str,
        system_prompt: str = "",
        agent_id: str = "",
        task_id: str = "",
        model: str = "",
    ) -> LoopResult:
        self.cost_tracker.reset_task_cost()

        messages = self._build_initial_messages(task, system_prompt)
        iteration_history = []
        final_response = ""
        total_iterations = 0

        for iteration in range(1, self.config.max_iterations + 1):
            allowed, reason = self.cost_tracker.check_budget(task_id)
            if not allowed:
                return LoopResult(
                    response=f"Budget exceeded: {reason}",
                    iterations=iteration - 1,
                    total_cost_usd=self.cost_tracker._task_cost,
                    iteration_history=iteration_history,
                    success=False,
                    error=reason,
                )

            llm_response = self._call_llm(messages, model, task_id, agent_id)
            if not llm_response.success:
                return LoopResult(
                    response=f"LLM error: {llm_response.error}",
                    iterations=iteration - 1,
                    total_cost_usd=self.cost_tracker._task_cost,
                    iteration_history=iteration_history,
                    success=False,
                    error=llm_response.error,
                )

            parsed = self._parse_response(llm_response.text)
            total_iterations = iteration

            iteration_result = IterationResult(
                iteration=iteration,
                thought=parsed.get("thought", ""),
                action=parsed.get("action", "finish"),
                action_input=parsed.get("action_input", {}),
                observation="",
                done=parsed.get("action", "finish") == "finish",
            )

            if iteration_result.done:
                final_response = parsed.get("final_answer", llm_response.text)
                iteration_result.observation = "Task completed"
                iteration_history.append(iteration_result)
                break

            tool_result = self._execute_tool(parsed)
            iteration_result.observation = self._format_tool_result(tool_result)
            iteration_history.append(iteration_result)

            messages.append({
                "role": "assistant",
                "content": llm_response.text,
            })
            messages.append({
                "role": "user",
                "content": f"Observation: {iteration_result.observation}",
            })

        if not final_response and iteration_history:
            last = iteration_history[-1]
            if last.observation:
                final_response = f"Completed after {total_iterations} iterations. Last observation: {last.observation[:500]}"
            else:
                final_response = f"Completed after {total_iterations} iterations."

        return LoopResult(
            response=final_response or "No response generated",
            iterations=total_iterations,
            total_cost_usd=self.cost_tracker._task_cost,
            iteration_history=iteration_history,
            success=True,
        )

    def _build_initial_messages(self, task: str, system_prompt: str) -> list[dict]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        tools_desc = self._format_tool_descriptions()
        user_content = (
            f"{task}\n\n"
            f"You have access to these tools: {tools_desc}\n\n"
            f"To use a tool, respond with this exact JSON format:\n"
            f'{{"thought": "your reasoning", "action": "tool_name", '
            f'"action_input": {{"arg": "value"}}}}\n\n'
            f'When you have the final answer, respond with:\n'
            f'{{"thought": "your reasoning", "action": "finish", '
            f'"final_answer": "your answer"}}'
        )
        messages.append({"role": "user", "content": user_content})
        return messages

    def _format_tool_descriptions(self) -> str:
        tools = [
            "read (path: str) — read file contents",
            "write (path: str, content: str) — write to file",
            "edit (path: str, old: str, new: str) — edit file",
            "search (query: str, path: str) — search for pattern",
            "list (path: str) — list directory contents",
            "python (code: str) — execute Python code",
            "git (args: str) — run git command",
        ]
        return "; ".join(tools)

    def _call_llm(self, messages: list[dict], model: str, task_id: str, agent_id: str):
        prompt = self._messages_to_prompt(messages)
        system = ""
        user = prompt
        if messages and messages[0]["role"] == "system":
            system = messages[0]["content"]
            user = "\n".join(m["content"] for m in messages[1:])

        try:
            response = self.provider.complete(
                prompt=user,
                system=system,
                model=model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens_per_call,
            )
            self.cost_tracker.record_usage(
                model=model or "unknown",
                provider=self.provider.__class__.__name__,
                prompt_tokens=len(prompt.split()) * 4 // 3,
                completion_tokens=len(response.split()) * 4 // 3,
                agent_id=agent_id,
                task_id=task_id,
            )
            return _LLMResponse(text=response, success=True)
        except Exception as e:
            return _LLMResponse(text="", success=False, error=str(e))

    def _messages_to_prompt(self, messages: list[dict]) -> str:
        parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                parts.append(f"[System]\n{content}")
            elif role == "assistant":
                parts.append(f"[Assistant]\n{content}")
            elif role == "user":
                parts.append(content)
        return "\n\n".join(parts)

    def _parse_response(self, text: str) -> dict:
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        if "finish" in text.lower() or "final answer" in text.lower():
            return {
                "thought": text,
                "action": "finish",
                "final_answer": text,
            }

        return {
            "thought": text,
            "action": "finish",
            "final_answer": text,
        }

    def _execute_tool(self, parsed: dict) -> ToolResult:
        action = parsed.get("action", "")
        action_input = parsed.get("action_input", {})

        plan = ToolPlan(tool=action, args=action_input)
        return self.tool_runner.run_plan(plan)

    def _format_tool_result(self, result: ToolResult) -> str:
        if result.success:
            output = result.output[:2000]
            return f"Success: {output}"
        return f"Error: {result.error}"


@dataclass
class _LLMResponse:
    text: str
    success: bool
    error: str = ""
