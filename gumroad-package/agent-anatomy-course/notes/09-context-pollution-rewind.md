# Context Pollution & Correction-Aware Rewind

Status: Feature proposal. Not implemented in CC or any framework as of 2026-04.

---

## The Problem

```
Turn 1: User asks X
Turn 2: Model responds A (wrong understanding)
Turn 3: User corrects: "No, I meant Y"
Turn 4: Model input = [X, A, "No I meant Y", ...]
```

A is wrong but stays in context. Three degradation mechanisms compound this:
- **Softmax dilution:** A consumes attention budget even though it's wrong
- **Lost in the middle:** If A lands in the middle of context, it still influences reasoning
- **Self-reinforcement:** Model sees its own wrong reasoning and may reinforce it — the correction has to "fight against" A

The correction "No, I meant Y" doesn't erase A. It adds competing signal. The model must simultaneously hold "A was wrong" and "Y is right" — this is strictly harder than just having Y.

## What CC Has (Adjacent Mechanisms)

| Mechanism | Scope | Does it solve this? |
|-----------|-------|-------------------|
| `compact.ts` — full compaction | All old messages → summary | No — summarizes A along with everything else |
| `autoCompact.ts` — threshold trigger | Auto at 95% capacity | No — same as above |
| `microCompact.ts` — surgical | Specific tool results (file reads, grep) | **Closest** — selectively compresses specific entries |
| `rewind_files` — SDK control | File state → checkpoint | File state only, not conversation |
| Tool Result Clearing | Lightest compaction | Tool results only |

microCompact's `collectCompactableToolIds()` already marks specific conversation entries for selective compression. The pattern exists. It just targets tool results, not wrong model outputs.

## Proposed: Correction-Aware microCompact

```
User says "不对" / "no" / "wrong" / "I meant..."
  → Correction classifier detects correction pattern
    (Reuse auto-mode's two-stage classifier: Stage 1 single-token, Stage 2 CoT)
  → Mark previous assistant message as compactable
  → Trigger microCompact:
    Replace [wrong A] + [correction B]
    with [correction note: "User clarified: Y, not X"]
  → Context is clean. Attention freed. No self-reinforcement.
```

### Why compress, not delete:

| Approach | Pro | Con |
|----------|-----|-----|
| Delete A entirely | Cleanest context | Loses "what was wrong" — model may repeat the mistake |
| Keep A + B | Model learns from mistake | A pollutes attention, may reinforce error |
| **Compress A+B → correction note** | Preserves learning signal + frees attention | Needs correction boundary detection |

### Implementation as CC hook:

```python
# PreToolUse hook on user message
def on_user_message(hook_input):
    if correction_classifier(hook_input.content):
        return {
            "hookSpecificOutput": {
                "compactPreviousAssistant": True,
                "correctionSummary": extract_correction(
                    wrong=hook_input.previous_assistant_message,
                    correction=hook_input.content
                )
            }
        }
```

This could ship as a PostToolUse hook that fires after the user message is processed, compacting the previous wrong exchange before the model generates the next response.

## Relation to Handoff

The same pattern applies to inter-session handoff. If a session produced wrong outputs that were later corrected, the handoff should:
1. NOT preserve the wrong output in the brief
2. Preserve the CORRECTION (what was wrong and why)
3. This is what our "Corrections" table already does — but manually

Correction-aware microCompact automates what our Corrections table does manually.

## Prior Art

- ChatGPT message editing: forks conversation at edit point (user-initiated, not automatic)
- LangChain memory: has `clear()` but not selective correction
- MemGPT: has memory editing but at the long-term store level, not in-context

**No existing system does automatic correction-aware context rewind.** This is novel.

## Prototype Spec (for nano-agent-anatomy)

```python
# context_v4.py — adds correction-aware microcompact

def detect_correction(user_message: str) -> bool:
    """Detect if user is correcting previous model output."""
    correction_patterns = ["不对", "no,", "wrong", "I meant", "actually", "不是这样"]
    return any(p in user_message.lower() for p in correction_patterns)

def correction_microcompact(messages: list, correction_msg: str) -> list:
    """Replace wrong assistant msg + correction with a correction note."""
    # Find last assistant message
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["role"] == "assistant":
            wrong_content = messages[i]["content"][:200]  # truncate
            # Replace wrong msg + correction with note
            messages[i] = {
                "role": "user",
                "content": f"[Correction: Previous response was wrong. "
                           f"User clarified: {correction_msg}. "
                           f"Wrong response (truncated): {wrong_content}...]"
            }
            # Remove the correction message (now absorbed)
            break
    return messages
```

## Curriculum Position

This belongs in:
- **Unit 3** (Context Compression) — as context_v4.py progression
- **Blog** — "The Context Pollution Problem Nobody Talks About"
- **Unit 6** (Integration) — connects to reliability triad (context degradation + intent-execution gap)

---

## Implementation Notes (context_v4.py — 2026-04)

**File:** `context_v4.py` — 128 lines, no deps beyond `anthropic`.

**What was built:** Three functions + a chat wrapper that demonstrates the full
correction-aware microCompact loop.

### Key design decisions made during implementation

**Correction note injected as `user` role, not `assistant`.**
An assistant-role note looks self-generated — the model can implicitly
rationalize it away. A user-role note is ground truth from outside. This
distinction matters for self-reinforcement suppression.

**The wrong turn is replaced in-place at `idx`, not appended.**
Appending a correction note while keeping the wrong message would preserve
both — defeating the purpose. Slice replacement (`messages[:idx] + [note] +
messages[idx+1:]`) removes the wrong entry entirely, net -1 message.

**The correction user message is still appended after compaction.**
The note absorbs the error context. The original correction text is still
added as a normal user turn so the model sees the explicit user intent, not
just the note. This creates a clean [note → correction → response] triplet.

**Pattern matching as Stage 1 classifier.**
CC's auto-mode uses two-stage LLM classification. For this teaching prototype,
a string match over `CORRECTION_SIGNALS` implements Stage 1 cheaply. Stage 2
(CoT pass for ambiguous cases like "actually that's interesting") is omitted
but is where production would invest next.

### Demo output (2026-04-02)

```
USER: What is the capital of Australia?
ASST: The capital of Australia is Canberra.
USER: No, I meant the administrative capital — the seat of government.
  [microcompact-v4] correction detected → wrong turn compacted into note
ASST: The administrative capital and seat of government of Australia is Canberra...
```

Context message [3] after compaction:
```
[Correction note — previous assistant response was wrong and compacted]
Wrong response (excerpt): The capital of Australia is **Canberra**...
User clarified: No, I meant the administrative capital — the seat of government.
Proceed from the clarification. Ignore the wrong response.
```

Net effect: two messages (wrong assistant + correction) collapsed to one note.
Attention freed from the wrong response. Error signal preserved in note form.
