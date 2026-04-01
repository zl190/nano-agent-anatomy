"""
Layer 3 v3: NO_TOOLS_PREAMBLE + dual trigger.
Source: CC TypeScript compact/prompt.ts. Full production pattern.

1. NO_TOOLS_PREAMBLE: a tool-aware model may emit tool_use JSON even without
   tools bound — rejected by the API, wasting the turn. Blunt pre-emption.

2. Dual trigger: message count AND token count both exceeded. Single-dimension
   triggers fire on huge-single-message or tiny-many-message edge cases.
"""

import re
from anthropic import Anthropic

# Must come first — models attend more strongly to top-of-prompt content.
# Subtle phrasing ('please only respond with text') is overridden by the
# model's trained tool-use behavior. Blunt is necessary.
NO_TOOLS_PREAMBLE = (
    "You have no tools available in this turn. "
    "Tool calls will be REJECTED and will waste your only turn. "
    "Respond with text only."
)


def count_tokens_approx(messages: list) -> int:
    """Approximate token count: len/4 + 1 per content block."""
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
    """Regex scan for file path tokens with known extensions."""
    pattern = r'[\w./~-]+\.(?:py|ts|js|rs|md|json|yaml|toml)'
    return list(dict.fromkeys(re.findall(pattern, text)))[:max_paths]


def infer_pending_work(messages: list) -> list[str]:
    """Keyword scan over recent messages for pending task signals."""
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


def strip_analysis_tags(text: str) -> str:
    """Remove <analysis>...</analysis> blocks. Internal reasoning stays internal."""
    return re.sub(r'<analysis>.*?</analysis>', '', text, flags=re.DOTALL).strip()


def _build_compaction_prompt(messages: list) -> str:
    """9-section schema prefixed with NO_TOOLS_PREAMBLE (position matters)."""
    u = [m for m in messages if m.get("role") == "user" and isinstance(m.get("content"), str)]
    a = [m for m in messages if m.get("role") == "assistant"]
    all_text = " ".join(m.get("content", "") for m in messages if isinstance(m.get("content"), str))
    files = extract_file_paths(all_text)
    pending = infer_pending_work(messages)
    transcript = "\n\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages if isinstance(m.get("content"), str)
    )
    return f"""{NO_TOOLS_PREAMBLE}

You are compacting a conversation. Analyze and summarize it.

Output format (required):
<analysis>
Internal reasoning about what matters most. Not stored.
</analysis>
<summary>
1. Conversation stats: {len(u)} user messages, {len(a)} assistant messages
2. User intent: <what the user is trying to accomplish overall>
3. Key decisions: <decisions made so far>
4. Tools used: <tools invoked and their outcomes>
5. Files modified: {', '.join(files) if files else 'none identified'}
6. Errors encountered: <errors and how they were resolved>
7. Pending tasks: {'; '.join(pending) if pending else 'none identified'}
8. Environment state: <relevant env facts: cwd, language, framework>
9. Important context: <anything else the next session must know>
</summary>

Conversation to compact:
{transcript}"""


class ContextCompressor:
    def __init__(self, client: Anthropic, model: str,
                 max_tokens: int = 8000, min_messages: int = 10, keep_recent: int = 4):
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.min_messages = min_messages
        self.keep_recent = keep_recent

    def should_compress(self, messages: list) -> bool:
        """Dual condition: both must fire — avoids compressing huge-but-short
        or tiny-but-long histories that single-dimension triggers mishandle."""
        return (
            len(messages) > self.min_messages
            and count_tokens_approx(messages) > self.max_tokens
        )

    def maybe_compress(self, messages: list) -> list:
        """Full production pattern. suppress_follow_up_questions uses explicit list
        ('do not acknowledge', 'do not recap') — generic 'continue normally' is ignored."""
        if not self.should_compress(messages):
            return messages

        old = messages[:-self.keep_recent]
        recent = messages[-self.keep_recent:]
        prompt = _build_compaction_prompt(old)

        response = self.client.messages.create(  # no tools=: belt-and-suspenders with NO_TOOLS_PREAMBLE
            model=self.model, max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text

        match = re.search(r'<summary>(.*?)</summary>', raw, re.DOTALL)
        summary_text = match.group(1).strip() if match else strip_analysis_tags(raw)

        suppress_follow_up_questions = (
            "Previous conversation was compressed. Summary above. "
            "Recent messages are preserved verbatim below. "
            "Resume directly — do not acknowledge the summary, "
            "do not recap what was happening, "
            "and do not preface with continuation text."
        )
        compressed = [
            {"role": "user", "content": f"<summary>\n{summary_text}\n</summary>\n\n{suppress_follow_up_questions}"},
            {"role": "assistant", "content": "Understood. Continuing from where we left off."},
        ] + recent

        print(f"  [compress-v3] {len(old)} messages → NO_TOOLS_PREAMBLE + structured summary ({len(summary_text)} chars)")
        return compressed
