"""
Layer 2 v0: Append-only in-memory list. The tutorial version — no persistence,
no consolidation.

Production concept: the minimal viable memory substrate. Every production
memory system starts here conceptually — a list you append to. The gap between
this and v1 is exactly what persistence buys you: memories survive the process.
"""

import json


class MemoryStore:
    def __init__(self):
        # In-memory only — nothing survives process exit.
        # This forces the question: when does memory need to outlive the session?
        self._entries: list[dict] = []

    def load(self) -> str:
        """Return all memories as a formatted string for the system prompt."""
        if not self._entries:
            return ""

        lines = ["# Agent Memory\n"]
        for entry in self._entries:
            # Flat format — no file hierarchy needed when everything is in RAM
            lines.append(f"- [{entry['key']}] {entry['summary']}")
        return "\n".join(lines) + "\n"

    def save(self, key: str, summary: str):
        """Append a memory entry. No deduplication — every call adds a new entry."""
        # Appending without dedup is the core limitation this version exposes.
        # In production (v1+), _write_memory checks for marker before inserting.
        self._entries.append({"key": key, "summary": summary})

    def maybe_save(self, messages: list, client, model: str):
        """Ask the LLM if anything in the last 3 exchanges is worth remembering."""
        # Only trigger every 3 user turns — avoids burning tokens on every message.
        # Production uses background tasks so this check doesn't block the response.
        user_turns = [
            m for m in messages
            if m.get("role") == "user" and isinstance(m.get("content"), str)
        ]
        if len(user_turns) % 3 != 0:
            return

        # Window: last 3 exchanges (6 messages) — recency bias is intentional.
        # You care about what just happened, not the full history.
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
            # Extract JSON from anywhere in the response — LLMs often add prose
            data = json.loads(text[text.index("{"):text.rindex("}") + 1])
            for mem in data.get("memories", []):
                # save() here means every extraction appends — duplicates accumulate.
                # v1 fixes this with marker-based dedup in the index.
                self.save(mem["key"], mem["summary"])
        except (json.JSONDecodeError, ValueError, KeyError):
            # Silent skip: memory extraction is best-effort, not load-bearing.
            # A failed extraction never breaks the conversation.
            pass
