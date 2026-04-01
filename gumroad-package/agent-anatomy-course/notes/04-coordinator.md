# Week 4: Multi-Agent Coordination

Source: `claw-code/src/reference_data/` (TS file paths + tool snapshot)
Rust tool spec: `claw-code/rust/crates/tools/src/lib.rs` (Agent tool)
MOOC: Berkeley CS294 F24 L3 (Chi Wang + Jerry Liu, AutoGen) — 6 orchestration axes, validated
Cross-validation: CC TS source, claw-code, Anthropic Eng Blog ("Building Effective Agents"), Agent SDK, Berkeley MOOC F24 L3

## The biggest surprise: coordinator is 1 file

Everyone talks about "multi-agent orchestration" like it's a complex system. In production, `coordinator/coordinatorMode.ts` is a single file — a mode flag. The real complexity is in `tools/AgentTool/` (21 files).

Coordinator mode doesn't implement orchestration. It enables it. The LLM, guided by a system prompt, does the actual orchestration. The code handles lifecycle.

## The architecture: two layers

**Natural language layer (LLM decides):**
- What tasks to create
- Which agent type to assign
- Whether results are good enough
- When to synthesize

**Deterministic code layer (runtime handles):**
- How to fork a subagent (`forkSubagent.ts`)
- How to pass state (`agentMemorySnapshot.ts`)
- How to resume after interruption (`resumeAgent.ts`)
- Permission boundaries between coordinator and workers

The LLM decides WHAT. The code decides HOW. They're not alternatives — they're layers.

## Seven things tutorials skip

### 1. Agent is a tool, not a function call

Tutorials: `result = run_worker(task)` — Python function call.
Production: `agent_use` tool_use block — the LLM emits it, the runtime executes it.

This is the physical implementation of "orchestration is a prompt, not code." The coordinator LLM doesn't call a Python function. It emits a tool use block, and the runtime forks a subagent. The coordinator can also decide NOT to fork — it's a decision, not a hardcoded step.

### 2. Subagents share state via memory snapshots

Tutorials pass results as return values: `results.append(worker_result)`.
Production: `agentMemorySnapshot.ts` serializes the working state and injects it into the next agent's system prompt.

Why? Return values are summaries. Memory snapshots are full context. When agent #3 needs details from agent #1, the return value says "auth bug fixed." The snapshot says "auth bug was in src/auth.rs:142, the issue was a missing null check, fix was a guard clause, tests added in auth_test.rs."

### 3. Coordinator and worker have different permissions

```
coordinatorHandler.ts  → can fork new agents (DangerFullAccess)
swarmWorkerHandler.ts  → restricted (no forking, limited tools)
```

This prevents worker agents from spawning their own workers infinitely. Without this, a buggy worker could fork itself recursively until resources are exhausted.

Our `coordinator.py` uses the same PermissionPolicy for both. Production separates them explicitly.

### 4. Agent tool requires DangerFullAccess

```rust
ToolSpec { name: "Agent", required_permission: PermissionMode::DangerFullAccess }
```

In the default WorkspaceWrite mode, you cannot spawn subagents. This is rarely documented but means multi-agent architectures silently fail in restricted environments.

### 5. Tasks are persistent entities

Production has 6 task tools: TaskCreate, TaskGet, TaskList, TaskOutput, TaskStop, TaskUpdate.

Tasks aren't in-memory objects that disappear when the worker finishes. They're persistent, queryable, stoppable. `TaskOutputTool` even has a UI component for real-time streaming of task progress.

Our coordinator runs workers sequentially and forgets them immediately.

### 6. Five built-in agent types

Not all workers are generic. Production has specialized agents:

| Agent | Role |
|-------|------|
| `exploreAgent` | Codebase exploration |
| `generalPurposeAgent` | Default worker |
| `planAgent` | Architecture planning |
| `verificationAgent` | QA and validation |
| `claudeCodeGuideAgent` | User onboarding |

Each has its own system prompt with role-specific instructions. Our coordinator gives every worker the same generic prompt.

### 7. Workers can message the coordinator

`SendMessageTool` enables bidirectional communication. Workers don't just return results — they can send progress updates, ask clarifying questions, or request additional resources mid-task.

Our workers are fire-and-forget: dispatch task, wait for return value, done.

## What I changed in coordinator.py

No code changes yet — the existing implementation captures the basic pattern. The insights from this analysis are for Week 4's newsletter and future improvements.

Priority improvements for later:
1. **Agent as tool_use block** — let the LLM decide when to fork, not hardcode decomposition
2. **Memory snapshot injection** — pass full context between agents, not just return values
3. **Permission separation** — coordinator gets fork rights, workers don't

## Production → Our code mapping

