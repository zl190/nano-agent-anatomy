# From Theory to Production: What 513K Lines Taught Me About Context Degradation

I spent three weeks writing blog posts about why LLM context degrades. Three mechanisms, empirical thresholds, the practical heuristic of planning for 200K effective tokens instead of 1M. I was confident in the theory.

Then I read 513,000 lines of production agent source code. Anthropic builds every engineering response to the exact degradation mechanism I'd described. One-to-one mapping. I didn't predict what they'd build — I described the disease, and they had already built the treatment.

---

## Why This Matters

Context degradation isn't a niche problem. It's why your agent stops following instructions after 45 minutes. It's why the YAML it confidently generated at turn 3 becomes malformed by turn 30. It's why "1M context window" in the marketing copy doesn't translate to "1M tokens of reliable reasoning" in production.

If you're building long-running agents and you've hit these symptoms, the usual responses are: blame the model, add more instructions, cap session length. All treating the symptom. The question is whether the underlying mechanisms tell you something more precise to do.

---

## Part 1: The Theory (What We Knew Before)

### Three mechanisms, all absolute-token-dependent

The research on long-context performance coalesces around three distinct failure modes. I'm going to be direct about what each one actually says, because the vague version ("models struggle with long contexts") is useless for engineering decisions.

**Mechanism 1: Softmax dilution.** When you compute attention over n tokens, the softmax denominator grows with n. Nakanishi (2025) formalizes this: attention entropy scales as Θ(log n), meaning each token's share of attention decreases as absolute context grows. Double the context, and each token gets less. This is a structural property of the attention mechanism, not a quality issue with any particular model.

**Mechanism 2: Lost in the middle.** Liu (2023) documented the U-curve: models recall information at the beginning and end of context better than the middle. Laban (2025) quantified it in multi-turn settings — 39% performance drop for relevant information buried in middle turns. The implication is that it's not just about *how much* is in context. *Where* it sits matters too.

**Mechanism 3: Position OOD.** Rotary position encodings (RoPE) are trained on sequences up to some maximum length. Du (2025) shows that beyond the training range, position encodings are extrapolated rather than learned — the model is operating outside its training distribution. Even if a model's context window is technically 1M tokens, the effective reliable range is bounded by the training distribution of position encodings.

### The 30-50K threshold

These three mechanisms converge on an empirical observation: at roughly 30-50K absolute tokens, complex reasoning measurably degrades. Not at 1M. Not at 200K. At 30-50K.

I want to be precise here: this is *absolute* token count, not relative to window size. A model with a 1M context window still degrades at 30-50K tokens because softmax dilution is a function of absolute n, lost-in-the-middle is a function of absolute position, and position OOD is a function of absolute position relative to training range. Window size sets the ceiling; these mechanisms set a much earlier floor.

My practical heuristic: plan for 200K effective tokens, not 1M. Accept that the last 800K of your context window is there for emergencies, not reliable reasoning.

### The gap I couldn't close

Theory explains *why* degradation happens. What it doesn't explain is what to *do* about it in a production system. I had vague answers: summarize periodically, prioritize recent content, keep system prompts short. None of it was grounded in anything except intuition.

That's where reading the source code changed things.

---

## Part 2: The Engineering (What Claude Code Actually Does)

### The first surprise: compaction uses an LLM

I'd read a Rust port of Claude Code's compaction logic (claw-code). It's deterministic — pure extraction of stats, recent requests, key files, pending work. No model calls. Simple, transparent, fast.

I assumed production worked the same way.

It doesn't. The TypeScript production source uses an LLM to generate the compaction summary. There's a full 9-section prompt, a `<analysis>` scratchpad for chain-of-thought, post-processing that strips the analysis before the summary reaches context, and a physical guard against the compactor itself calling tools.

The reason is worth sitting with: summary quality matters more than the cost of one additional LLM call. Deterministic extraction can identify *that* you discussed a file. An LLM can understand *why* that file matters in context of the task. These are not the same thing.

### The 9-section structure

The compaction prompt produces a structured summary with exactly these sections:

1. Primary Request and Intent
2. Key Technical Concepts
3. Files and Code Sections (with full code snippets)
4. Errors and Fixes
5. Problem Solving
6. **All User Messages** (every non-tool-result user message, verbatim)
7. Pending Tasks
8. Current Work (most recent activity, verbatim quotes)
9. Optional Next Step (must directly align with most recent request)

Section 6 is the one I didn't anticipate. It preserves *every user message*, not a summary of user intent. The explicit instruction in the prompt is to include them all. This isn't about compression — it's about retention of the actual conversational record.

### Preventing the compactor from degrading

Here's the part that made me stop and reread it twice.

The compaction system itself runs an LLM. That LLM is operating on a long context (the conversation being compacted). Which means it faces the same degradation risks as any other long-context call. Anthropic's solution is physical enforcement:

```
CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.
Tool calls will be REJECTED and will waste your only turn.
```

And then: `maxTurns: 1`.

This isn't just a prompt instruction. It's a code constraint. The compactor gets one turn, and if it spends that turn calling a tool, the turn is gone. The compactor fails. The model is told this explicitly — "you will fail the task" — making compliance the rational strategy rather than just a request.

Why does this exist? Because Sonnet 4.6 was calling tools 2.79% of the time with a weaker instruction (from CC TS source: `src/services/compact/index.ts`, comment on prior tool-call rate). That's one in thirty-six compaction calls where the model goes off-script. At production scale, that's not acceptable. The solution isn't a better prompt — it's code that makes non-compliance physically self-defeating.

### The dual trigger

