# Issue #0: The Structured Approach Lost

I ran a blind experiment comparing two ways to read 513,000 lines of publicly available source code with AI agents. The structured approach — JSON schemas, validation gates, architecture personas — lost: the blind evaluator preferred free-form output for 5 of 6 readers plus the synthesis (6 picks to 1).

This wasn't supposed to happen. I'd designed SOP v2 specifically to improve on the baseline: typed extraction schemas, per-reader validation gates, confidence tags on every claim. The kind of rigor that sounds obviously better. Then I ran a baseline with plain Markdown output, no schema, no gates. Randomized both into "A" and "B," and had a fresh Opus instance evaluate them blind.

The evaluator picked the free-form output for 5 of 6 readers and the synthesis. Consistently. The structured version won on evidence quality (+1.33 on a 5-point Likert scale) and extracted 2.2x more named symbols in automated counts. But it lost on pattern depth (-1.00) and actionability (-1.17) — the dimensions that make source reading worth doing.

## What the Experiment Was

After Anthropic's Claude Code CLI source became publicly available on March 31 via an npm source map, I downloaded all 513K lines of TypeScript across 1,892 files. Too large for any single agent — Sonnet's 200K context would be 80-90% full just loading the code, leaving no room to think.

So I split it into 6 subsystems and pointed one agent at each: core runtime (`QueryEngine.ts`, `Tool.ts`, bootstrap), tools (`BashTool/`, `FileEditTool/`, `GrepTool/`), AI & MCP integration (`AgentTool/`, `services/api/`), UI & terminal (`components/`, `ink/`), state & persistence (`hooks/`, `memdir/`), and commands & skills (`commands/`, `skills/`).

I ran this twice. Once with a minimal prompt: "read these files, report line count, core classes, production insights, and how this maps to our code." Free-form Markdown output. No schema, no persona, no validation.

Then with a structured SOP: JSON output schema requiring typed symbol arrays with signatures and dependencies, data flow edges with file:line evidence, confidence-tagged pattern claims, plus an architecture persona ("you are a systems architect") and validation gates that rejected malformed output.

Same model (Sonnet). Same 6 file assignments. Same codebase. Different SOP. Each run cost about $3.

Critically, the two runs happened in physically isolated sessions. The v1 agents never saw v2's results and vice versa. Then I anonymized both sets, flipped a coin for A/B labels, and had a fresh Opus instance — with no knowledge of which was which — evaluate them on five dimensions.

## The Scores

| Dimension | Free-form | Structured | Delta |
|-----------|-----------|------------|-------|
| Extraction Completeness | 4.50 | **4.83** | +0.33 |
| Pattern Depth | **5.00** | 4.00 | -1.00 |
| Evidence Quality | 3.33 | **4.67** | +1.33 |
| Cross-Reference | 4.33 | 4.33 | 0.00 |
| Actionability | **5.00** | 3.83 | -1.17 |

The structured version turned agents into catalogers. They produced clean JSON with file:line references you could grep for. But the free-form version produced insights like "this codebase is a game engine in disguise" and "sed -i is intercepted and simulated — the approved diff is applied directly without running sed" — the kind of observations that change how you think about agent architecture.

The evaluator's summary: "A embeds surprising findings throughout 'Production insight' sections rather than in labeled 'surprise' sections." Its overall rationale for preferring v1: "the kind of output that justifies spending time reading source code."

## The Fix: Dual-Channel Output

Structure aids verification. Freedom aids insight. They're different goals. I was wrong to stuff both into one format.

SOP v3 separates them:

```
Phase 1: Extraction (JSON schema, cheap model)
  → What exists: symbols, signatures, dependencies, file:line evidence
  → Gated: must parse, must have ≥1 symbol per file

Phase 2: Interpretation (free-form Markdown, premium model)
  → What it means: patterns, surprises, "what tutorials don't teach"
  → Ungated: only check that cited file:line references exist
```

The extraction pass uses Haiku (mechanical work, don't overpay). The interpretation pass uses Sonnet or Opus (creative depth, don't underpay). Total cost increase: ~20-30% over running it once, mostly from the cheap extraction pass.

I haven't validated v3 yet. That's the next experiment.

## Why This Matters Beyond Source Reading

Every agent workflow faces this trade-off. When you constrain LLM output with schemas, you get verifiability at the cost of depth. When you leave it free-form, you get insight at the cost of rigor. Most agent frameworks pick one side — some mandate JSON schemas for every agent output, while others emit unstructured prose.

The experiment says: pick both, but in sequence, not in parallel. Extract first, interpret second. Gate the facts, free the narrative. The extraction pass is cheap mechanical work. The interpretation pass is expensive creative work. Don't force the creative pass through a schema-shaped hole.

This is the first post in a series where I'm reading through the publicly available Claude Code source alongside [Berkeley's Agentic AI course](https://rdi.berkeley.edu/agentic-ai/f25), rebuilding each layer in ~100 lines of Python, and running experiments on the methodology itself. Each issue: one production pattern dissected, one Python file rebuilt, one experiment on the process.

**Next issue:** I found that Berkeley's 45 lectures across 3 semesters have zero coverage of context compression — the thing that determines whether your agent gracefully continues or loses all state after 50 tool calls. What production builds for this, and why no one teaches it.

Code + experiment data: [github.com/zl190/nano-agent-anatomy](https://github.com/zl190/nano-agent-anatomy)