| Production concept | Our implementation | Gap |
|---|---|---|
| NL orchestration via system prompt | COORDINATOR_SYSTEM prompt | **Done** (basic) |
| Worker isolation (separate messages) | Separate message lists per worker | **Done** |
| Max iterations per worker | for _ in range(10) | **Done** |
| Agent as tool_use (LLM-initiated) | run_worker() Python function | Architectural |
| agentMemorySnapshot | Return value only | High priority |
| Coordinator vs worker permissions | Same PermissionPolicy | Medium priority |
| Task persistence (Create/Get/Stop) | Workers forgotten after completion | Nice-to-have |
| Built-in agent types (5 roles) | Single generic WORKER_SYSTEM | Nice-to-have |
| SendMessage (bidirectional) | Fire-and-forget | Nice-to-have |
| spawnMultiAgent (true parallel) | Sequential for loop | Nice-to-have |

## Code progression files

- `coordinator_v0.py` — hardcoded task decomposition (tutorial version)
- `coordinator_v1.py` — LLM-driven decomposition with NL system prompt
- `coordinator_v2.py` — add worker isolation + scratch directories
- `coordinator_v3.py` — add CC prompt patterns: "brief like colleague" + "never delegate understanding"
- `coordinator.py` — latest integrated version

## What Production Does That We Don't

| Production feature | Why it matters | Why we skip it |
|---|---|---|
| Agent as tool_use block (LLM-initiated) | Coordinator decides WHEN to fork, not hardcoded | Fundamental architectural difference |
| agentMemorySnapshot (full context transfer) | Workers get rich context, not just task string | Would need serialization framework |
| Separate permissions (coordinator vs worker) | Workers can't fork sub-workers infinitely | Our PermissionPolicy is shared |
| Task persistence (Create/Get/Stop/Update) | Tasks survive process restarts, are queryable | Over-engineering for learning |
| 5 built-in agent types | Specialized workers for different task types | We use one generic worker |
| SendMessage (bidirectional communication) | Workers can ask coordinator for clarification | Fire-and-forget is simpler to understand |
| spawnMultiAgent (true parallel execution) | Workers run concurrently for speed | Sequential is clearer for learning |
| KV cache forking for subagents | Subagent shares parent's cache, saves tokens | Deep runtime optimization |

## MOOC cross-validation (F24 L3 — Chi Wang + Jerry Liu, AutoGen)

Slides: http://llmagents-learning.org/slides/autogen.pdf (37 slides)

**6 multi-agent orchestration axes (slide 14):**
1. Static vs dynamic topology
2. NL vs PL communication
3. Context sharing vs isolation
4. Cooperation vs competition
5. Centralized vs decentralized
6. Intervention vs automation

**CC coordinator classification on these axes:**
Dynamic topology (LLM decides which agents to spawn) | NL communication (coordinator ↔ workers via text, not API) | Isolation (workers get separate context, not shared messages) | Cooperation | Centralized (coordinator owns task decomposition) | Automation (no human intervention by default)

**Commander/Writer/Safeguard pattern (slides 7-9):** nested chat where a commander orchestrates a writer and a safeguard validator. Maps directly to CC: coordinator + worker + `verificationAgent.ts` ("try to break it" verifier).

**Reflection pattern (slides 21-22):** Writer + Critic with termination condition. Maps to CC's Evaluator-Optimizer pattern (official Anthropic name from "Building Effective Agents" blog post). `is_termination_msg` pattern in AutoGen = CC's `stop_reason` field on TurnResult.

**StateFlow (slide 25):** Agents as state machine, transitions triggered by message content. Maps to CC's permission system as state transitions: unknown tool → DENY state → LLM must reason about fallback.

**AutoBuild (slides 33-35):** Meta-agent builds agent teams from task description. Captain Agent = 84.25 avg vs 40.98 vanilla LLM. Analogous to CC's coordinator system prompt as the "team-building" instruction.

## Anthropic Eng Blog cross-validation

Source: "Building Effective Agents" (Dec 2024)
URL: https://www.anthropic.com/research/building-effective-agents

**Official pattern taxonomy confirmed:**
- "Orchestrator-Workers" = official Anthropic name for coordinator pattern (our implementation)
- "Evaluator-Optimizer" = `verificationAgent.ts` in CC TS
- Workflow vs Agent distinction: workflows = predefined code paths; agents = LLMs dynamically directing tool use. CC coordinator is an agent, not a workflow.

**Agent SDK cross-validation (subagent mechanics):**
- Subagents invoked via `Agent` tool (tool_use block) — confirms note section 1 ("agent is a tool, not a function call")
- Fresh context window per subagent (no parent message history) — confirms isolation axis classification
- Inherits permission context from parent — explains why DangerFullAccess flows to coordinator
- Cannot spawn further subagents (no nesting) — confirms swarmWorkerHandler restriction
- Transcripts at: `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`

Source: https://platform.claude.com/docs/en/sub-agents

## Comprehension check

1. Why is the coordinator a mode flag (1 file) rather than a complex system?
2. What problem does agentMemorySnapshot solve that return values don't?
3. Why must coordinator and worker have different permission levels?
4. What happens if Agent tool requires DangerFullAccess but you're in WorkspaceWrite mode?
5. On the 6 AutoGen orchestration axes, how does CC classify: NL or PL communication? Context sharing or isolation?
