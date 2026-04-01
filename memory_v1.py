"""
Layer 2 v1: File-based memory with MEMORY.md index. Source: claw-code memdir/
subsystem. Index always in context, details on demand.

Production concept: split memory into two tiers — a lightweight index that fits
in every system prompt, and full-detail files fetched only when the agent needs
them. The index is the table of contents; the files are the chapters. This is
the same pattern as a search index: you scan the index, retrieve only what hits.
"""

import json
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path.home() / ".nano-agent-anatomy" / "memory"
INDEX_FILE = MEMORY_DIR / "MEMORY.md"

# 50 lines keeps the index under ~3KB — small enough to include in every
# system prompt without burning meaningful context budget.
MAX_INDEX_LINES = 50


class MemoryStore:
    def __init__(self, memory_dir: Path = MEMORY_DIR):
        self.memory_dir = memory_dir
        # Create the directory tree on first use — agents start with empty memory.
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        # Header-only index on first run — load() returns something non-empty
        # even before any memories are saved, which is a cleaner system prompt.
        if not INDEX_FILE.exists():
            INDEX_FILE.write_text("# Agent Memory Index\n\n")

    def load(self) -> str:
        """Read the index file. This goes into the system prompt every turn.

        Only the index — not the full memory files — travels with every request.
        Full files are available on demand (the agent can ask to read them).
        This is the key cost-control insight: token budget scales with index
        size, not total memory size.
        """
        if INDEX_FILE.exists():
            return INDEX_FILE.read_text()
        return ""

    def save(self, key: str, summary: str):
        """Write a memory entry to disk and update the index."""
        self._write_memory(key, summary)

    def maybe_save(self, messages: list, client, model: str):
        """Ask the LLM if anything in the last 3 exchanges is worth remembering."""
        # Same 3-turn cadence as v0 — the file I/O doesn't change the trigger logic.
        user_turns = [
            m for m in messages
            if m.get("role") == "user" and isinstance(m.get("content"), str)
        ]
        if len(user_turns) % 3 != 0:
            return

        recent = messages[-6:]
        recent_text = "\n".join(
            f"{m['role']}: {m['content']}"
            for m in recent
            if isinstance(m.get("content"), str)
        )

        response = client.messages.create(
            model=model,
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": (
                    "Review this conversation and extract facts worth remembering "
                    "for future sessions. Return JSON: "
                    '{"memories": [{"key": "short_id", "summary": "one line"}]} '
                    'Return {"memories": []} if nothing is worth saving.\n\n'
                    f"Conversation:\n{recent_text}"
                ),
            }],
        )

        try:
            text = response.content[0].text
            data = json.loads(text[text.index("{"):text.rindex("}") + 1])
            for mem in data.get("memories", []):
                self._write_memory(mem["key"], mem["summary"])
        except (json.JSONDecodeError, ValueError, KeyError):
            pass

    def _write_memory(self, key: str, summary: str):
        """Write {key}.md and update the index. Deduplicates by key marker."""
        # Full detail file — stores the summary plus a timestamp for autoDream
        # pruning in v2. Timestamp is what lets the prune phase know age.
        entry_file = self.memory_dir / f"{key}.md"
        entry_file.write_text(
            f"# {key}\n\n{summary}\n\nSaved: {datetime.now().isoformat()}\n"
        )

        index = INDEX_FILE.read_text()
        marker = f"[{key}]"

        # Dedup: if this key already appears in the index, don't add a second
        # entry. v0's append-only list accumulates duplicates — this marker
        # check is the minimal fix. The key is the identity, not the summary.
        if marker not in index:
            lines = index.strip().split("\n")

            # Index budget enforcement: drop the oldest entry (line after header)
            # when full. FIFO eviction — simple and predictable.
            # Real production might rank by recency-weighted access frequency.
            if len(lines) >= MAX_INDEX_LINES:
                lines = lines[:1] + lines[2:]  # Keep header, drop entry at index 1

            # Link format matches Markdown conventions — the agent (and a human
            # reading the index) can navigate to the full file via the link.
            lines.append(f"- [{key}]({key}.md) — {summary[:120]}")
            INDEX_FILE.write_text("\n".join(lines) + "\n")
