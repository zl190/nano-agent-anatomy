"""
Layer 4 v1: LLM-driven decomposition. Source: claw-code AgentTool.
The LLM decides WHAT, code decides HOW.

Production insight from claw-code's AgentTool: the coordinator prompt is the
real product. The decomposition isn't in a routing table — the LLM reads the
task, decides how many subtasks make sense, and names them. Code only handles
the plumbing (JSON parsing, worker dispatch, synthesis API call).

This is why "orchestration is a prompt, not code" — the interesting decisions
live in COORDINATOR_SYSTEM, not in coordinate().
"""

import json
from anthropic import Anthropic

# Import shared tool definitions from v0 to stay within the 150-line budget.
# TOOLS is identical across versions — the progression is in the coordinator
# logic, not in the tool set.
from coordinator_v0 import TOOLS, execute_tool

COORDINATOR_SYSTEM = """You are a coordinator agent. You break complex tasks into subtasks
and delegate them to worker agents.

Rules:
- Decompose the task into 2-4 independent subtasks
- Each subtask must be self-contained (a worker cannot see other workers' results)
- After collecting worker results, synthesize a coherent final answer
- Do not rubber-stamp weak work — if a worker's result is poor, say so

Return your decomposition as JSON:
{"subtasks": ["description of subtask 1", "description of subtask 2", ...]}"""

WORKER_SYSTEM = """You are a worker agent executing a specific subtask.
Complete the task thoroughly. Use tools if needed.
Be concise in your final answer — the coordinator will synthesize."""


def run_worker(task: str, client: Anthropic, model: str) -> str:
    """Single worker: isolated message history, capped at 10 iterations."""
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


def coordinate(task: str, model: str) -> str:
    """Coordinate using LLM decomposition + LLM synthesis.

    Two LLM calls bookend the worker calls:
      1. Decomposition: LLM reads the task and decides on subtasks
      2. Synthesis: LLM reads all worker results and writes the final answer

    The fallback (run as single task) matters in production: a coordinator
    that crashes on bad JSON is worse than one that degrades gracefully.
    """
    client = Anthropic()

    # Step 1: LLM decides the decomposition — the key difference from v0.
    print(f"[coordinator] Decomposing: {task[:80]}...")
    response = client.messages.create(
        model=model, max_tokens=1000, system=COORDINATOR_SYSTEM,
        messages=[{"role": "user", "content": task}],
    )

    try:
        text = response.content[0].text
        # Slice out JSON even if the LLM wraps it in explanation text
        data = json.loads(text[text.index("{"):text.rindex("}") + 1])
        subtasks = data["subtasks"]
    except (json.JSONDecodeError, ValueError, KeyError):
        # Fallback: LLM couldn't produce valid JSON — degrade to single worker.
        # Better to run than crash; quality review should catch the degradation.
        print("[coordinator] Could not parse decomposition — running as single task")
        return run_worker(task, client, model)

    # Step 2: Workers run sequentially — parallel is a performance concern,
    # not a correctness concern. Sequential is correct and easier to reason about.
    results = []
    for i, subtask in enumerate(subtasks):
        print(f"[worker {i+1}/{len(subtasks)}] {subtask[:60]}...")
        result = run_worker(subtask, client, model)
        results.append({"subtask": subtask, "result": result})
        print(f"[worker {i+1}/{len(subtasks)}] Done.")

    # Step 3: LLM synthesizes — it can spot contradictions and flag weak results.
    print("[coordinator] Synthesizing...")
    synthesis_prompt = (
        f"Original task: {task}\n\nWorker results:\n{json.dumps(results, indent=2)}\n\n"
        "Synthesize these results into a coherent final answer. "
        "Flag any weak or contradictory results."
    )
    response = client.messages.create(
        model=model, max_tokens=4096, system=COORDINATOR_SYSTEM,
        messages=[{"role": "user", "content": synthesis_prompt}],
    )
    return response.content[0].text
