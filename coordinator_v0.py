"""
Layer 4 v0: Hardcoded decomposition. Tutorial version — coordinator doesn't think, just splits.

Production insight: most "multi-agent" demos hardcode decomposition.
They look powerful but the coordinator adds no value — the developer, not
the LLM, decided what the subtasks are. Real value comes in v1 when the
LLM owns the decomposition decision.

This version exists to make the gap visible: if you hardcode "Research: X"
and "Execute: X", you haven't built a coordinator — you've built a router
with a fixed routing table.
"""

import json
import subprocess

from anthropic import Anthropic

# Worker prompt is intentionally minimal — the coordinator (this file) does
# no real thinking, so the worker is the only intelligent piece.
WORKER_SYSTEM = """You are a worker agent. Complete the task. Use tools if needed.
Be concise — your result will be combined with another worker's result."""

# Inline tools so this file is fully self-contained and importable without
# any sibling file. Each coordinator_vN can be read in isolation.
TOOLS = [
    {
        "name": "bash",
        "description": "Run a shell command and return its output.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file and return its contents.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
]


def execute_tool(name: str, tool_input: dict) -> str:
    if name == "bash":
        try:
            result = subprocess.run(
                tool_input["command"], shell=True, capture_output=True, text=True, timeout=30
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "Error: command timed out after 30s"
    elif name == "read_file":
        try:
            with open(tool_input["path"]) as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: file not found: {tool_input['path']}"
    elif name == "write_file":
        with open(tool_input["path"], "w") as f:
            f.write(tool_input["content"])
        return f"Wrote {len(tool_input['content'])} bytes to {tool_input['path']}"
    return f"Error: unknown tool: {name}"


def run_worker(task: str, client: Anthropic, model: str) -> str:
    """Run a single worker agent on a subtask.

    Separate message history per worker is the only real isolation here —
    workers cannot see each other's tool calls or intermediate reasoning.
    """
    messages = [{"role": "user", "content": task}]

    for _ in range(10):  # Cap prevents infinite tool loops
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=WORKER_SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        tool_uses = [b for b in assistant_content if b.type == "tool_use"]
        if not tool_uses:
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


def coordinate(task: str, model: str) -> str:
    """Coordinate by hardcoding the decomposition strategy.

    The split is always "Research: X" + "Execute: X" — the developer decided
    this, not the LLM. This is the anti-pattern v1 fixes: the coordinator
    should understand the task before splitting it.

    No synthesis step either — we just concatenate. That omission exposes
    another gap: collecting results without reasoning about them produces
    noise, not signal.
    """
    client = Anthropic()

    # Hardcoded decomposition: developer-defined, not LLM-defined.
    # Every task gets the same two subtasks regardless of what it actually is.
    subtasks = [
        f"Research: {task}",
        f"Execute: {task}",
    ]

    results = []
    for i, subtask in enumerate(subtasks):
        print(f"[worker {i+1}/{len(subtasks)}] {subtask[:60]}...")
        result = run_worker(subtask, client, model)
        results.append({"subtask": subtask, "result": result})
        print(f"[worker {i+1}/{len(subtasks)}] Done.")

    # Naive concatenation — no LLM synthesizes the results.
    # The caller gets raw worker output; making sense of it is their problem.
    combined = "\n\n".join(
        f"[{r['subtask']}]\n{r['result']}" for r in results
    )
    return combined
