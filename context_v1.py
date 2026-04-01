"""
Layer 3 v1: Deterministic extraction. Source: compact.rs (485 lines).
Zero LLM calls — cheaper, faster, testable.

Production concept: Claude Code's compact.rs replaces LLM summarization with
pure code. It scans messages for structure: paths, keywords, counts. Output is
reproducible — the same history always produces the same summary. This makes
compression a pure function you can unit-test without mocking an API.

No Anthropic dependency. Zero cost per compaction. Arbitrarily frequent.
"""

import re


def count_tokens_approx(messages: list) -> int:
    """Approximate token count: len/4 + 1 per content block.
    Heuristic is good enough for a trigger — exact counting costs a round-trip."""
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


def extract_file_paths(text: str, max_paths: int = 8) -> list[str]:
    """Regex scan for tokens that look like file paths.
    Production (compact.rs) scans for / tokens with known extensions.
    Capping at max_paths avoids bloating the summary with every log line."""
    pattern = r'[\w./~-]+\.(?:py|ts|js|rs|md|json|yaml|toml)'
    paths = list(dict.fromkeys(re.findall(pattern, text)))  # dedupe, preserve order
    return paths[:max_paths]


def infer_pending_work(messages: list) -> list[str]:
    """Keyword scan over recent messages to surface pending tasks.
    Production keywords: todo, next, pending, follow up, remaining, still need.
    Only scans last 6 messages — older pending items are stale by definition."""
    keywords = ("todo", "next", "pending", "follow up", "remaining", "still need")
    pending = []
    for m in messages[-6:]:
        content = m.get("content", "")
        if not isinstance(content, str):
            continue
        for line in content.split("\n"):
            if any(kw in line.lower() for kw in keywords):
                pending.append(line.strip()[:160])
    return pending[:5]


def summarize_messages(messages: list) -> str:
    """Deterministic summary — no LLM call.
    Production pattern: stats + recent user requests + key files + pending work.
    Everything is extracted from structure, not inferred from meaning.
    This is the key insight of compact.rs: structure outlives meaning in compression."""
    user_msgs = [m for m in messages if m.get("role") == "user" and isinstance(m.get("content"), str)]
    assistant_msgs = [m for m in messages if m.get("role") == "assistant"]

    # Recent user requests — last 3, truncated to 160 chars each.
    # These capture intent without committing to exact wording.
    recent_requests = [m["content"][:160] for m in user_msgs[-3:]]

    # Key files — scan all text content for path-shaped tokens.
    all_text = " ".join(
        m.get("content", "") for m in messages if isinstance(m.get("content"), str)
    )
    key_files = extract_file_paths(all_text)

    # Pending work — keyword scan over tail of conversation.
    pending = infer_pending_work(messages)

    parts = [
        "<summary>",
        f"Messages: {len(user_msgs)} user, {len(assistant_msgs)} assistant",
        f"Recent requests: {'; '.join(recent_requests)}" if recent_requests else "",
        f"Key files: {', '.join(key_files)}" if key_files else "",
        f"Pending: {'; '.join(pending)}" if pending else "",
        "</summary>",
    ]
    return "\n".join(p for p in parts if p)


class ContextCompressor:
    def __init__(self, max_tokens: int = 8000, min_messages: int = 10, keep_recent: int = 4):
        """Dual trigger: compress only when BOTH message count AND token count exceeded.
        Single-dimension triggers cause premature compression (message-count-only fires
        on short exchanges) or delayed compression (token-only fires on wall-of-text
        single messages that are actually fine to keep)."""
        self.max_tokens = max_tokens
        self.min_messages = min_messages
        self.keep_recent = keep_recent

    def should_compress(self, messages: list) -> bool:
        """Dual condition: message count AND token estimate both exceeded.
        Production uses this to avoid edge cases at either extreme."""
        return (
            len(messages) > self.min_messages
            and count_tokens_approx(messages) > self.max_tokens
        )

    def maybe_compress(self, messages: list) -> list:
        """Compress if over budget. Deterministic — no LLM call, no cost.

        The suppress-follow-up continuation is specific wording from production.
        Vague instructions ('continue normally') get ignored. The LLM needs to
        be told explicitly not to recap, acknowledge, or preface."""
        if not self.should_compress(messages):
            return messages

        old = messages[:-self.keep_recent]
        recent = messages[-self.keep_recent:]

        summary = summarize_messages(old)

        # Suppression prompt: copied from production because vague alternatives fail.
        # Without this, the LLM opens every response post-compression with
        # "Based on the summary, it seems we were..." — which wastes tokens and
        # breaks the illusion of continuity.
        continuation = (
            "Previous conversation was compressed. Summary above. "
            "Recent messages are preserved verbatim below. "
            "Resume directly — do not acknowledge the summary, "
            "do not recap what was happening, "
            "and do not preface with continuation text."
        )

        compressed = [
            {"role": "user", "content": f"{summary}\n\n{continuation}"},
            {"role": "assistant", "content": "Understood. Continuing from where we left off."},
        ] + recent

        print(f"  [compress-v1] {len(old)} messages → deterministic summary ({len(summary)} chars)")
        return compressed
