"""
Layer 1: The Agent Loop — the core tool-use cycle.
Production equivalent: conversation.rs (584 lines) in claw-code.

Key production patterns implemented:
  - max_iterations=16 hard limit (not infinite while True)
  - Permission check BEFORE tool execution
  - Denied tools return is_error=true tool_result to LLM
  - LLM perceives rejections and can choose fallback strategies
"""

import json
from anthropic import Anthropic
from permissions import PermissionPolicy, PermissionMode

MAX_ITERATIONS = 16  # Production uses 16. Prevents runaway tool loops.

# --- Tool definitions (the agent's hands) ---

TOOLS = [
    {
        "name": "bash",
        "description": "Run a shell command and return its output.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "The command to run"}},
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file and return its contents.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to the file"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
]


def execute_tool(name: str, tool_input: dict) -> str:
    """Execute a tool and return the result as a string."""
    import subprocess

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


def agent_loop(model: str, memory=None, compressor=None, permission_mode=None):
    """Core agent loop with permission checks and iteration limits."""
    client, messages = Anthropic(), []
    policy = PermissionPolicy(permission_mode or PermissionMode.DANGER_FULL_ACCESS)

    # Layer 2: Load memory into system prompt if available
    system = "You are a helpful assistant with access to tools."
    if memory:
        context = memory.load()
        if context:
            system += f"\n\nYour memory from previous sessions:\n{context}"

    print("Agent ready. Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        # Layer 3: Compress context if needed
        if compressor:
            messages = compressor.maybe_compress(messages)

        # The loop: keep going until no tool calls or iteration limit
        for _iteration in range(MAX_ITERATIONS):
            response = client.messages.create(
                model=model, max_tokens=4096, system=system,
                tools=TOOLS, messages=messages,
            )

            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            tool_uses = [b for b in assistant_content if b.type == "tool_use"]
            if not tool_uses:
                for block in assistant_content:
                    if hasattr(block, "text"):
                        print(f"\nAgent: {block.text}\n")
                break

            # Execute each tool with permission check
            tool_results = []
            for tool_use in tool_uses:
                allowed, reason = policy.authorize(tool_use.name, tool_use.input)
                if allowed:
                    print(f"  [tool] {tool_use.name}({json.dumps(tool_use.input)[:80]})")
                    result = execute_tool(tool_use.name, tool_use.input)
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": tool_use.id, "content": result}
                    )
                else:
                    # Denied: write reason as is_error=true so LLM perceives rejection
                    print(f"  [denied] {tool_use.name}: {reason}")
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": tool_use.id,
                         "content": reason, "is_error": True}
                    )

            messages.append({"role": "user", "content": tool_results})
        else:
            print(f"\n[error] Hit iteration limit ({MAX_ITERATIONS}). Stopping.\n")

        # Layer 2: Save to memory after each exchange
        if memory:
            memory.maybe_save(messages, client, model)
