"""
Layer 1 v0: The tutorial version — bare while True loop with no safety rails.

This is the agent loop you see in every blog post and quickstart guide.
It works — until it doesn't. The LLM can call tools forever with no exit
condition. One bad prompt → infinite API spend. No permission check means
any tool runs unconditionally. This file exists so the problems are visible
before we fix them in v1, v2, v3.
"""

import json
import subprocess

from anthropic import Anthropic

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
    """Execute a tool and return the result as a string.

    No permission check, no error boundary beyond the happy path.
    bash runs anything. write_file overwrites anything.
    This is the naive version — exactly what a tutorial ships.
    """
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


def agent_loop(model: str = "claude-opus-4-5"):
    """Core agent loop — bare while True, no safeguards.

    The inner loop (while True) is the agentic part: the LLM drives
    tool calls until it has no more to make. The outer loop collects
    user turns. Both are unbounded — the danger is in the inner one.
    """
    client = Anthropic()
    messages = []
    system = "You are a helpful assistant with access to tools."

    print("Agent ready. Type 'quit' to exit.\n")

    while True:  # outer: one iteration per user turn
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        # Inner loop: the LLM keeps calling tools until it stops on its own.
        # No ceiling. If the LLM gets stuck in a tool loop, this runs forever.
        while True:
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

            # When there are no tool calls, the LLM is done for this turn.
            if not tool_uses:
                for block in assistant_content:
                    if hasattr(block, "text"):
                        print(f"\nAgent: {block.text}\n")
                break  # exit inner loop, wait for next user turn

            # Execute every tool the LLM requested, unconditionally.
            tool_results = []
            for tool_use in tool_uses:
                print(f"  [tool] {tool_use.name}({json.dumps(tool_use.input)[:80]})")
                result = execute_tool(tool_use.name, tool_use.input)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tool_use.id, "content": result}
                )

            messages.append({"role": "user", "content": tool_results})
