"""
Layer 1 v1: max_iterations + is_error denial. Source: conversation.rs (584 lines).

Two fixes over v0:

1. MAX_ITERATIONS = 16. The inner while True becomes a for loop.
   conversation.rs uses this exact number. It prevents runaway tool loops
   from burning indefinite API budget. The for/else pattern lets us
   distinguish "LLM stopped naturally" from "we hit the ceiling".

2. is_error=True in tool_result. When a tool is denied, we don't just
   skip it — we return a structured error the LLM can read. This matters:
   the LLM sees the rejection in its context and can choose a fallback.
   Without is_error, the LLM would keep trying the same denied tool.

Import TOOLS and execute_tool from v0 — they're unchanged. Only the
loop structure and denial logic are new here.
"""

import json

from anthropic import Anthropic
from loop_v0 import TOOLS, execute_tool

# 16 is the production number from conversation.rs.
# High enough to handle multi-step tasks; low enough to bound runaway loops.
MAX_ITERATIONS = 16


def is_bash_denied(command: str) -> bool:
    """Hardcoded deny rule: block rm -rf.

    Placeholder for the full permission system that arrives in v3.
    The point here is showing that denial produces is_error feedback,
    not that this specific rule is the right policy.
    """
    return "rm -rf" in command


def agent_loop(model: str = "claude-opus-4-5"):
    """Core agent loop with iteration ceiling and is_error denial feedback."""
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

        # for/else: the else block runs only if the loop exhausts its range
        # without hitting a break. That's how we know we hit the ceiling.
        for _iteration in range(MAX_ITERATIONS):
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
                for block in assistant_content:
                    if hasattr(block, "text"):
                        print(f"\nAgent: {block.text}\n")
                break  # natural completion — for/else won't fire

            tool_results = []
            for tool_use in tool_uses:
                # Deny check before execution. The hardcoded rule is a stand-in;
                # v3 replaces this with the full permissions module.
                if tool_use.name == "bash" and is_bash_denied(tool_use.input.get("command", "")):
                    print(f"  [denied] {tool_use.name}: blocked destructive command")
                    # is_error=True: LLM sees this as a tool failure, not silence.
                    # It can ask a clarifying question or try a safer path.
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": "Denied: destructive commands (rm -rf) are not allowed.",
                        "is_error": True,
                    })
                else:
                    print(f"  [tool] {tool_use.name}({json.dumps(tool_use.input)[:80]})")
                    result = execute_tool(tool_use.name, tool_use.input)
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": tool_use.id, "content": result}
                    )

            messages.append({"role": "user", "content": tool_results})

        else:
            # for/else fires here: the range was exhausted without a break.
            print(f"\n[error] Hit iteration limit ({MAX_ITERATIONS}). Stopping.\n")
