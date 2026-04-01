"""
Layer 4: Multi-Agent Coordination
===================================

The biggest surprise from production agent systems: orchestration logic
is a prompt, not code.

The coordinator doesn't call worker.run(task) — it tells the LLM
"you are a coordinator, here are your workers, delegate wisely."
The LLM decides task decomposition, assignment, and quality checks.

Production systems use:
  - XML protocol for task notifications (<task-notification> with status, summary, tokens)
  - Scratch directories for worker isolation
  - System prompts like "Do not rubber-stamp weak work"

This file implements the pattern in ~120 lines.
"""

import json
from anthropic import Anthropic
from loop import TOOLS, execute_tool


COORDINATOR_SYSTEM = """You are a coordinator agent. You break complex tasks into subtasks
and delegate them to worker agents.

Rules:
- Decompose the task into 2-4 independent subtasks
- Each subtask must be self-contained (a worker can't see other workers' results)
- After collecting results, synthesize a final answer
- Do not rubber-stamp weak work — if a worker's result is poor, say so

Return your decomposition as JSON:
{"subtasks": ["description of subtask 1", "description of subtask 2", ...]}"""


WORKER_SYSTEM = """You are a worker agent executing a specific subtask.
Complete the task thoroughly. Use tools if needed.
Be concise in your final answer — the coordinator will synthesize."""


def run_worker(task: str, client: Anthropic, model: str, memory=None) -> str:
    """
    Run a single worker agent on a subtask.

    Each worker gets its own message history (isolation).
    Production systems use scratch directories and separate processes.
    We use separate message lists — same principle, simpler implementation.
    """
    system = WORKER_SYSTEM
    if memory:
        context = memory.load()
        if context:
            system += f"\n\nContext from memory:\n{context}"

    messages = [{"role": "user", "content": task}]

    # Worker runs the same tool loop as the main agent
    for _ in range(10):  # Max 10 iterations to prevent runaway
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        tool_uses = [b for b in assistant_content if b.type == "tool_use"]
        if not tool_uses:
            # Worker is done — extract text response
            texts = [b.text for b in assistant_content if hasattr(b, "text")]
            return "\n".join(texts)

        tool_results = []
        for tool_use in tool_uses:
            result = execute_tool(tool_use.name, tool_use.input)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": tool_use.id, "content": result}
            )
        messages.append({"role": "user", "content": tool_results})

    return "[Worker hit iteration limit]"


def coordinate(task: str, model: str, memory=None) -> str:
    """
    Coordinate a complex task using multiple worker agents.

    Flow:
      1. Coordinator decomposes the task
      2. Workers execute subtasks in parallel (sequential here for clarity)
      3. Coordinator synthesizes results

    Production adds: parallel execution, progress tracking, retry logic,
    and XML-based status notifications between coordinator and workers.
    """
    client = Anthropic()

    # Step 1: Decompose
    print(f"[coordinator] Decomposing task: {task[:80]}...")
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        system=COORDINATOR_SYSTEM,
        messages=[{"role": "user", "content": task}],
    )

    try:
        text = response.content[0].text
        data = json.loads(text[text.index("{"):text.rindex("}") + 1])
        subtasks = data["subtasks"]
    except (json.JSONDecodeError, ValueError, KeyError):
        # Fallback: run as single task
        print("[coordinator] Could not decompose — running as single task")
        return run_worker(task, client, model, memory)

    # Step 2: Execute workers
    results = []
    for i, subtask in enumerate(subtasks):
        print(f"[worker {i+1}/{len(subtasks)}] {subtask[:60]}...")
        result = run_worker(subtask, client, model, memory)
        results.append({"subtask": subtask, "result": result})
        print(f"[worker {i+1}/{len(subtasks)}] Done.")

    # Step 3: Synthesize
    print("[coordinator] Synthesizing results...")
    synthesis_prompt = f"""Original task: {task}

Worker results:
{json.dumps(results, indent=2)}

Synthesize these results into a coherent final answer.
Flag any weak or contradictory results."""

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=COORDINATOR_SYSTEM,
        messages=[{"role": "user", "content": synthesis_prompt}],
    )

    return response.content[0].text
