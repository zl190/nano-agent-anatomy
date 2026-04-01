# Layer 2: Persistent Memory + autoDream

## Status: Draft (partially validated)

Cross-validation: CC TS source, claw-code, Anthropic Eng Blog ("Effective Context Engineering"), Agent SDK, Berkeley MOOC F24 L2 (Shunyu Yao)

## What we know

From the leak analysis:

- MEMORY.md is a lightweight index (~150 char/line), always loaded into context
- Individual memory files hold full content, loaded on demand
- autoDream runs during idle time with 4 phases:
  1. **Orient** — read everything in memory
  2. **Gather** — collect all entries across sessions
  3. **Consolidate** — merge duplicates, resolve contradictions, sharpen vague → concrete
  4. **Prune** — remove stale entries (no recent references)
- Triggers: ≥24h since last dream AND ≥5 sessions
- Output limit: <25KB
- Dream phases execute as read-only bash operations

## Key insight

Memory is NOT append-only. Without consolidation, it fills with contradictions and noise.
This is the same problem as database compaction — you need a background GC process.

## What we need to study

- [ ] What's the exact trigger logic for autoDream?
- [ ] How does it detect contradictions between entries?
- [ ] What's the index format? (We use markdown, is that what production uses?)
- [ ] How does MEMORY_SHAPE_TEL telemetry work?
- [ ] What's EXTRACT_MEMORIES flag do differently from our inline extraction?

## MOOC cross-validation (F24 L2 — Shunyu Yao, OpenAI)

Slides: http://llmagents-learning.org/slides/llm_agent_history.pdf (slides 35-45)

**Short-term / long-term memory split (slides 37, 44-45):**
- Short-term = context window: append-only, limited, does NOT persist across sessions
- Long-term = external storage: read/write, DOES persist
- Controller mediating between them = "code-based controller"

**Cross-validation with CC:**
- Short-term = `mutable_messages` (compacted at ~95% capacity)
- Long-term = `TranscriptStore` (never truncated) + memory files on disk (MEMORY.md index + individual files)
- "Code-based controller" = `conversation.rs` runtime managing the boundary between them

**CoALA framework (slide 45):** Memory + Action Space + Decision Making. CC maps: Memory (short+long) → Action Space (tool registry) → Decision Making (LLM call).

**Retrieval scoring from Generative Agents (slides 41-43):**
score = recency × importance × relevance
CC's 256-token side call for relevance (noted in the gap table below) is a partial implementation of this formula — it scores relevance but not recency or importance separately.

**Reflexion (slides 38-39):** GPT-4 + Reflexion = 91% HumanEval pass@1 vs 67% zero-shot. "Verbal RL" — text feedback updates long-term memory. CC's autoDream consolidation phase is structurally similar: feedback from sessions gets written back to persistent memory (not reinforcement learning, but same feedback loop in spirit).

**Note on lecture numbering:** Early drafts referenced "L6: Training Agentic Models (Weizhu Chen, Microsoft)" — this speaker/topic is not found in any Berkeley LLM Agents course iteration (F24, S25, F25). The correct cross-validation source is F24 L2 (Shunyu Yao).

## Anthropic Eng Blog cross-validation

Source: "Effective Context Engineering for AI Agents" (Sep 2025)
URL: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

**Official terminology (confirmed):**
- "Structured Note-Taking" = Anthropic's term for agentic memory pattern (our autoDream → official name: memory consolidation / structured note-taking)
- Sub-agents return condensed summaries of 1,000-2,000 tokens to coordinator — this caps what enters `agentMemorySnapshot`
- "Just-in-time tool loading" = maintain lightweight identifiers, load full content dynamically. Maps to CC's 256-token side call for relevance

**autoDream gate sequence (from community reverse engineering, high confidence):**
- Triggers: ≥24 hours since last dream AND ≥5 sessions
- Internal name: "autoDream" from minified JS bundle. Official Anthropic term: "memory consolidation"
- Gate prevents over-consolidation on short sessions

## Code progression files

- `memory_v0.py` — append-only list (the tutorial version)
- `memory_v1.py` — add MEMORY.md index + per-file storage (claw-code pattern)
- `memory_v2.py` — add autoDream consolidation: Orient→Gather→Consolidate→Prune
- `memory.py` — latest integrated version

## What Production Does That We Don't

| Production feature | Why it matters | Why we skip it |
|---|---|---|
| Semantic search over memory entries | Finds relevant memories without loading all | Would need embedding model + vector store |
| Team memory paths (shared across agents) | Coordinator and workers share persistent context | Single-agent scope is sufficient for learning |
| Content-hash deduplication | Prevents exact duplicates without LLM call | Our LLM consolidation handles this |
| MEMORY_SHAPE_TEL telemetry | Tracks memory growth, consolidation frequency | Observability is a production concern |
| EXTRACT_MEMORIES feature flag | Gradual rollout of memory extraction | Feature flags add code complexity |
| 256-token side call for relevance | Only loads memories relevant to current task | We load all memories (small enough) |
| Session DAG with parentUuid chain | Memory traces back to which session created it | Adds graph complexity without teaching memory concepts |

## Open questions

- Is 50 lines enough for the index? Production uses ~150 char/line with 200 line max = 30KB
- How often should consolidation run for a single-user agent vs multi-user?
