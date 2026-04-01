"""
Layer 1 v3: permission system. Source: permissions.rs (232 lines).
Fail-secure: unknown tools → highest permission.

Replaces the hardcoded "rm -rf" check from v1/v2 with the full permission
module. Two design decisions from permissions.rs worth studying:

1. Fail-secure default: TOOL_PERMISSIONS.get(unknown_tool) falls back to
   DANGER_FULL_ACCESS, not READ_ONLY. Counter-intuitive — but correct. If
   you don't know what a tool does, you should require maximum permission
   to run it, not silently allow it. Unknown → dangerous.

2. Denial is structured feedback, not silence. policy.authorize() returns
   (bool, str). The denial reason string goes into the tool_result as
   is_error=True. The LLM sees exactly why it was blocked and can adapt.

This file is the end state. loop.py = this + Layer 2 (memory) +
Layer 3 (context compression) integrated.
"""

import json

from anthropic import Anthropic
from loop_v0 import TOOLS, execute_tool
from loop_v2 import MAX_ITERATIONS, run_turn as _run_turn_v2
from permissions import PermissionMode, PermissionPolicy


def run_turn(
    client: Anthropic,
    model: str,
    system: str,
    messages: list,
    policy: PermissionPolicy,
    token_budget: int = 0,
) -> dict:
    """Run one user turn with full permission checks.

    Same signature as v2.run_turn but adds policy parameter.
    Returns the same stop_reason dict.
    """
    cumulative_tokens = 0

    for _iteration in range(MAX_ITERATIONS):
        response = client.messages.create(
            model=model, max_tokens=4096, system=system, tools=TOOLS, messages=messages,
        )

        input_tok = response.usage.input_tokens
        output_tok = response.usage.output_tokens
        cumulative_tokens += input_tok + output_tok

        budget_str = str(token_budget) if token_budget > 0 else "unlimited"
        print(f"  [tokens] input={input_tok} output={output_tok} cumulative={cumulative_tokens}/{budget_str}")

        if token_budget > 0 and cumulative_tokens >= token_budget:
            messages.append({"role": "assistant", "content": response.content})
            return {"stop_reason": "max_budget_reached", "tokens_used": cumulative_tokens}

        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        tool_uses = [b for b in assistant_content if b.type == "tool_use"]

        if not tool_uses:
            for block in assistant_content:
                if hasattr(block, "text"):
                    print(f"\nAgent: {block.text}\n")
            return {"stop_reason": "completed", "tokens_used": cumulative_tokens}

        tool_results = []
        for tool_use in tool_uses:
            # Permission check BEFORE execution. The policy knows the required
            # level per tool (from TOOL_PERMISSIONS) and the current mode.
            # Unknown tools default to DANGER_FULL_ACCESS inside the module.
            allowed, reason = policy.authorize(tool_use.name, tool_use.input)

            if allowed:
                print(f"  [tool] {tool_use.name}({json.dumps(tool_use.input)[:80]})")
                result = execute_tool(tool_use.name, tool_use.input)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tool_use.id, "content": result}
                )
            else:
                # Return the policy's denial reason as structured LLM feedback.
                # The reason string tells the LLM which permission level was
                # required vs. active — enough context to choose a fallback.
                print(f"  [denied] {tool_use.name}: {reason}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": reason,
                    "is_error": True,
                })

        messages.append({"role": "user", "content": tool_results})

    return {"stop_reason": "max_turns_reached", "tokens_used": cumulative_tokens}


def agent_loop(
    model: str = "claude-opus-4-5",
    token_budget: int = 0,
    permission_mode: PermissionMode = PermissionMode.DANGER_FULL_ACCESS,
):
    """REPL wrapper. Permission mode controls which tools the LLM can use."""
    client = Anthropic()
    messages = []
    system = "You are a helpful assistant with access to tools."

    # The policy object is created once per session and passed into each turn.
    # In production, a prompter callback can be injected for interactive
    # approval at the WORKSPACE_WRITE → DANGER boundary.
    policy = PermissionPolicy(permission_mode)

    budget_str = str(token_budget) if token_budget > 0 else "unlimited"
    print(f"Agent ready. Mode: {permission_mode.name}. Budget: {budget_str}. Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        result = run_turn(client, model, system, messages, policy, token_budget)

        if result["stop_reason"] == "max_budget_reached":
            print(f"\n[error] Token budget exhausted ({result['tokens_used']}/{token_budget}). Stopping.\n")
        elif result["stop_reason"] == "max_turns_reached":
            print(f"\n[error] Hit iteration limit ({MAX_ITERATIONS}). Stopping.\n")