Compaction fires when: `message_count > N AND tokens >= budget`.

Both conditions. Not either. This matters because:

- A short conversation with many tool-call round-trips (high message count, low tokens) shouldn't trigger compaction — there's nothing to compress
- A large system prompt with a two-message conversation (high tokens, low message count) shouldn't trigger compaction — the cost is in the static prompt, not the conversation

The AND condition means compaction fires when there's actually a long conversation worth compacting. This seems obvious in retrospect. I hadn't thought through the failure modes of a single-condition trigger.

### SYSTEM_PROMPT_DYNAMIC_BOUNDARY

This is the mechanism I found most architecturally interesting. The system prompt is split into two parts:

- **Static portion**: tool descriptions, base instructions — content that never changes mid-session
- **Dynamic portion**: CLAUDE.md content, MCP server list, agent definitions — content that varies

The boundary isn't cosmetic. Cached tokens require the prefix to be identical. If tool descriptions change, the entire cache busts, and you pay full price to re-process everything. By keeping tool schemas in the static portion and volatile configuration in the dynamic portion, only the dynamic changes cause cache misses.

The 10.2% fleet savings from moving the agent list to an attachment message rather than embedding it in tool descriptions (from CC TS source: `src/services/prompt/` cache hit metrics) shows how much this matters at scale. The agent list was in tool descriptions — so every session that had a different set of available agents caused the tool schema to change, which busted the cache. Move the agent list out, and the tool schema stays static, and the cache holds.

---

## Part 3: The Bridge

The theory and the engineering don't just coexist — they map to each other precisely.

| Degradation mechanism | Engineering response |
|---|---|
| Softmax dilution (attention per token decreases) | SYSTEM_PROMPT_DYNAMIC_BOUNDARY keeps critical content at the start, where it gets disproportionate attention |
| Lost in the middle (U-curve, 39% drop) | 9-section summary preserves ALL user messages, not a compressed abstraction |
| Position OOD (encodings extrapolated past training range) | Compaction resets absolute position — after compaction, you're back at position 0 |
| 30-50K absolute token threshold | Dual trigger calibrated to fire in this range, before degradation becomes severe |

Each design decision is an engineering response to a specific mechanism. The connections aren't obvious until you hold the theory and the code side by side.

SYSTEM_PROMPT_DYNAMIC_BOUNDARY is billed as a caching optimization, but the deeper purpose is attention management. Softmax dilution means that as context grows, the attention weight on any given token shrinks proportionally. The practical implication: put what matters most at the start of context, because the start gets disproportionate weight relative to the middle. Partitioning the system prompt into static (first, cached, always at position 0) and dynamic (appended after) keeps tool instructions and base behavior at the front — where attention is densest — regardless of how long the conversation grows.

Compaction isn't primarily cost reduction either. It's a position reset. After 40K tokens, you're approaching the range where position encodings extrapolate past the training distribution. Compaction replaces all those tokens with a fresh summary at position 0, and the conversation resumes from 0. You don't fix OOD position encodings; you prevent them by never getting there.

The 9-section structure is the clearest example. Lost-in-the-middle isn't fixed by summarizing better — it's fixed by ensuring that all user messages appear in the summary so the reconstructed context has the same U-curve properties as the original. You can't compress the user's intent into a paragraph and expect the model to reason about it with the same fidelity. So they don't compress it. They keep it verbatim. Section 6 ("All User Messages") exists because of Liu (2023), whether or not the engineers had the paper in mind when they wrote it.

---

## Part 4: What I Got Wrong

My original heuristic was "plan for 200K effective tokens, not 1M." I still think the number is approximately right. But the framing was wrong.

I treated this as a static property — here's your effective window size, don't go over it. What the production engineering shows is that degradation is a *dynamic* problem that requires a *dynamic* response. You don't just cap your context length. You actively manage it: trigger compaction before degradation, preserve high-value content in structured form, use position in context as a design variable (not just a side effect), and enforce compaction quality at the code level.

The threshold isn't a limit to stay under. It's a trigger to act before crossing.

I also didn't consider that the compactor itself could degrade. I thought about context degradation as a problem for the main agent. The production code treats the compaction call with the same seriousness — it's operating on a long context, it can fail, so it gets physical enforcement. The 2.79% tool-call failure rate shows this isn't hypothetical.

---

## The Meta-Insight

Reading production source code after building a theory of the same system is an unusual situation. I don't know if I'll get it again.

What I found: the theory predicted the engineering. Not in every implementation detail, but structurally. Three degradation mechanisms mapped to three engineering responses. The empirical 30-50K threshold appeared as a calibration parameter in the dual trigger. The U-curve from Liu (2023) appeared as an architectural decision about verbatim message retention. Position OOD appeared as the primary justification for compaction's existence — not cost, but position reset.

The cross-validation works in both directions. The theory is more credible because engineers shipping at production scale responded to exactly the mechanisms the theory identifies. The engineering is more legible because the theory gives you a vocabulary for *why* each decision exists — SYSTEM_PROMPT_DYNAMIC_BOUNDARY reads differently when you know about softmax dilution.

For everyone building long-context agents: the research I drew on includes Nakanishi (2025) on softmax entropy scaling, Liu (2023) on the lost-in-the-middle U-curve, Laban (2025) on multi-turn degradation, and Du (2025) on position OOD. These are from my earlier literature review and were not re-verified for this post — but they give you the diagnostic language for why your agent degrades, and that language turns opaque architectural decisions into obvious ones.

The disease was already described. The treatment was already built. They match.

---

*The takeaway: context degradation has three mechanisms, each with a specific engineering response — and the compaction code confirms all three.*
