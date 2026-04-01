# What Production Does That We Don't — Complete Gap Analysis

Summary of all gaps between CC production (513K lines TS+Rust) and nano-agent-anatomy (~1000 lines Python).

Source: CC TS + claw-code + Anthropic Academy + Agent SDK/CCA (4-source cross-validation).
Individual unit gaps: notes/01 through notes/07.

---

## How to read this document

Every gap has four fields:
- **What production does** — the specific mechanism, with file path where known
- **What we do** — our nano implementation (or absence of one)
- **Why the gap exists** — deliberate simplification for learning, or genuine limitation
- **Learning value** — does understanding this gap teach something about production agent engineering?

Gaps are organized by category, not by unit. Most gaps span multiple units.

---

## Scale gaps

Things that only matter at fleet scale — irrelevant for a study project, but necessary for understanding why production looks the way it does.

### Fleet-level telemetry

**Production:** Every tool call, every compaction event, every token count, every cache hit ratio is tracked in real time. CC source references `MEMORY_SHAPE_TEL` (memory telemetry), cache hit metrics via `cache_creation_input_tokens` + `cache_read_input_tokens` fields (claw-code `usage.rs`), and the 2.79% tool non-compliance rate that drove the NO_TOOLS_PREAMBLE redesign.

**We do:** Nothing. No metrics, no logging, no tracking.

**Why the gap:** Telemetry requires an observability stack. Building one would teach infrastructure, not agents.

**Learning value:** High. The telemetry is where the calibration lives. The 2.79% failure rate is not a number someone reasoned to — it was measured. Understanding that production numbers come from measurement (not design) changes how you think about the techniques.

### A/B testing infrastructure

**Production:** Feature-flagged prompt sections (`feature('KAIROS')`) allow different users to receive different prompt variants. CC can measure which variant produces better task completion, fewer errors, or lower token cost. The agent list was moved from tool descriptions to an attachment message after measuring that this saved 10.2% of fleet cache creation tokens (CC TS source comment).

**We do:** Single prompt variant, no measurement.

**Why the gap:** A/B testing requires user traffic (scale) and infrastructure. A study project has neither.

**Learning value:** Medium. The insight is that prompt engineering at production scale is experimental, not authorial. Write → measure → iterate. We teach the write step only.

### Session-level cost tracking

