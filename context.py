"""
Layer 3: Context Compression — deterministic, no LLM calls.
Production equivalent: compact.rs (485 lines) in claw-code.

Key production insight: compaction does NOT call the LLM. It uses
deterministic rules — stats, keyword extraction, path scanning.
This is cheaper, faster, and fully testable.

Production also:
  - Inserts summary as System role (not User — avoids breaking alternation)
  - Adds suppress_follow_up_questions to stop LLM from recapping
  - Uses dual trigger: message count AND token estimate both exceeded
  - Caps summary size (160 chars per entry, 8 key files max)
"""

import re


def count_tokens_approx(messages: list) -> int:
    """Approximate token count: len/4 + 1. Production uses this too — exact
    counting needs a tokenizer call, which costs more than the ~20% error."""
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
    """Extract file paths from text. Production scans for tokens with /
    and known extensions (rs/ts/js/py/md/json)."""
    pattern = r'[\w./~-]+\.(?:py|ts|js|rs|md|json|yaml|toml)'
    paths = list(dict.fromkeys(re.findall(pattern, text)))  # dedupe, preserve order
    return paths[:max_paths]


def infer_pending_work(messages: list) -> list[str]:
    """Scan recent messages for pending work keywords.
    Production uses: todo, next, pending, follow up, remaining."""
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
    """Deterministic summary — no LLM call. Extracts structure from messages.
    Production: stats + recent user requests + tools used + key files + pending work."""
    user_msgs = [m for m in messages if m.get("role") == "user" and isinstance(m.get("content"), str)]
    assistant_msgs = [m for m in messages if m.get("role") == "assistant"]

    # Tools used (deduplicated)
    tools_used = set()
    for m in messages:
        content = m.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    tools_used.add("tool_result")

    # Recent user requests (last 3, truncated)
    recent_requests = [m["content"][:160] for m in user_msgs[-3:]]

    # Key files mentioned
    all_text = " ".join(m.get("content", "") for m in messages if isinstance(m.get("content"), str))
    key_files = extract_file_paths(all_text)

    # Pending work
    pending = infer_pending_work(messages)

    parts = [
        f"<summary>",
        f"Messages: {len(user_msgs)} user, {len(assistant_msgs)} assistant",
        f"Recent requests: {'; '.join(recent_requests)}" if recent_requests else "",
        f"Key files: {', '.join(key_files)}" if key_files else "",
        f"Pending: {'; '.join(pending)}" if pending else "",
        f"</summary>",
    ]
    return "\n".join(p for p in parts if p)


class ContextCompressor:
    def __init__(self, max_tokens: int = 8000, min_messages: int = 10, keep_recent: int = 4):
        """Dual trigger: compress only when BOTH conditions met (production pattern)."""
        self.max_tokens = max_tokens
        self.min_messages = min_messages
        self.keep_recent = keep_recent

    def should_compress(self, messages: list) -> bool:
        """Dual condition: message count AND token estimate both exceeded."""
        return (len(messages) > self.min_messages
                and count_tokens_approx(messages) > self.max_tokens)

    def maybe_compress(self, messages: list) -> list:
        """Compress if over budget. Returns (possibly compressed) message list.

        Production pattern: summary is a System-role message (not User),
        followed by a continuation prompt that suppresses follow-up questions."""
        if not self.should_compress(messages):
            return messages

        old = messages[:-self.keep_recent]
        recent = messages[-self.keep_recent:]

        summary = summarize_messages(old)

        # Continuation message: suppress LLM's urge to recap
        # Production wording is specific — vague instructions get ignored
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

        print(f"  [compress] {len(old)} messages → deterministic summary ({len(summary)} chars)")
        return compressed
