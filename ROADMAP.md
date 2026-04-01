# Learning Roadmap V2

Complete course, ship at once. Iterate weekly with expert review.

**Design principles** (from CS336, nanoGPT, minbpe, microgpt research):
1. Simplify scale, not algorithm — preserve real production patterns
2. Verify against production reference — scenario tests per layer
3. Progressive onion layers — each step self-contained and runnable
4. Make the gap explicit — "What Production Does That We Don't"
5. Cross-validate 4 validated sources — discrepancies = insights

## Four Sources (Cross-Validation)

Every topic is read from all 4 validated sources. The value is WHERE THEY DISAGREE.

Note: Berkeley MOOC (CS294) lecture numbers appear throughout as suggested reading pointers. They are NOT cross-validated — no findings from the lectures were extracted or verified against code. Treating them as validated would be dishonest. They remain as orientation signposts.

| Source | What it teaches | Limitation | Status |
|--------|----------------|------------|--------|
| **Berkeley MOOC** (CS294) | Theory: multi-agent, planning, safety | Framework-agnostic, no production code | Suggested reading only — not validated |
| **CC TS Source** (513K lines) | Real implementation: prompts, skills, hooks | Leaked, may diverge from current shipping version | Validated |
| **claw-code** (Rust port) | Clean reimplementation with tests | Simplified — e.g., compaction is deterministic (CC TS uses LLM) | Validated |
| **Anthropic Academy + CCA** | Official teaching: how to USE Claude | Black-box — doesn't explain internals | Validated |
| **Agent SDK** (6,290 lines) | Control protocol over CC CLI binary | Wraps binary, doesn't implement agent behavior | Validated |

**Known cross-validation discrepancies (the gold):**
- Compaction: claw-code = deterministic, CC TS = LLM with 9-section prompt + `<analysis>` scratchpad
- Agent spawning: SDK = `AgentDefinition` dataclass, CC source = "Never delegate understanding" + fork-vs-fresh cache strategy
- Permissions: Academy teaches 5 modes, CC source has fail-secure (unknown → highest) + deny reason as is_error
- Memory: SDK exposes `memory` flag, CC source has 2-layer architecture + autoDream + semantic search

## Course Structure

### Unit 0: Methodology (NEW)

**What:** How to systematically read production source with AI agents.

- **Experiment:** Blind A/B comparing structured vs free-form reading (our data)
- **Result:** Structure aids verification, freedom aids insight. SOP v3: dual-channel.
- **Exercise:** Read a 5K-line repo using SOP v3. Compare your extraction vs interpretation outputs.
- **Gap:** We tested on 1 codebase. Production SOP would need benchmarking across many codebases.

### Unit 1: The Tool Loop

**Objective:** Understand the tool-use cycle well enough to draw it without notes.

| Source | What to study | Key finding |
|--------|--------------|-------------|
| MOOC | L1-L2: LLM Agents Overview (~2h) | Theory: ReAct, function calling |
| CC TS | `src/constants/prompts.ts` (system prompt) | Real prompt = hundreds of lines with feature flags |
| claw-code | `conversation.rs` (584 lines) | State machine: max_iterations=16, deny→is_error |
| Academy | "Building with the Claude API" (tool use section) | Official: `tool_use` content blocks |
| SDK | `query.py` (749 lines) | Control protocol: JSON-over-stdio to CLI binary |

**Cross-validation:**
- Academy teaches simple `tool_use` → CC source adds permission check BEFORE execution, max_iterations hard ceiling, dual stop conditions
- SDK wraps the loop as a subprocess → actual loop semantics live inside the 196MB binary

**Code progression** (onion layers):
- `loop_v0.py` — bare while loop, no safety (the tutorial version)
- `loop_v1.py` — add max_iterations + is_error for denied tools (conversation.rs)
- `loop_v2.py` — add streaming + token budget tracking (CC TS)
- `loop_v3.py` — add permission check before execution (permissions.rs)

**Scenario tests** (verify against production):
- `test_loop.py::test_denied_tool_returns_is_error` — must match conversation.rs behavior
- `test_loop.py::test_max_iterations_stops_loop` — must halt at 16
- `test_loop.py::test_budget_exceeded_stops_loop` — token budget stop condition

**Exercise:**
1. Run `loop_v0.py`. Observe: what happens if the LLM calls tools forever?
2. Add max_iterations. Predict: what happens when the LLM hits the limit?
3. Compare your loop to `conversation.rs`. List 3 things production does that you don't.

**Gap:** No retry logic, no circuit breaker, no streaming fallback (529 pattern).

### Unit 2: Memory + Consolidation

**Objective:** Understand why memory is not append-only.

| Source | What to study | Key finding |
|--------|--------------|-------------|
| MOOC | L6: Training Agentic Models (~1.5h) | Theory: episodic vs semantic memory |
| CC TS | `src/services/extractMemories/prompts.ts`, `src/services/SessionMemory/` | Memory extraction = LLM call with specific prompt |
| claw-code | `memdir/` subsystem | 2-layer: MEMORY.md index (always loaded) + per-file (on demand) |
| Academy | "Introduction to Agent Skills" | Skills as persistent learned behavior |
| SDK | `sessions.py` (1,742 lines) | Session DAG with parentUuid chain, fork_session() UUID remapping |

