# Code Review: context_v4.py -- Correction-Aware microCompact

Reviewer: Independent (did not write this code)
Date: 2026-04-02
Verdict: **REVISE** -- one logic bug, one misleading comment, two minor issues

---

## 1. Correctness

### BUG: Consecutive user-role messages after compaction (lines 79-81, 90-95)

`correction_microcompact` replaces the assistant message at `idx` with a
user-role correction note. Control returns to `chat()`, which then appends the
user's correction message as another user-role entry (line 95). The preceding
message before the (now-replaced) assistant turn is also user-role.

Result after compaction in the demo:

```
[2] user: What is the capital of Australia?
[3] user: [Correction note...]          <-- was assistant, now user
[4] user: No, I meant the administrative...  <-- appended by chat()
```

Three consecutive user messages. The Anthropic API happens to accept this, so
the demo runs. But:

- The message structure violates the expected alternating-role convention.
- A reader learning from this file will think consecutive same-role messages are
  normal practice. They are not -- the API tolerates them but most production
  code enforces alternation.
- The proposal says "Two entries (wrong A + correction B) collapse to one note.
  Net: -1 message." This is incorrect: the function replaces 1 message with 1
  message (net 0). The correction message is then appended separately (+1). The
  actual net change per turn is 0, not -1.

**Fix:** The correction note should absorb the correction message. Do not
append the correction as a separate user message when compaction occurred.
Alternatively, emit the note as assistant-role with a prefixed caveat
(less desirable per the existing design rationale on line 58-59).

Recommended fix in `chat()` (lines 90-98):

```python
def chat(client: Anthropic, model: str, messages: list, user_input: str) -> tuple[list, str]:
    if detect_correction(user_input) and messages:
        messages, compacted = correction_microcompact(messages, user_input)
        if compacted:
            print("  [microcompact-v4] correction detected -> wrong turn compacted into note")
            # Note already contains the correction text. Skip separate append
            # so we don't create consecutive user messages.
        else:
            messages.append({"role": "user", "content": user_input})
    else:
        messages.append({"role": "user", "content": user_input})

    response = client.messages.create(model=model, max_tokens=512, messages=messages)
    reply = response.content[0].text
    messages.append({"role": "assistant", "content": reply})
    return messages, reply
```

With this fix, the correction note at `idx` absorbs both the wrong response and
the user clarification (it already contains `User clarified: {correction_msg}`).
No information is lost. The message count genuinely drops by 1 (wrong assistant
turn removed, note inserted in its place, no new user message appended).

### Misleading comment (line 79)

> Two entries (wrong A + correction B) collapse to one note. Net: -1 message

As written, only one entry is replaced (the assistant turn). The correction
message B has not been added yet at this point, so "two entries collapse" is
aspirational, not actual. After applying the fix above, this comment becomes
correct. Without the fix, it must be updated.

---

## 2. Teaching Quality

**Strong points:**

- The docstring (lines 1-20) is excellent. The problem statement with three
  degradation mechanisms (softmax dilution, lost-in-middle, self-reinforcement)
  is clear and well-motivated.
- The three-option table (delete / keep / compress) in the proposal is faithfully
  reflected in the code comments.
- The rationale for user-role vs assistant-role (lines 58-59) is a genuine
  insight and well-placed.
- The CORRECTION_SIGNALS list with bilingual patterns is a nice touch for the
  teaching audience.
- The `extract_text` helper handles both str and content-block forms, which is
  realistic for anyone working with the Anthropic API.

**Issues:**

- The consecutive-user-messages bug undermines teaching value. A learner who
  runs this and inspects the final context (the demo prints it) will see three
  consecutive user messages and either think it's normal or be confused about
  why the note didn't actually reduce the message count.
- Line 25 mentions "two-stage LLM classifier" but the code only implements
  Stage 1 (pattern matching). This is correctly noted -- no issue here, just
  confirming the attribution is accurate.

---

## 3. Production Mapping

| Claim in code | Accurate? |
|---|---|
| microCompact.ts + collectCompactableToolIds() selectively compress specific entries | Yes |
| Extension to wrong model outputs is novel / not in CC | Yes (as of 2026-04) |
| CC would use PreToolUse hook | Reasonable mapping |
| Two-stage classifier (single-token Stage 1, CoT Stage 2) | Yes, matches auto-mode pattern |
| microCompact caps tool result summaries to avoid re-polluting | Yes |

Production mapping is accurate. No misattributions found.

---

## 4. Code Quality

- **Line count:** 128 lines (within the 150-line budget).
- **Dependencies:** Only `anthropic`. Correct.
- **Dead code:** None.
- **Naming:** Clear and consistent. `correction_microcompact` directly maps to
  the proposal name.
- **Type hints:** Present on all function signatures. `tuple[list, bool]` return
  on `correction_microcompact` is a good addition over the proposal spec (which
  returned only `list`).

Minor style note: `extract_text` (line 41) uses a dense list comprehension with
mixed dict/object handling. For a teaching file, breaking this into an explicit
loop with comments would improve readability. Not blocking.

---

## 5. Runnable

- Syntax check: PASS
- Import check: PASS
- Unit tests (detect_correction, extract_text, correction_microcompact): PASS
- Full demo with API key: PASS (runs, produces output, no crashes)

The demo works end-to-end. The consecutive-user-messages issue does not cause
a runtime error but produces a misleading context structure.

---

## Summary of Required Changes

| # | Severity | Location | Issue | Fix |
|---|----------|----------|-------|-----|
| 1 | **Bug** | `chat()` lines 90-98 | Consecutive user messages after compaction | Skip appending user message when compaction absorbed it (see fix above) |
| 2 | **Comment** | Line 79 | "Net: -1 message" is wrong | Will become correct after fix #1; otherwise update to "Net: 0" |

## Optional Improvements (non-blocking)

| # | Location | Suggestion |
|---|----------|------------|
| A | Line 29 | `"sorry,"` triggers on user apologies that are not corrections. Consider removing or narrowing. |
| B | Lines 46-48 | `extract_text` list comprehension is dense for a teaching file. Consider an explicit loop. |
| C | Demo | The demo correction ("administrative capital") is weak because Canberra IS both the capital and administrative capital. The model's original answer may not actually be wrong. Consider a demo where the model gives a clearly wrong answer, or use a different question. |

---

Verdict: **REVISE** -- fix the consecutive-user-messages bug in `chat()`, update
the net-message-count comment. Then it passes.
