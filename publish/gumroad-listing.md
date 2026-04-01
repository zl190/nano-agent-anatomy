# Gumroad Listing

## Name
Agent Internals: From Leaked Source to Working Code

## Price
$19

## URL slug
agent-internals

## Description

On March 31, 2026, Anthropic accidentally shipped a source map in their npm package. 513,000 lines of Claude Code's TypeScript — exposed.

I spent the next few days reading through every layer, cross-referencing with Berkeley's CS294 Agentic AI course, claw-code (Rust port), Anthropic's official docs, and the Agent SDK.

**What's in the ZIP (20 files, ~3,300 lines of Markdown):**

- 12 study notes covering 4 agent layers: tool loop, memory, context compression, coordinator
- 5-source cross-validation audit with 64 file:line citations
- 5 exercises that force you to trace real code with concrete values
- Blind A/B experiment: structured vs free-form source reading (6-0 result)
- 9 verified claims with full evidence chains

**The 4 key discrepancies (the gold):**
1. Compaction: claw-code = deterministic; CC TypeScript = LLM with 9-section prompt
2. Agent spawning: SDK = dataclass; CC = "never delegate understanding" + cache forking
3. Permissions: docs = 3-tier auto-mode; CC = fail-secure + deny reason as is_error
4. Memory: SDK = a flag; CC = 2-layer architecture + autoDream + semantic search

Pairs with the open-source repo: github.com/zl190/nano-agent-anatomy