**Production:** `UsageTracker::from_session()` in `claw-code/rust/crates/runtime/src/usage.rs` rebuilds cumulative token counts when a session is restored. Token tracking survives process restarts. CC tracks 4D token counts: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`.

**We do:** No cost tracking. The Anthropic API returns usage fields; we discard them.

**Why the gap:** Deliberate — adds boilerplate without teaching agent concepts.

**Learning value:** Low for concept, high for production ops. Knowing your cost per session is table stakes for running agents at scale.

---

## Safety gaps

Things that protect against real harm. These gaps are the most consequential — a study project can survive without telemetry; a production system cannot survive without safety.

### File system sandboxing

**Production:** CC operates within workspace boundaries defined by the project directory. The permission system (`permissions.rs`, 232 lines) enforces an ordered permission hierarchy: `READ_ONLY < WORKSPACE_WRITE < DANGER_FULL_ACCESS`. The Agent tool requires `DANGER_FULL_ACCESS` to spawn subagents — in default `WORKSPACE_WRITE` mode, multi-agent architectures silently fail.

**We do:** `permissions.py` implements the same permission enum and policy pattern. Permission check happens before tool execution, and denials are written as `is_error=true` tool results so the LLM sees the rejection. This gap is largely closed.

**Why the gap:** Mostly closed — this was Unit 1's core lesson.

**Learning value:** N/A — already implemented. The lesson was learning WHY the check happens inside the loop, not outside it.

### Recursive agent prevention

**Production:** Coordinator agents have `DangerFullAccess` (can spawn subagents). Worker agents run under `swarmWorkerHandler.ts` with restricted permissions — workers cannot fork sub-workers. This prevents recursive spawning.

**We do:** Same `PermissionPolicy` for both coordinator and workers. Our coordinator could technically spawn workers that spawn workers.

**Why the gap:** Deliberate simplification. Our coordinator delegates sequentially, and workers don't have access to the fork mechanism. The risk exists in theory, not in practice for a 3-tool study agent.

**Learning value:** High. The distinction between coordinator-level and worker-level permissions is easy to miss and hard to add retroactively.

### Audit trail

**Production:** Every tool call, denial, and result is in the transcript (`TranscriptStore` in `claw-code/src/query_engine.py`). The transcript is separate from `mutable_messages` — it is never truncated or compacted. Full history survives compression.

**We do:** Single `messages` list. When compaction runs, old messages are replaced with the summary. The original tool calls are gone.

**Why the gap:** Deliberate — covered conceptually in Unit 3. The production pattern (two separate lists) adds implementation complexity. The concept (you need a separate store for the uncompressed record) is teachable without implementing it.

**Learning value:** High. This gap is subtle: the system works without the audit trail, but you lose debuggability and session replay. You won't notice the gap until you need to debug a production failure.

### `sed -i` interception

**Production:** FileEditTool intercepts `sed -i` commands. The model cannot use sed for in-place file edits — it must use the structured file editing tool. This is code-level enforcement: the model cannot claim "I used sed to fix line 42" and have it be real.

**We do:** No sed interception. Our tools are `read_file`, `write_file`, `bash`. The bash tool can run sed.

**Why the gap:** Our bash tool is intentionally limited in scope, so this is less of a concern. But the principle — block escape hatches that bypass the tool's audit trail — is real.

**Learning value:** Medium. The specific mechanism is less important than the principle: every path that lets the model act without leaving a tool result is a path that breaks the intent-execution gap enforcement.

---

## Reliability gaps

Things that prevent failures. The difference between a demo and a production system is often just this category.

### Retry with exponential backoff

**Production:** On HTTP 529 (overloaded), CC retries with exponential backoff. This is standard for any system that calls external APIs at scale.

**We do:** Crash on API error. One rate limit error ends the session.

**Why the gap:** Adds error handling complexity without teaching agent concepts. The right pattern (retry with backoff, max retries, jitter) is well-documented elsewhere.

**Learning value:** Low — this is API client engineering, not agent architecture. But it's the first thing you add when moving from study project to real use.

### Circuit breaker for repeated tool failures

**Production:** After N consecutive tool errors, the system stops trying that tool class rather than running the agent into a wall. Referenced in CC source comments as protection against buggy tool implementations.

**We do:** Tool errors go back to the LLM as `is_error=true` tool results. The LLM might choose a different approach, or might retry the same failing tool 16 times.

**Why the gap:** Over-engineering for a study project with 3 tools. Real concern with large tool registries where individual tools can fail independently.

**Learning value:** Low for concept, medium for production. Relevant when you have 20+ tools and some are external APIs.

### Error recovery vs crash

**Production:** Errors are first-class values. `TurnResult` carries a named `stop_reason` field: `completed`, `max_turns_reached`, `max_budget_reached`, `error`. The caller can handle each case differently.

**We do:** Return the raw API response object. `stop_reason` is buried inside. Callers (like `main.py`) don't distinguish between "completed normally" and "hit the iteration limit."

**Why the gap:** Deliberate simplification in Unit 1. Adding a DTO for stop_reason teaches abstraction, not agent concepts.

**Learning value:** Medium. Named exit conditions are the difference between a system you can operate and a system you can only hope works.

### Graceful degradation during compaction

**Production:** `NO_TOOLS_PREAMBLE` prevents tool calls during compaction. `maxTurns: 1` physically enforces it. If the compaction LLM call fails, the system falls back to the deterministic summary. Multiple layers of defense so compaction failure doesn't end the session.

**We do:** Context_v2 implements the LLM-based compaction. If it fails, the session errors out.

**Why the gap:** The fallback chain (LLM compaction → deterministic extraction → no compaction but continue) is multiple implementations deep. Too much infrastructure for a study project.

**Learning value:** High conceptually. Knowing that production compaction has multiple fallback layers changes how you think about depending on it.

---

## Performance gaps

Things that optimize cost and speed. None of these affect correctness — they affect economics.

### Prompt cache architecture

**Production:** `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` in `claw-code/rust/crates/runtime/src/prompt.rs` splits the system prompt into a static section (cached across calls) and a dynamic section (uncached). Everything before the boundary — tool descriptions, base instructions, anti-pattern lists — never changes and is cached. The Anthropic API caches prompt prefixes, so the static section costs nothing after the first call.

**We do:** Single system prompt, not split. Every API call sends the full prompt. Every call pays full token cost.

**Why the gap:** Prompt cache management requires infrastructure. The concept is teachable (and taught in Unit 3 and Unit 5) without implementing it in the nano code.

**Learning value:** High for economics. At 10+ calls per session, the static section is 50-70K tokens saved per session. At scale, this is what makes agent economics viable.

### Partial compaction

**Production:** `PartialCompactDirection` in CC TS allows compressing only the oldest messages while preserving recent ones. Two directions: compress-from-start or compress-from-end.

**We do:** Full compaction only — all old messages replaced by a single summary.

**Why the gap:** Adds selection logic complexity. The concept (preserve recent at the cost of old) is explained in Unit 3 without implementing it.

**Learning value:** Medium. Relevant when you have long sessions with a hot current task and important early context.

### KV cache forking for subagents

**Production:** When the coordinator spawns a subagent, the subagent can share the coordinator's KV cache. The first API call in a subagent is nearly free if the parent's context is already cached.

**We do:** Each subagent starts from scratch. No cache sharing.

**Why the gap:** This is deep runtime optimization requiring cache pointer sharing across API calls. Not learnable from the Python client.

**Learning value:** Low for understanding, high for cost. For parallel subagent architectures, cache forking can cut cost by 50%.

### Semantic search over memory

**Production:** Instead of loading all memory files, CC can retrieve only the entries relevant to the current task via a 256-token side call for relevance scoring.

**We do:** Load all memory files (small enough that this doesn't matter for a study project).

**Why the gap:** Semantic search requires embedding model + vector store. The infrastructure would dominate the memory concept.

**Learning value:** Medium. The principle (only retrieve what's relevant, not everything you have) matters at scale when memory grows to thousands of entries.

---

## Architecture gaps

Structural differences that couldn't be addressed without rewriting the fundamental design.

### Dual codebase (Rust + TypeScript)

**Production:** CC has two codebases. TypeScript for the frontend, agent logic, and tool implementations. Rust (via claw-code) for the performance-critical runtime: `conversation.rs` (585 lines), `compact.rs` (485 lines), `permissions.rs` (232 lines). The Rust crate is compiled into the TS application via WASM or native binding.

**We do:** Single Python module. Everything in one language.

**Why the gap:** The dual codebase exists for performance (Rust) and web deployment (TS/WASM). Python has neither requirement for a study project.

**Learning value:** High for architecture, low for agent concepts. The lesson is that production agent systems have hot paths (the loop, compaction) that justify a different language. Knowing the hot paths tells you what matters.

### Plugin system and hook protocol

**Production:** The Agent SDK exposes a hook protocol: `PreCompact`, `PostToolExecution`, `PreAgentSpawn`. External code can observe and modify behavior at defined extension points without forking the core.

**We do:** No hook protocol. Modifying behavior requires editing the core files.

**Why the gap:** Hook protocols require stable interface contracts. Our code is structured for learning (change anything), not for extensibility (preserve interfaces).

**Learning value:** Medium. The hook protocol is what allows CC to be extended by MCP servers, user scripts, and third-party tools without modifying core behavior. Understanding what hooks exist tells you what the production team considers extension points vs invariants.

### Injectable API client

**Production:** `ConversationRuntime<C, T>` in `conversation.rs` — both the API client and tool executor are traits (interfaces). Tests use `ScriptedApiClient` that returns pre-recorded responses. No API key needed for 200+ unit tests.

**We do:** Hardcoded `client = Anthropic()`. Tests require a real API key or are mocked at the function level.

**Why the gap:** Dependency injection in Python requires either a framework or careful design. Neither teaches agent concepts.

**Learning value:** Medium. The pattern (injectable client = testable system) is universal. The nano implementation demonstrates why it matters: our 4 test files test much less than production's 200+.

### CLAUDE.md content hashing and deduplication

**Production:** In monorepos with many nested CLAUDE.md files, the same file might appear in multiple search paths. `prompt.rs` deduplicates by content hash — if two files have the same content, only one is injected. Also enforces a 4000 char/file limit and 12000 char total limit, truncating with `[truncated]`.

**We do:** No CLAUDE.md handling. Static system prompt only.

**Why the gap:** The CLAUDE.md system is a CC-specific feature for project configuration. Our study project configures via code, not config files.

**Learning value:** Low for agent concepts, high for CC specifically. If you're building a CC-compatible tool, you need to understand how CLAUDE.md is processed.

---

## Gaps that ARE the curriculum

Most gaps above are things we don't implement because they're over-engineering, infrastructure concerns, or CC-specific features. But some gaps, when understood rather than implemented, teach the most important things about production agent engineering. These are worth studying, not closing.

### Gap 1: The feedback loop (telemetry → calibration)

The 2.79% tool non-compliance rate is a specific number in CC source. It drove a specific design change (stronger NO_TOOLS_PREAMBLE). Without telemetry, you can't know your failure rate. Without knowing your failure rate, you can't justify engineering investment in fixing it. Without fixing it, you have a system that fails 2.79% of the time in ways you can't see.

Understanding this gap teaches: production agent engineering is empirical, not theoretical. You build measurement infrastructure first, then optimize. The nano curriculum teaches the optimization without the measurement. If you go to production, add measurement first.

### Gap 2: The two-list problem (messages vs transcript)

We use one list. Production uses two. The compaction operates on `mutable_messages`; the `TranscriptStore` is append-only and never touched. This means you can replay any session, debug any failure, and restore any conversation without losing history.

Understanding this gap teaches: in any system with lossy compression (and compaction is lossy), you need an uncompressed record. This is true in databases (WAL), in video codecs (I-frames), in systems engineering generally. The agent form is just another instance of the same principle.

### Gap 3: Agent as tool_use block (not function call)

Our `coordinator.py` calls `run_worker()` as a Python function. Production's coordinator emits an `agent_use` tool_use block, and the runtime forks the subagent. This is not a minor implementation difference — it's the difference between orchestration-in-code and orchestration-in-model.

When the LLM decides to fork via tool_use, it can also decide NOT to fork. It can adjust the task description. It can synthesize across multiple subagent results. When we call `run_worker()` in Python, the fork is unconditional — the code decides, not the model.

Understanding this gap teaches: "orchestration is a prompt, not code" means the LLM should have the decision, not just the execution. The code handles the HOW; the model handles the WHEN and WHETHER.

### Gap 4: Compaction as the reliability-performance intersection

Compaction sits at the intersection of all three reliability problems. It solves context degradation (the performance problem). But the compactor itself is subject to non-compliance (hence NO_TOOLS_PREAMBLE), produces output that could have an intent-execution gap (hence the 9-section structured format that includes all user messages verbatim), and must preserve the tool call/result pairs from the tool loop (hence understanding Unit 1 is a prerequisite for Unit 3).

Understanding this gap teaches: the "layers" mental model breaks down at compaction. Compaction is not a layer — it's a cross-cutting mechanism that touches every other layer. Production systems are full of these. Identifying them is a core production engineering skill.

### Gap 5: The 513K-to-1000-line ratio

The scale difference isn't just lines of code. It's discovered edge cases, error recovery, telemetry, graceful degradation, extensibility, and calibrated numbers. The nano implementation cannot achieve the same behavior because it lacks the feedback loop that produced those behaviors.

Understanding this gap teaches: reading production code is not sufficient to reproduce production behavior. The techniques are necessary but not sufficient. The missing piece — measurement, iteration, co-evolution with the model — is what separates understanding from building. This is not a limitation of the curriculum. It's what the curriculum is about.

---

## The meta-lesson

We don't implement most of these gaps because closing them would make the code longer without making the concepts clearer. A 5000-line nano implementation with telemetry, retry logic, prompt cache management, and hook protocols would be harder to understand than production CC, not easier.

The right relationship with these gaps is: understand why they exist, understand what failure mode they prevent, and understand what it would take to close them for your own production system. You don't learn to build production systems by building all the infrastructure at once. You learn by understanding each layer well enough to know what's missing — and why.

That's what this curriculum is for.