**Cross-validation:**
- MOOC teaches memory as "vector DB retrieval" → CC uses file-based MEMORY.md + LLM-driven relevance selection (256-token side call)
- Academy teaches Skills as config → CC source shows skills are agents in disguise (Reader 6 finding)

**Code progression:**
- `memory_v0.py` — append-only list (the tutorial version)
- `memory_v1.py` — add MEMORY.md index + per-file storage (claw-code pattern)
- `memory_v2.py` — add autoDream consolidation: Orient→Gather→Consolidate→Prune

**Scenario tests:**
- `test_memory.py::test_duplicate_entries_consolidated` — autoDream merges same-topic entries
- `test_memory.py::test_stale_entries_pruned` — entries with no references after 30 days removed
- `test_memory.py::test_index_stays_under_limit` — MEMORY.md ≤ 200 lines

**Exercise:**
1. Run memory for 10 exchanges. How big is MEMORY.md?
2. Trigger autoDream. What changed?
3. Read `extractMemories/prompts.ts`. Compare to your implementation.

**Gap:** No semantic search, no team memory paths, no content-hash dedup.

### Unit 3: Context Compression

**Objective:** Know exactly what breaks and why compression is lossy.

| Source | What to study | Key finding |
|--------|--------------|-------------|
| MOOC | L8: Predictable Noise (Sida Wang, Meta) | Theory: information loss in compression |
| CC TS | `src/services/compact/prompt.ts` | **LLM-based!** 9-section prompt + `<analysis>` scratchpad stripped |
| claw-code | `compact.rs` (485 lines) | **Deterministic!** Zero LLM calls, pure extraction |
| Academy | "Claude Code in Action" (context management) | Official: autoCompactEnabled flag |
| SDK | `PreCompact` hook | Can observe/modify before compact fires, cannot replace algorithm |

**Cross-validation (MAJOR DISCREPANCY):**
- claw-code = deterministic extraction (stats, recent requests, key files, pending work)
- CC TS = full LLM prompt with `<analysis>` scratchpad, 9 structured sections, `NO_TOOLS_PREAMBLE` enforcement
- **Why the discrepancy?** claw-code is a simplified reimplementation. CC TS is the production system. The deterministic version is the "nano" approximation of the LLM-based production version.
- **This validates our approach:** we build the deterministic version first (understand the structure), then study the LLM-based version (understand why production chose differently).

**Code progression:**
- `context_v0.py` — LLM summarization (the tutorial version: "summarize this conversation")
- `context_v1.py` — deterministic extraction (compact.rs pattern: stats + files + pending)
- `context_v2.py` — LLM-based with `<analysis>` scratchpad (CC TS pattern)
- `context_v3.py` — add `NO_TOOLS_PREAMBLE` enforcement + dual trigger

**Scenario tests:**
- `test_context.py::test_dual_trigger_requires_both_conditions`
- `test_context.py::test_summary_preserves_pending_tasks`
- `test_context.py::test_analysis_tags_stripped_from_output`

**Integration checkpoint:** Loop + Memory + Context working together. 20-turn conversation → compress → continue without losing critical context.

**Gap:** No `SYSTEM_PROMPT_DYNAMIC_BOUNDARY`, no prompt cache break detection, no partial compaction.

### Unit 4: Multi-Agent Coordination

**Objective:** Understand why orchestration is prompt-based, not code-based.

| Source | What to study | Key finding |
|--------|--------------|-------------|
| MOOC | L7+L11: Multi-Agent AI (~3h) | Theory: coordination, communication protocols |
| CC TS | `src/tools/AgentTool/prompt.ts` (full prompt) | "Brief like a smart colleague", "Never delegate understanding", fork vs fresh |
| claw-code | `AgentTool/` (21 files) | Agent-as-tool_use block, 5 built-in types, 6 task tools |
| Academy | "Introduction to Subagents" | Official: context isolation, anti-patterns |
| SDK | `AgentDefinition` dataclass | Observable surface: task lifecycle events |

**Cross-validation:**
- MOOC teaches programmatic coordination → CC uses NL system prompt ("Do not rubber-stamp weak work")
- Academy teaches subagents as isolated workers → CC source reveals bidirectional SendMessage + memory snapshots
- SDK exposes `TaskStarted/Progress/Notification` → actual orchestration logic entirely inside binary

**Code progression:**
- `coordinator_v0.py` — hardcoded task decomposition (the tutorial version)
- `coordinator_v1.py` — LLM-driven decomposition with NL system prompt (claw-code)
- `coordinator_v2.py` — add worker isolation + scratch directories
- `coordinator_v3.py` — add CC's prompt patterns: "brief like colleague" + "never delegate understanding"

**Scenario tests:**
- `test_coordinator.py::test_bad_worker_result_rejected` — "Do not rubber-stamp weak work"
- `test_coordinator.py::test_workers_isolated` — worker A cannot see worker B's messages
- `test_coordinator.py::test_decomposition_produces_2_to_4_subtasks`

