# The Context Pollution Problem Nobody Talks About

Here is something that bothered me for weeks before I could name it. You're in a long conversation with a model. It misunderstands you on turn 2. You correct it on turn 3. The model acknowledges the correction. And then, subtly, it keeps being wrong — in the same direction as the original mistake.

This is not hallucination. The model isn't fabricating. It understood your correction. The problem is structural: the wrong output from turn 2 is still sitting in the context window, competing for attention against your correction. You didn't fix the context. You added to it.

## Why This Matters

Every production agent framework I've read through has some version of context compression. They all handle the obvious case: context windows fill up, you need to summarize or prune. But compression is triggered by *volume*, not by *correctness*. The assumption is that all old context is equally worth compressing. It isn't.

When a model generates a wrong response and the user corrects it, the wrong response doesn't get labeled as wrong. It just sits there. The correction sits next to it. Now the model, on every subsequent turn, must simultaneously process "A is wrong" and "Y is right" as competing signals. That's strictly harder than just having Y.

I found three mechanisms that make this worse as the conversation continues.

**Softmax dilution.** Attention is a finite budget. Tokens in the wrong response consume that budget whether or not those tokens are useful. A 300-token wrong analysis dilutes the signal from the 30-token correction that followed it.

**Lost in the middle.** There's well-documented evidence that transformer models weight beginning and end context more heavily than middle context. As the conversation grows, the wrong response from turn 2 migrates toward the middle of the window — exactly where it has the most damaging effect.

**Self-reinforcement.** This one is the most counterintuitive. In my experience, when a model sees its own prior output, it tends to treat it as evidence. Even a corrected wrong answer can anchor subsequent reasoning toward its original framing. The correction has to fight against the model's own prior work.

None of these effects are catastrophic in isolation. Together, over a multi-turn session, they produce the gradual degradation I kept noticing: models that started confident and precise, then drifted inconsistent by turn 15.

## What Exists Today

I spent time reading through Claude Code's context management source. It has three compaction layers that together handle most of the volume problem.

`compact.ts` handles full compaction: when context gets heavy, summarize all old messages into a brief. `autoCompact.ts` fires this automatically at 95% capacity. Both are blunt instruments — they compress everything, wrong and right alike.

The interesting one is `microCompact.ts`. It does *surgical* compression: instead of summarizing everything, it identifies specific tool results — file reads, grep outputs, bash returns — and compresses those selectively. The function `collectCompactableToolIds()` marks individual conversation entries for compression without touching the rest of the context. The implementation is precise. It already knows how to target specific entries.

The pattern exists. It's just aimed at the wrong target.

Tool results are compressed because they're large and their content is now represented elsewhere (in the code that processed them, or in the model's reasoning). Wrong model outputs should be compressed for a different but structurally identical reason: their content is now superseded by a correction.

Nobody has built this. ChatGPT has message editing — you can manually fork the conversation at any point, which is the right intuition. But it's user-initiated and it deletes the wrong branch entirely. LangChain has `memory.clear()` but nothing selective. MemGPT has memory editing but at the long-term store level, not the in-context message array. No system does *automatic* correction-aware compression.

## The Proposed Fix

The idea is to extend microCompact with a correction detector. When the user sends a message that looks like a correction, instead of appending it to the existing context, trigger a compression step first.

The correction classifier already exists in CC's auto-mode: a two-stage classifier (fast single-token check, then CoT reasoning) that decides whether compaction is appropriate. The same architecture applies here. Stage 1: does this message contain correction signals? Stage 2: what exactly was wrong, and what is the clarification?

If correction detected, replace the pair — `[wrong response A] + [correction message B]` — with a single correction note:

```
[Correction: Previous response was wrong about X. User clarified: Y.]
```

Then proceed with the model's next generation reading only clean context.

Here's the prototype I wrote while working through this, built as a hook that could attach to any message loop:

```python
# context_v4.py — correction-aware microcompact

def detect_correction(user_message: str) -> bool:
    """Detect if user is correcting previous model output."""
    correction_patterns = ["no,", "wrong", "I meant", "actually", "not quite"]
    return any(p in user_message.lower() for p in correction_patterns)

def correction_microcompact(messages: list, correction_msg: str) -> list:
    """Replace wrong assistant msg + correction with a correction note."""
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["role"] == "assistant":
            wrong_content = messages[i]["content"][:200]  # truncate
            messages[i] = {
                "role": "user",
                "content": (
                    f"[Correction: Previous response was wrong. "
                    f"User clarified: {correction_msg}. "
                    f"Wrong response (truncated): {wrong_content}...]"
                )
            }
            break
    return messages
```

This is rough. The correction pattern list needs to handle negation and sarcasm. The truncation at 200 characters is arbitrary. But the structure is right: detect, locate, compress, proceed.

## Why Compress, Not Delete

The obvious objection: why not just delete the wrong response entirely? It's wrong. Get rid of it.

The problem with deletion is that it throws away the learning signal. If the model made a mistake about the structure of your codebase, and you corrected it, the *fact that it was wrong about that* is useful information. The correction note captures it: "model assumed X, user clarified Y." Deletion leaves the model without that anchor.

The compression note is doing something subtler than either keeping or deleting. It converts a competing signal into a directional one. Instead of `[wrong analysis] [correction]` — two things pointing in different directions — you get `[correction note]` — one thing pointing in the right direction, with the wrong reasoning summarized and labeled as such.

It's the difference between striking out a wrong sentence and writing a footnote that says "the above was incorrect because..."

The same logic applies to inter-session handoffs. If a session produced wrong outputs that were corrected, a good handoff note should not preserve the wrong output. It should preserve the correction. This is what I do manually in my session notes — a "Corrections" table that logs what was wrong and what replaced it. Correction-aware microCompact is just automating what I already do by hand.

## The Gap Is Real

I find it genuinely surprising that this doesn't exist yet. Context management is not a new problem. The mechanics of softmax attention are well understood. The lost-in-the-middle effect has a paper behind it. And yet every framework treats all context as equally worth compressing and none of it as specifically wrong.

The closest analogy I can find is version control. Git doesn't delete old commits when you make a fix — it preserves the history. But it also doesn't make you re-read every wrong commit every time you run `git log`. Old commits are still accessible; they're just not in your working tree. Correction-aware compression is trying to do something similar for conversational context.

The gap is narrow but real: every framework has a way to clean up large context, and one has a way to manually fork conversations, but none has a way to automatically compact the specific entries that are wrong.

---

Wrong output that survives correction doesn't just waste attention budget — it actively competes with the correction that was supposed to fix it, and no framework I've found does anything about that automatically.
