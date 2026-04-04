"""
Layer 2: Persistent Memory — MEMORY.md index + autoDream consolidation.

Production uses 3 parts: lightweight index (always in context),
individual memory files (on demand), and autoDream (idle consolidation).
"""

import json
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path.home() / ".agent-anatomy" / "memory"
INDEX_FILE = MEMORY_DIR / "MEMORY.md"
MAX_INDEX_LINES = 50  # Keep index small — it's always in context


class MemoryStore:
    def __init__(self, memory_dir: Path = MEMORY_DIR):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        if not INDEX_FILE.exists():
            INDEX_FILE.write_text("# Agent Memory Index\n\n")

    def load(self) -> str:
        """Load the memory index. This goes into the system prompt every turn."""
        if INDEX_FILE.exists():
            return INDEX_FILE.read_text()
        return ""

    def maybe_save(self, messages: list, client, model: str):
        """Ask the LLM if anything is worth remembering. Production does this in background."""
        # Only check every 3 exchanges to avoid spamming
        user_turns = [m for m in messages if m.get("role") == "user" and isinstance(m.get("content"), str)]
        if len(user_turns) % 3 != 0:
            return

        recent = messages[-6:]  # Last 3 exchanges
        recent_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in recent
            if isinstance(m.get("content"), str)
        )

        response = client.messages.create(
            model=model,
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Review this conversation and extract facts worth remembering
for future sessions. Return JSON: {{"memories": [{{"key": "short_id", "summary": "one line"}}]}}
Return {{"memories": []}} if nothing is worth saving.

Conversation:
{recent_text}""",
            }],
        )

        try:
            text = response.content[0].text
            data = json.loads(text[text.index("{"):text.rindex("}") + 1])
            for mem in data.get("memories", []):
                self._write_memory(mem["key"], mem["summary"])
        except (json.JSONDecodeError, ValueError, KeyError):
            pass  # LLM didn't return valid JSON — skip silently

    def _write_memory(self, key: str, summary: str):
        """Write a memory entry and update the index."""
        # Write full entry
        entry_file = self.memory_dir / f"{key}.md"
        entry_file.write_text(f"# {key}\n\n{summary}\n\nSaved: {datetime.now().isoformat()}\n")

        # Update index (append if new, skip if exists)
        index = INDEX_FILE.read_text()
        marker = f"[{key}]"
        if marker not in index:
            lines = index.strip().split("\n")
            # Enforce max index size — drop oldest if full
            if len(lines) >= MAX_INDEX_LINES:
                lines = lines[:1] + lines[2:]  # Drop first entry after header
            lines.append(f"- [{key}]({key}.md) — {summary[:120]}")
            INDEX_FILE.write_text("\n".join(lines) + "\n")

    def consolidate(self, client, model: str):
        """autoDream: Orient → Gather → Consolidate → Prune. Memory is not append-only."""
        entries = []
        for f in self.memory_dir.glob("*.md"):
            if f.name == "MEMORY.md":
                continue
            entries.append(f"## {f.stem}\n{f.read_text()}")

        if not entries:
            return

        all_memories = "\n\n".join(entries)

        response = client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"""You are consolidating an agent's memory. Review all entries below.

Tasks:
1. Merge entries that describe the same thing
2. Remove entries that contradict each other (keep the newer one)
3. Convert vague observations into concrete facts
4. Remove entries older than 30 days with no recent references
5. Return the consolidated memories as JSON:
   {{"consolidated": [{{"key": "id", "summary": "one line fact"}}]}}

Current memories:
{all_memories}""",
            }],
        )

        try:
            text = response.content[0].text
            data = json.loads(text[text.index("{"):text.rindex("}") + 1])

            # Wipe and rewrite
            for f in self.memory_dir.glob("*.md"):
                f.unlink()

            INDEX_FILE.write_text("# Agent Memory Index\n\n")
            for mem in data.get("consolidated", []):
                self._write_memory(mem["key"], mem["summary"])
        except (json.JSONDecodeError, ValueError, KeyError):
            pass  # Consolidation failed — keep existing memories