**Exercise:**
1. Give coordinator a task needing 3 subtasks. Does it decompose correctly?
2. Deliberately return bad work from a worker. Does coordinator catch it?
3. Read CC's AgentTool prompt. List 3 anti-patterns they enforce that we don't.

**Gap:** No agent-as-tool_use block, no KV cache forking, no 5 built-in agent types.

### Unit 5: Production Prompt Engineering (NEW)

**Objective:** Learn prompt engineering from 44 production tool prompts.

| Source | What to study | Key finding |
|--------|--------------|-------------|
| CC TS | 44 `tools/*/prompt.ts` files | Real production prompts with anti-patterns, enforcement, examples |
| CC TS | `src/constants/prompts.ts` | System prompt architecture: static/dynamic split for cache |
| CC TS | `src/skills/bundled/skillify.ts` | Session → interview → SKILL.md conversion |
| Academy | "Building with the Claude API" (prompt engineering) | Official best practices |
| CCA | Domain 3: Prompt Engineering (20% of exam) | What Anthropic tests on |

**Key patterns from CC prompts:**
1. `NO_TOOLS_PREAMBLE` — "Tool calls will be REJECTED and will waste your only turn"
2. `<analysis>` scratchpad — internal reasoning stripped before reaching context
3. Feature-gated prompt sections — `feature('KAIROS')` conditional requires
4. Agent list as attachment (not in tool desc) — saved 10.2% cache tokens
5. Anti-patterns enforced in prompt text: "Never delegate understanding", "Don't peek", "Don't race"
6. Skillify multi-round interview — session analysis → 3 rounds of structured questions

**Cross-validation:**
- Academy teaches prompt engineering as a craft → CC source shows it as engineering (cache optimization, DCE, feature flags)
- CCA tests prompt engineering (20%) → but none of the Academy courses teach the prompt architecture from the source

**Exercise:**
1. Read 5 tool prompts. What patterns repeat? (hint: examples, anti-patterns, enforcement language)
2. Write a tool prompt for a new tool using CC's patterns. Have it reviewed.
3. Compare CC's system prompt to what Academy teaches. List discrepancies.

**Gap:** This is the most underserved topic in the entire agent education space. Zero coverage in Chinese or English markets.

### Unit 6: Integration + Security + Verification

**Objective:** All layers working together. Audit against production.

- **Full pipeline:** loop + memory + context + coordinator running together
- **Security audit:** `permissions.rs` (232 lines) + `BashTool/prompt.ts` security checks
- **Verification:** Run all scenario tests. Compare behavior to production.
- **Final exercise:** Explain the full architecture in 5 minutes. Record yourself.

**Gap documentation:** Final "What Production Does That We Don't" covering all layers.

## Delivery Plan

```
Launch Release (this week):
  - All 7 units written (notes + code + exercises + tests + gap docs)
  - Ship to GitHub + Substack (launch post = experiment story)
  - 小红书 launch post

Weekly Iteration:
  - Expert review (spawn Opus reviewer per unit)
  - Community feedback (GitHub issues)
  - New cross-validation findings
  - Exercise improvements based on learner experience
```

## Verification Targets (from nanoGPT pattern)

| Layer | Observable behavior | Must match |
|-------|-------------------|------------|
| Loop | denied_tool → is_error with reason text | conversation.rs |
| Memory | consolidation merges same-topic entries | autoDream |
| Context | deterministic summary extracts files + pending | compact.rs |
| Coordinator | workers get isolated histories | scratch directory pattern |
| Permissions | unknown tools → highest permission required | permissions.rs |

## Files Structure

```
nano-agent-anatomy/
├── loop.py, loop_v0.py, loop_v1.py, loop_v2.py, loop_v3.py
├── memory.py, memory_v0.py, memory_v1.py, memory_v2.py
├── context.py, context_v0.py, context_v1.py, context_v2.py, context_v3.py
├── coordinator.py, coordinator_v0.py ... coordinator_v3.py
├── permissions.py
├── main.py
├── tests/
│   ├── test_loop.py
│   ├── test_memory.py
│   ├── test_context.py
│   └── test_coordinator.py
├── exercises/
│   ├── unit1-loop.md
│   ├── unit2-memory.md
│   ├── unit3-context.md
│   ├── unit4-coordinator.md
│   └── unit5-prompts.md
├── notes/
│   ├── 01-tool-loop.md (+ "What Production Does" section)
│   ├── 02-memory.md
│   ├── 03-context.md (+ cross-validation: claw-code vs CC TS)
│   ├── 04-coordinator.md
│   └── 05-prompt-engineering.md (NEW)
├── experiment/ (blind A/B data)
├── publish/ (Substack + 小红书 + Gumroad)
└── ROADMAP.md (this file)
```

## Rules

- Each .py ≤ 150 lines. If longer, the concept isn't simplified enough.
- Each unit ships with: note + code progression + scenario tests + exercises + gap doc.
- Cross-validation findings go in notes with explicit source attribution.
- Blog drafts accumulate in notes/. Publish on completion of V1, not per-unit.
- No dependencies beyond `anthropic`. Zero-framework understanding.
