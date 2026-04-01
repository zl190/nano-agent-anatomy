"""
Layer 4 v3: CC prompt patterns. Source: AgentTool/prompt.ts. Prompt-based enforcement, not code.

Production insight from AgentTool/prompt.ts: CC's coordinator prompt does real
work. The phrases are not flavor text — they encode behavioral contracts:

  "Brief like a smart colleague who just walked into the room" prevents
  the LLM from re-explaining the whole project in every message.

  "Never delegate understanding" blocks a class of bugs where the coordinator
  decomposes a task it didn't understand, producing subtasks that are internally
  consistent but solve the wrong problem.

  "Do not rubber-stamp weak work" is the quality gate. Without it, the
  synthesizer defaults to polite acceptance. The post-synthesis quality_check
  call gives this rule teeth: the LLM must evaluate before output ships.
"""

import json
import shutil
import tempfile
from anthropic import Anthropic
from coordinator_v2 import TOOLS, make_scoped_execute_tool

# CC prompt patterns sourced from AgentTool/prompt.ts.
# Each rule targets a specific failure mode observed in production.
COORDINATOR_SYSTEM = """You are a coordinator agent. You break complex tasks into subtasks
and delegate them to worker agents.

Communication: Brief like a smart colleague who just walked into the room — no preamble, no recap.
Never delegate understanding — clarify the task before decomposing if anything is unclear.

Decomposition: 2-4 independent subtasks, each self-contained.
Name them with action verbs ("Investigate X", not "Task 1").

Quality: Do not rubber-stamp weak work — if a worker's result is poor, say so and explain why.
A synthesis that ignores a weak result is itself weak.

Return your decomposition as JSON:
{"subtasks": ["description of subtask 1", "description of subtask 2", ...]}"""

# Worker prompt from AgentTool/prompt.ts worker variant.
# "Do not expand scope" prevents gold-plating; "explain blockers" prevents
# silent partial results that look complete but aren't.
WORKER_SYSTEM = """You are a focused worker agent. Complete exactly the task assigned.

Rules:
- Do not expand scope beyond what was asked — if the task is narrow, be narrow
- If you cannot complete the task, explain what is blocking you rather than returning partial work
- Do not summarize the task back to the coordinator — they already know it
- Use tools if needed; prefer reading evidence over assuming"""


def run_worker(task: str, client: Anthropic, model: str, scratch_dir: str) -> str:
    """Worker with CC-style prompt: focused scope, explicit blocker reporting."""
    execute_tool = make_scoped_execute_tool(scratch_dir)
    messages = [{"role": "user", "content": task}]
    for _ in range(10):
        response = client.messages.create(
            model=model, max_tokens=4096, system=WORKER_SYSTEM,
            tools=TOOLS, messages=messages,
        )
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})
        tool_uses = [b for b in assistant_content if b.type == "tool_use"]
        if not tool_uses:
            return "\n".join(b.text for b in assistant_content if hasattr(b, "text"))
        results = [
            {"type": "tool_result", "tool_use_id": tu.id,
             "content": execute_tool(tu.name, tu.input)}
            for tu in tool_uses
        ]
        messages.append({"role": "user", "content": results})
    return "[Worker hit iteration limit]"


def quality_check(synthesis: str, results: list, client: Anthropic, model: str) -> str:
    """Post-synthesis quality check — the coordinator evaluates its own output.

    Without this, the synthesizer defaults to polite acceptance. A separate
    adversarial call with explicit evaluation criteria forces critical review.
    The check runs after synthesis so it can see both the assembled answer
    and the underlying worker evidence simultaneously.
    """
    qc_prompt = (
        f"You just synthesized worker results. Before finalizing, evaluate quality.\n\n"
        f"Your synthesis:\n{synthesis}\n\n"
        f"Worker results:\n{json.dumps(results, indent=2)}\n\n"
        "For each worker result, state ADEQUATE or WEAK (with reason). "
        "Then state whether your synthesis accurately reflects the evidence quality. "
        "If any worker result was weak, say so explicitly in your final answer."
    )
    response = client.messages.create(
        model=model, max_tokens=2048, system=COORDINATOR_SYSTEM,
        messages=[{"role": "user", "content": qc_prompt}],
    )
    return response.content[0].text


def coordinate(task: str, model: str) -> str:
    """Coordinate with CC prompt patterns and a post-synthesis quality check."""
    client = Anthropic()

    print(f"[coordinator] Decomposing: {task[:80]}...")
    response = client.messages.create(
        model=model, max_tokens=1000, system=COORDINATOR_SYSTEM,
        messages=[{"role": "user", "content": task}],
    )

    try:
        text = response.content[0].text
        data = json.loads(text[text.index("{"):text.rindex("}") + 1])
        subtasks = data["subtasks"]
    except (json.JSONDecodeError, ValueError, KeyError):
        print("[coordinator] Could not parse decomposition — running as single task")
        scratch = tempfile.mkdtemp(prefix="worker_")
        try:
            return run_worker(task, client, model, scratch)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    scratch_dirs = [tempfile.mkdtemp(prefix="worker_") for _ in subtasks]
    try:
        results = []
        for i, (subtask, scratch) in enumerate(zip(subtasks, scratch_dirs)):
            print(f"[worker {i+1}/{len(subtasks)}] {subtask[:60]}...")
            result = run_worker(subtask, client, model, scratch)
            results.append({"subtask": subtask, "result": result})
            print(f"[worker {i+1}/{len(subtasks)}] Done.")

        print("[coordinator] Synthesizing...")
        synthesis_prompt = (
            f"Original task: {task}\n\nWorker results:\n{json.dumps(results, indent=2)}\n\n"
            "Synthesize these results into a coherent final answer."
        )
        response = client.messages.create(
            model=model, max_tokens=4096, system=COORDINATOR_SYSTEM,
            messages=[{"role": "user", "content": synthesis_prompt}],
        )
        synthesis = response.content[0].text

        # Quality check: coordinator must evaluate before output ships.
        # This adds one LLM call but closes the rubber-stamp gap from v1/v2.
        print("[coordinator] Quality check...")
        return quality_check(synthesis, results, client, model)
    finally:
        for d in scratch_dirs:
            shutil.rmtree(d, ignore_errors=True)
