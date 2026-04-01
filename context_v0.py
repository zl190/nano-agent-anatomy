"""
Layer 3 v0: LLM-based summarization. The tutorial version — costs tokens,
unpredictable output.

Production concept: the naive approach every tutorial shows. Summarize old
messages with an LLM call. The problem: you spend tokens to save tokens,
and the LLM can hallucinate, restructure, or drop critical context. No test
can verify correctness because the output is probabilistic.

This file exists to show what production code does NOT do, before showing
what it does instead.
"""

import re
from anthropic import Anthropic


def count_tokens_approx(messages: list) -> int:
    """Approximate token count: len/4 + 1 per content block.
    Production uses this heuristic — exact counting requires a tokenizer call,
    which costs latency and money, and the ~20% error margin is acceptable for
    a compression trigger."""
    total = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            total += len(content) // 4 + 1
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total += len(str(block)) // 4 + 1
                elif hasattr(block, "text"):
                    total += len(block.text) // 4 + 1
    return total


class ContextCompressor:
    def __init__(
        self,
        client: Anthropic,
        model: str,
        max_tokens: int = 8000,
        min_messages: int = 10,
        keep_recent: int = 4,
    ):
        # Requires an Anthropic client because compression is itself an LLM call.
        # This is the core cost of the tutorial approach: you must already have
        # a conversation to summarize it, so every compaction burns a turn.
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.min_messages = min_messages
        self.keep_recent = keep_recent

    def should_compress(self, messages: list) -> bool:
        """Single condition: token count exceeds max.
        Tutorial version checks only one dimension. Production uses dual trigger
        (both message count AND tokens) to avoid compressing tiny-but-long messages
        or huge-but-short histories independently."""
        return count_tokens_approx(messages) > self.max_tokens

    def maybe_compress(self, messages: list) -> list:
        """If over budget, call the LLM to summarize old messages.

        The tutorial approach: hand the history to the LLM and ask nicely.
        Problems this creates:
          1. You spend tokens to save tokens — net negative until history is very long.
          2. Output is probabilistic: the LLM may invent decisions or drop tasks.
          3. Untestable: you can't assert correctness without another LLM call.
          4. The LLM may call tools if any are bound — catastrophic mid-compaction."""
        if not self.should_compress(messages):
            return messages

        old = messages[:-self.keep_recent]
        recent = messages[-self.keep_recent:]

        # Build the conversation to summarize as a flat string.
        # We join rather than pass as messages so the LLM sees it as data, not dialogue.
        conversation_text = "\n\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in old
            if isinstance(m.get("content"), str)
        )

        # Single-shot summarization call — no system prompt, no structured output.
        # The tutorial version trusts the LLM to "just do the right thing."
        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Summarize this conversation concisely, preserving key "
                        "decisions and pending tasks:\n\n" + conversation_text
                    ),
                }
            ],
        )

        summary_text = response.content[0].text

        # Wrap in a synthetic exchange so the conversation still alternates roles.
        # The LLM expects user/assistant alternation; a bare system summary breaks
        # some providers and confuses others.
        compressed = [
            {"role": "user", "content": f"[Summary] {summary_text}"},
            {"role": "assistant", "content": "Understood."},
        ] + recent

        print(f"  [compress-v0] {len(old)} messages → LLM summary ({len(summary_text)} chars)")
        return compressed
