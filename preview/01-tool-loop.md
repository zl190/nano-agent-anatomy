# Week 1: The Tool Loop

Source: `claw-code/rust/crates/runtime/src/conversation.rs` (584 lines)
Python port: `claw-code/src/query_engine.py` (193 lines)
MOOC: Berkeley CS294 F24 L2 (Shunyu Yao, OpenAI) — ReAct formal definition, validated
Cross-validation: CC TS source, claw-code, Anthropic Eng Blog (Tool Use API docs), Agent SDK, Berkeley MOOC F24 L2

## What the production loop actually looks like

The core of every AI agent is a loop: send a message to the LLM, check if it wants to call a tool, execute the tool, send the result back, repeat. Tutorials teach this in 20 lines. Production needs 584.

The difference isn't complexity for its own sake. It's six things tutorials skip.

## Six things tutorials skip

### 1. The loop has a hard ceiling

```python
MAX_ITERATIONS = 16  # conversation.rs default
```

Tutorials write `while True`. Production writes `for _ in range(16)`. The difference: a buggy tool that always returns "try again" will loop forever in a tutorial agent. In production, it hits 16 and returns a RuntimeError.

In claw-code, this is configurable per-instance via a builder method (`with_max_iterations`), defaulting to 16. The ceiling protects the system from the agent, not from the user.

### 2. Permission check happens BEFORE execution

```
Tool call arrives → check permission → THEN execute
                                    → OR write denial as is_error=true tool_result
```

The denied tool call doesn't disappear. It goes back to the LLM as an error result with the full reason: "tool 'bash' requires DANGER_FULL_ACCESS but current mode is WORKSPACE_WRITE." The LLM sees the rejection and can choose a fallback — like using write_file instead of bash to create a file.

Tutorials either skip permissions entirely or raise an exception that kills the loop.

### 3. Three stop conditions, not one

Production has an iteration limit, a token budget, AND a server-side pause:

```python
# query_engine.py
max_turns: int = 8         # API call count limit
max_budget_tokens: int = 2000  # token spend limit
```

When any fires, `stop_reason` tells you which: `max_turns_reached` vs `max_budget_reached` vs `completed` vs `pause_turn`. This is a first-class field on the result, not an exception.

`pause_turn` is a fourth stop reason returned by the Anthropic API when the server-side iteration limit is hit (distinct from the client-side `max_turns`). Source: Tool Use API docs (https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works).

### 4. The API client is injectable

```rust
pub struct ConversationRuntime<C, T> {  // C: ApiClient, T: ToolExecutor
```

Both the API client and tool executor are traits (interfaces). Tests use `ScriptedApiClient` that returns pre-recorded responses. No API key needed for unit tests.

Tutorials hardcode `client = Anthropic()`. Production injects it. This is the difference between "works on my machine" and "has 200 tests."

### 5. Session restore preserves cost

```rust
UsageTracker::from_session(session)  // rebuilds cumulative token count
```

When you restore a saved session, the token counter doesn't reset to zero. It rebuilds from the session history. This means cost tracking survives across process restarts.

Tutorials don't track cost at all.

### 6. Transcript and messages are separate

```python
# query_engine.py has both:
self.mutable_messages = [...]    # gets compacted (truncated)
self.transcript = TranscriptStore()  # full history, never truncated
```

Messages get compressed by the context compaction system — old messages are replaced with a summary. But the transcript keeps everything for replay, debugging, and session restore.

Tutorials use one list for both. When you compress, you lose the full history.

## Code progression files

- `loop_v0.py` — bare while loop, no safety (the tutorial version)
- `loop_v1.py` — add max_iterations + is_error for denied tools
- `loop_v2.py` — add streaming + token budget tracking
- `loop_v3.py` — add permission check before execution
- `loop.py` — latest integrated version

## What I changed in loop.py

Based on this analysis, three changes:

1. **Added MAX_ITERATIONS = 16** — `for` loop instead of `while True`
2. **Added permission check** — deny writes `is_error=true` tool_result back to LLM
3. **Imported PermissionPolicy** — separate module, fail-secure default

Still missing (future weeks):
- Token budget as second stop condition
- TurnResult DTO with stop_reason
- Transcript separate from messages
- Injectable API client for testing

## Production → Our code mapping

| Production concept | Our implementation | Gap |
|---|---|---|
| max_iterations=16 | MAX_ITERATIONS=16 in loop.py | **Done** |
| Permission check before execution | PermissionPolicy in permissions.py | **Done** |
| Deny → is_error tool_result | Deny reason written to messages | **Done** |
| Token budget stop condition | Not implemented | Week 1 stretch |
| TurnResult DTO with stop_reason | Raw response object | Week 1 stretch |
| Transcript separate from messages | Single messages list | Week 2 (with memory) |
| Injectable API client | Hardcoded Anthropic() | Nice-to-have |
| Streaming events | Blocking calls | Not needed for learning |
| Tool registry (JSON snapshot) | Hardcoded TOOLS list | Nice-to-have |

## MOOC cross-validation (F24 L2 — Shunyu Yao, OpenAI)

Slides: http://llmagents-learning.org/slides/llm_agent_history.pdf (60 slides)

**ReAct formal definition (slide 31):** Â = A ∪ L — the action space includes language sequences as first-class actions. A reasoning step (â_t ∈ L) updates context only; it does not affect the environment. This is the theoretical grounding for why the tool loop distinguishes "think" steps from "act" steps.

**ReAct performance (slide 31):** PaLM-540B with ReAct: 35.1 HotpotQA / 64.6 FEVER / 71 ALFWorld — beats both reasoning-only and acting-only baselines. Production data validating the two-stop-condition architecture (thinking turns also consume budget).

**Cross-validation with CC source:**
- ReAct action space Â = A ∪ L → `conversation.rs`: tool_use blocks (A) + text blocks (L) both go through the same loop iteration
- "Reasoning is internal action" → extended thinking tokens count toward the iteration budget
- `stop_reason == "tool_use"` from API docs confirms canonical loop exit condition
- `pause_turn` stop reason (API docs) = server-side iteration limit hit — a third named stop condition beyond max_turns and max_budget

**Note on lecture numbering:** Early drafts referenced "L2: System Design (Yangqing Jia, NVIDIA)" — this speaker/topic is not found in any Berkeley LLM Agents course iteration (F24, S25, F25). The correct F24 L2 is Shunyu Yao (OpenAI) on agent history and ReAct.

## The one-sentence insight

The production tool loop isn't a loop with tools — it's a **state machine with safety rails**, where every exit path is named and every denial is visible to the agent.

## What Production Does That We Don't

| Production feature | Why it matters | Why we skip it |
|---|---|---|
| Token budget as second stop condition | Prevents cost runaway across many short turns | Added in loop_v2.py progression |
| TurnResult DTO with named stop_reason | Caller knows WHY the loop ended | Adds abstraction without teaching a new concept |
| Transcript separate from messages | Full history survives compaction | Covered in Unit 3 (context) |
| Injectable API client (trait/interface) | Enables 188 unit tests without API keys | Would need dependency injection framework |
| Streaming events | Real-time output, partial tool results | Blocking calls are clearer for learning |
| Tool registry (JSON snapshot at session start) | Tools can be added/removed at runtime | Our 3 tools are static |
| Retry with backoff (529 pattern) | Handles API rate limits gracefully | Adds error handling complexity |
| Circuit breaker for repeated failures | Stops after N consecutive tool errors | Over-engineering for a study project |

## Comprehension check

1. Why does production use `for _ in range(16)` instead of `while True`?
2. What happens when a tool is denied — does the loop stop?
3. Why are messages and transcript separate lists?
4. If you restore a session, what happens to the token counter?
