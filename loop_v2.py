"""
Layer 1 v2: dual stop conditions (iterations + token budget). Source: CC TS query_engine.

Adds token budget tracking over v1. In production (CC TypeScript query_engine),
budget is a first-class parameter — not an afterthought. Two reasons:

1. Cost control: unbounded token use = unbounded spend. Budget makes the
   ceiling explicit and communicable to callers.

2. stop_reason as structured output: callers need to know WHY the loop
   stopped — not just that it did. "max_budget_reached" is different from
   "max_turns_reached" is different from "completed". The caller can choose
   to re-invoke with more budget, surface an error, or treat it as success.

token_budget=0 means unlimited (preserves v1 behaviour).
"""

import json

from anthropic import Anthropic
from loop_v0 import TOOLS, execute_tool
from loop_v1 import MAX_ITERATIONS, is_bash_denied


def run_turn(
    client: Anthropic,
    model: str,
    system: str,
    messages: list,
    token_budget: int = 0,
) -> dict:
    """Run one user turn (inner tool loop) and return a result dict.

    Returns:
        {
            "stop_reason": "completed" | "max_turns_reached" | "max_budget_reached",
            "tokens_used": int,   # cumulative for this turn
        }

    Separating the turn runner from the outer REPL makes stop_reason
    testable without mocking stdin. Production wraps this in async.
    """
    cumulative_tokens = 0

    for _iteration in range(MAX_ITERATIONS):
        response = client.messages.create(
            model=model, max_tokens=4096, system=system, tools=TOOLS, messages=messages,
        )

        # Track tokens per API call. input includes the full context window
        # (all messages), so cumulative_tokens grows faster than output alone.
        input_tok = response.usage.input_tokens
        output_tok = response.usage.output_tokens
        cumulative_tokens += input_tok + output_tok

        budget_str = str(token_budget) if token_budget > 0 else "unlimited"
        print(f"  [tokens] input={input_tok} output={output_tok} cumulative={cumulative_tokens}/{budget_str}")

        # Budget check comes AFTER getting the response — we can't predict
        # how many tokens an API call will consume before making it.
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
            if tool_use.name == "bash" and is_bash_denied(tool_use.input.get("command", "")):
                print(f"  [denied] {tool_use.name}: blocked destructive command")
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

    return {"stop_reason": "max_turns_reached", "tokens_used": cumulative_tokens}


def agent_loop(model: str = "claude-opus-4-5", token_budget: int = 0):
    """REPL wrapper. token_budget=0 means unlimited."""
    client = Anthropic()
    messages = []
    system = "You are a helpful assistant with access to tools."

    budget_str = str(token_budget) if token_budget > 0 else "unlimited"
    print(f"Agent ready. Token budget: {budget_str}. Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        result = run_turn(client, model, system, messages, token_budget)

        # stop_reason drives caller behaviour. "completed" is the happy path.
        if result["stop_reason"] == "max_budget_reached":
            print(f"\n[error] Token budget exhausted ({result['tokens_used']}/{token_budget}). Stopping.\n")
        elif result["stop_reason"] == "max_turns_reached":
            print(f"\n[error] Hit iteration limit ({MAX_ITERATIONS}). Stopping.\n")
