"""
Layer 2 v2: autoDream consolidation. Source: CC TS autoDream. Memory is not
append-only — it needs background GC.

Production concept: treat memory like a heap — it accumulates garbage over time.
autoDream is the GC pass: it runs during idle time to merge duplicates, resolve
contradictions, sharpen vague facts into concrete ones, and prune stale entries.
The four phases (Orient → Gather → Consolidate → Prune) mirror how a human
reviews notes: first understand what exists, then collect it, then distill it,
then throw out what's no longer true.
"""

import json
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path.home() / ".nano-agent-anatomy" / "memory"
INDEX_FILE = MEMORY_DIR / "MEMORY.md"
MAX_INDEX_LINES = 50


class MemoryStore:
    def __init__(self, memory_dir: Path = MEMORY_DIR):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        if not INDEX_FILE.exists():
            INDEX_FILE.write_text("# Agent Memory Index\n\n")

    def load(self) -> str:
        """Read the index into the system prompt. Same as v1."""
        if INDEX_FILE.exists():
            return INDEX_FILE.read_text()
        return ""

    def save(self, key: str, summary: str):
        """Write a memory entry to disk and update the index."""
        self._write_memory(key, summary)

    def maybe_save(self, messages: list, client, model: str):
        """Ask the LLM if anything in the last 3 exchanges is worth remembering."""
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

    def consolidate(self, client, model: str):
        """autoDream: Orient → Gather → Consolidate → Prune.

        One LLM call handles both consolidation and pruning — combining them
        is cheaper and lets the model make merge/prune decisions holistically
        (a merge might make a prune moot). Runs during idle time in production.
        """
        # Phase 1 Orient: enumerate memory files, skip the index itself
        memory_files = [f for f in self.memory_dir.glob("*.md") if f.name != "MEMORY.md"]
        if not memory_files:
            return  # Nothing to consolidate — skip rather than burning a token call

        # Phase 2 Gather: one text blob with section headers so the LLM knows which
        # key each block belongs to. It can reuse or mint merged keys in its output.
        entries = [f"## {f.stem}\n{f.read_text()}" for f in memory_files]
        all_memories = "\n\n".join(entries)

        # Phase 3+4 Consolidate+Prune: single LLM call handles both.
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": (
                    "You are consolidating an agent's memory. Review all entries below.\n\n"
                    "Tasks:\n"
                    "1. Merge entries that describe the same thing\n"
                    "2. Remove entries that contradict each other (keep the newer one)\n"
                    "3. Convert vague observations into concrete facts\n"
                    "4. Remove entries older than 30 days with no recent references\n"
                    "5. Return the consolidated memories as JSON:\n"
                    '   {"consolidated": [{"key": "id", "summary": "one line fact"}]}\n\n'
                    f"Current memories:\n{all_memories}"
                ),
            }],
        )

        try:
            text = response.content[0].text
            data = json.loads(text[text.index("{"):text.rindex("}") + 1])

            # Wipe only after valid JSON is parsed — failed GC must not destroy data.
            # The LLM output becomes the new ground truth; wipe before rewriting.
            for f in self.memory_dir.glob("*.md"):
                f.unlink()
            INDEX_FILE.write_text("# Agent Memory Index\n\n")

            for mem in data.get("consolidated", []):
                self._write_memory(mem["key"], mem["summary"])

        except (json.JSONDecodeError, ValueError, KeyError):
            # Silent keep: a failed GC pass is safer than data loss.
            # The next idle cycle will try again.
            pass

    def _write_memory(self, key: str, summary: str):
        """Write {key}.md and update the index. Identical to v1."""
        entry_file = self.memory_dir / f"{key}.md"
        entry_file.write_text(
            f"# {key}\n\n{summary}\n\nSaved: {datetime.now().isoformat()}\n"
        )

        index = INDEX_FILE.read_text()
        marker = f"[{key}]"
        if marker not in index:
            lines = index.strip().split("\n")
            if len(lines) >= MAX_INDEX_LINES:
                lines = lines[:1] + lines[2:]
            lines.append(f"- [{key}]({key}.md) — {summary[:120]}")
            INDEX_FILE.write_text("\n".join(lines) + "\n")
