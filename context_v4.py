"""
Layer 3 v4: Correction-aware microCompact.
Novel idea — not yet in CC or any framework as of 2026-04.

Production concept: CC's microCompact.ts uses collectCompactableToolIds() to
selectively compress specific conversation entries (tool results: file reads,
greps). The pattern exists. The extension here: apply the same surgical
compaction to WRONG MODEL OUTPUTS when the user corrects them.

The problem:
  Turn 2: Model says A (wrong)
  Turn 3: User says "no, I meant Y"
  → A stays. Softmax dilution + lost-in-middle + self-reinforcement all fire.
  → Model must fight its own wrong reasoning to follow the correction.

The fix: compress [wrong A] + [correction B] into one correction note.
  Delete A entirely → model may repeat the mistake (loses error signal)
  Keep A + B       → attention pollution, self-reinforcement
  Compress → note  → preserves what-was-wrong + frees attention budget
"""

from anthropic import Anthropic

# Production would use CC's two-stage LLM classifier (single-token Stage 1 for
# speed, CoT Stage 2 for ambiguous cases). Pattern matching teaches the concept.
CORRECTION_SIGNALS = [
    "不对", "不是", "不是这样", "我是说",
    "no,", "no.", "nope", "wrong",
    "i meant", "actually,", "actually.",
    "wait,", "wait.", "sorry,",
    "that's not", "that isn't",
]


def detect_correction(user_message: str) -> bool:
    """Fast Stage-1 check: any correction signal present?"""
    msg = user_message.lower().strip()
    return any(signal in msg for signal in CORRECTION_SIGNALS)


def extract_text(content) -> str:
    """Normalise content — may be str or list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", str(b)) if isinstance(b, dict) else getattr(b, "text", str(b))
                 for b in content]
        return " ".join(parts)
    return str(content)


def correction_microcompact(messages: list, correction_msg: str) -> tuple[list, bool]:
    """Surgical compaction: [wrong assistant turn] → correction note (user role).

    Returns (new_messages, did_compact).

    Why user role for the note: must be ground truth the model accepts as
    external input. An assistant-role note looks self-generated — easier for
    the model to implicitly discount or rationalize away.
    """
    # Scan backwards — the wrong turn is always the most recent assistant message.
    idx = next((i for i in range(len(messages) - 1, -1, -1)
                if messages[i].get("role") == "assistant"), None)
    if idx is None:
        return messages, False  # no prior assistant turn; correction stands alone

    wrong_content = extract_text(messages[idx]["content"])
    # Truncate: retain error category, not the full wrong reasoning.
    # microCompact.ts similarly caps tool result summaries to avoid re-polluting.
    excerpt = wrong_content[:200].rstrip() + ("..." if len(wrong_content) > 200 else "")

    note = (
        f"[Correction note — previous assistant response was wrong and compacted]\n"
        f"Wrong response (excerpt): {excerpt}\n"
        f"User clarified: {correction_msg}\n"
        f"Proceed from the clarification. Ignore the wrong response."
    )

    # Two entries (wrong A + correction B) collapse to one note. Net: -1 message,
    # full attention freed from A, error signal preserved in a single location.
    new_messages = messages[:idx] + [{"role": "user", "content": note}] + messages[idx + 1:]
    return new_messages, True


def chat(client: Anthropic, model: str, messages: list, user_input: str) -> tuple[list, str]:
    """Single turn. Correction hook fires here — before the model sees context.

    In CC this would be a PreToolUse hook on the incoming user message.
    """
    if detect_correction(user_input) and messages:
        messages, compacted = correction_microcompact(messages, user_input)
        if compacted:
            print("  [microcompact-v4] correction detected → wrong turn compacted into note")
            # Don't append user_input — the correction note already contains it.
            # Without this skip, we'd get 3 consecutive user messages and the
            # "two entries collapse to one" claim would be a lie (net 0, not -1).
        else:
            messages.append({"role": "user", "content": user_input})
    else:
        messages.append({"role": "user", "content": user_input})
    response = client.messages.create(model=model, max_tokens=512, messages=messages)
    reply = response.content[0].text
    messages.append({"role": "assistant", "content": reply})
    return messages, reply


def demo():
    """Demonstrate: wrong answer → correction trigger → compacted context."""
    client = Anthropic()
    model = "claude-haiku-4-5-20251001"
    messages = []

    turns = [
        "What is 12 multiplied by 8?",
        "What is the capital of Australia?",
        "No, I meant the administrative capital — the seat of government.",
    ]

    print("=== context_v4.py — correction-aware microCompact demo ===\n")
    for user_input in turns:
        print(f"USER: {user_input}")
        messages, reply = chat(client, model, messages, user_input)
        print(f"ASST: {reply[:300]}")
        print(f"  [context size: {len(messages)} messages]\n")

    print(f"Final context ({len(messages)} messages):")
    for i, m in enumerate(messages):
        content = extract_text(m["content"])[:120].replace("\n", " ")
        print(f"  [{i}] {m['role'].upper()}: {content}...")


if __name__ == "__main__":
    demo()
