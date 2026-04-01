## I cross-validated Claude Code's leaked source against 4 other sources. Here are the 4 things that don't match.

The CC source leaked on March 31. I've been reading through it alongside claw-code (the Rust clean-room port), Anthropic's official docs, the Agent SDK, and Berkeley's CS294 Agentic AI course (45 lectures across 3 semesters).

The interesting part isn't what the source says. It's where the sources disagree.

**1. Context compression: deterministic vs LLM**

claw-code (Rust port) does compaction with zero LLM calls — pure extraction of stats, recent requests, key files, pending work. 584 lines of deterministic logic.

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

There's a full sample note and blind experiment report in the `preview/` directory if you want to see the analysis methodology before diving into the code.
