# Launch Posts

## Hacker News — Show HN

**Title:**
Show HN: I read 513K lines of Claude Code's leaked source and rebuilt each layer in 150 lines of Python

**URL:**
https://github.com/zl190/nano-agent-anatomy

**Note:** Do NOT mention the paid product. Let HN discover the Gumroad link via the repo README.

---

## Reddit r/ClaudeAI

**Title:**
I cross-validated Claude Code's leaked source against 4 other sources. Here are the 4 things that don't match.

**Body:**

The CC source leaked on March 31. I've been reading through it alongside claw-code (the Rust clean-room port), Anthropic's official docs, the Agent SDK, and Berkeley's CS294 Agentic AI course (45 lectures across 3 semesters).

The interesting part isn't what the source says. It's where the sources disagree.

**1. Context compression: deterministic vs LLM**

claw-code (Rust port) does compaction with zero LLM calls — pure extraction of stats, recent requests, key files, pending work. 485 lines of deterministic logic.

CC's TypeScript does compaction with a full LLM call using a 9-section structured prompt plus an `<analysis>` scratchpad that gets stripped before reaching context.

Same feature, completely different architecture. Neither is documented.

**2. Agent spawning: dataclass vs "never delegate understanding"**

The Agent SDK exposes agent spawning as an `AgentDefinition` dataclass — define tools, model, system prompt, done.

CC's actual implementation has a natural-language coordinator prompt that says "Never delegate understanding" and uses a fork-vs-fresh cache strategy for subagents. The coordinator is a prompt, not code.

**3. Permissions: 3-tier auto vs fail-secure**

Anthropic's docs teach a 3-tier auto-mode permission system.

CC source has fail-secure defaults (unknown tool = highest permission required) and returns deny reasons as `is_error=True` tool results back to the model — so the model perceives the rejection and can recover. Tutorials just skip the tool.

**4. Memory: a flag vs 2-layer architecture**

The Agent SDK exposes memory as a boolean flag.

CC source has a 2-layer system: persistent files (cross-session, `memdir/`) + runtime summary (within-session). Plus `autoDream` — a background consolidation process that fires after 24h + 5 sessions, running orient-gather-consolidate-prune. Plus semantic search via a 256-token Sonnet side call for relevance filtering.

---

I rebuilt each layer in ~150 lines of Python and wrote detailed notes with full file:line citations. 76 tests pass.

Repo: https://github.com/zl190/nano-agent-anatomy

There's also a full sample note and blind experiment report in the `preview/` directory if you want to see the analysis methodology before diving into the code.

---

## Reddit r/MachineLearning

**Title:**
[D] Berkeley's CS294 Agentic AI (45 lectures, 3 semesters) has zero coverage of context compression. The leaked CC source shows it's the most complex layer.

**Body:**

I audited all three iterations of Berkeley's LLM Agents curriculum — CS294 Fall 2024 (12 lectures), CS294/194-280 Spring 2025 (12 lectures), CS294 "Agentic AI" Fall 2025 (21 lectures). Total: 45 lectures.

Context compression — the mechanism that decides what stays in an agent's context window and what gets summarized or dropped — is not covered in any of them.

This is notable because the leaked Claude Code source reveals it's arguably the most architecturally complex layer. CC has three compaction subsystems (`compact.ts`, `autoCompact.ts`, `microCompact.ts`), a dual trigger mechanism (message count AND token budget), and selective tool result clearing.

The curriculum gap is genuine: 4 out of 5 agent layers have strong MOOC coverage. Context compression has none.

Full audit with slides references and source citations: https://github.com/zl190/nano-agent-anatomy

---

## Twitter/X Thread

**Tweet 1 (hook):**
Claude Code's source leaked 3 days ago. I've been reading all 513K lines.

The 4 biggest surprises (thread):

**Tweet 2:**
1/ Context compression in production is NOT deterministic.

The Rust port uses zero LLM calls — pure extraction. CC's TypeScript uses a full LLM call with a 9-section prompt + hidden scratchpad.

Same feature. Completely different architecture. Neither documented.

**Tweet 3:**
2/ The multi-agent coordinator is a prompt, not code.

SDK gives you an AgentDefinition dataclass. CC's actual implementation is a natural-language prompt that says "Never delegate understanding."

The coordinator manages other AIs by talking to them, not by calling APIs.

**Tweet 4:**
3/ Permission denials don't throw errors — they continue the loop.

CC returns deny reasons as is_error=True tool results. The model sees the rejection and can recover: "I can't run rm -rf, let me try a safer approach."

Tutorials just skip the tool. Production gives the model a second chance.

**Tweet 5:**
4/ Memory isn't a growing list. It has a garbage collector.

autoDream fires after 24h + 5 sessions: orient → gather → consolidate → prune.

Plus a 256-token Sonnet side call for relevance filtering. The "memory" flag in the SDK hides a 2-layer architecture.

**Tweet 6:**
I rebuilt each layer in ~150 lines of Python. 76 tests. Full cross-validation against 5 sources.

Repo: github.com/zl190/nano-agent-anatomy

Detailed notes + exercises + blind experiment in the preview/ directory.
