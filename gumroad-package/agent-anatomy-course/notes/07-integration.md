# Unit 6: How the Layers Compose

Source: All previous units + CC TS + claw-code
Cross-validation: CC TS, claw-code, Anthropic Academy, Agent SDK/CCA (4-source)

---

## The biggest surprise: layers aren't independent

Tutorials teach the layers as Lego blocks. Build the tool loop in week 1. Add memory in week 2. Add context compression in week 3. Add coordination in week 4. Each layer is a module you snap on.

That's not how they work in production.

The layers interact. Context compression must understand tool call structure or it loses the call/result pairs that the next turn depends on. Memory consolidation changes what the coordinator knows about prior subagent work. Permission checks don't happen at the coordinator level — they happen inside the tool loop, which both the main agent and every subagent share. The reliability triad from Unit 5 (non-compliance, intent-execution gap, context degradation) isn't a separate concern — it cuts across all five layers simultaneously.

The Lego metaphor fails because it implies independence. What we built is closer to a circuit: changing one component changes the behavior of the whole.

---

## How the layers compose in CC

A single user request moves through every layer before producing a response. Here's the actual flow:

```
User message arrives
  → System prompt applied (Unit 5: static/dynamic boundary, NO_TOOLS_PREAMBLE)
    → Tool loop begins (Unit 1: for _ in range(16), not while True)
      → Permission check: does this tool require DangerFullAccess? (Unit 1, permissions.rs)
        → Denied: is_error=true tool_result back to LLM (model sees rejection, chooses fallback)
        → Allowed: tool executes
          → readFileState check if FileEditTool (Unit 5/6: physical precondition)
          → Tool result enters messages
      → Memory check: extract entities from this exchange? (Unit 2: autoDream trigger)
        → If yes: update MEMORY.md index + relevant memory file
      → Context check: message_count > N AND tokens >= budget? (Unit 3: dual trigger AND)
        → Compaction fires: 9-section LLM prompt → strip <analysis> → summary into messages
        → Subagents get fresh context window; coordinator gets compacted one
    → Coordinator: does this require a subagent? (Unit 4: agent_use tool_use block)
      → Subagent spawned with DangerFullAccess (fork rights from coordinator)
      → Subagent runs its own loop — same tool loop (Unit 1), same permission check
      → Subagent's result via agentMemorySnapshot (not return value)
      → Coordinator synthesizes across subagent results
  → Response
```

This isn't a pipeline where output passes from one box to the next. The tool loop is the substrate that every other layer runs inside. Compaction runs inside the loop. Memory updates run inside the loop. Subagents run their own loops.

---

## Three cross-cutting concerns

### 1. The three-layer enforcement pattern appears everywhere

Unit 5 identified it for non-compliance: prompt instruction → consequence framing → code enforcement. What wasn't obvious until looking at all units together: this same pattern appears in every single layer.

- **Tool loop:** "use tools" (prompt) → is_error=true on denial (consequence) → max_iterations hard ceiling (code)
- **Memory:** "extract entities" (prompt) → stale entries get pruned (consequence) → 25KB output limit (code)
- **Compaction:** "text only" (prompt) → "tool calls REJECTED and waste your only turn" (consequence) → maxTurns:1 (code)
- **Coordinator:** "orchestrate" (prompt) → "sub-workers cannot fork" (consequence) → DangerFullAccess required for Agent tool (code)

Every layer that matters gets all three layers. The pattern isn't a compaction-specific trick — it's CC's universal enforcement architecture.

### 2. readFileState connects Unit 1 and Unit 5

`readFileState: Map<path, {content, timestamp}>` in `FileEditTool` looks like a Unit 1 concern (tool execution). But the instruction that enforces it lives in the system prompt: "read before edit" is a prompt instruction. The mechanism that enforces it is the tool rejecting edits if readFileState has no entry.

Prompt says what to do. Code makes non-compliance impossible. This is the clearest example of the three-layer pattern working across layers.

### 3. Compaction must understand tool calls to preserve them

Context compression (Unit 3) can't treat all messages as prose. Tool use blocks and tool results are structured pairs: call a tool, get a result. If compaction splits them — keeping the call but not the result, or vice versa — the LLM receives a malformed conversation history.

Production `compact.rs` tracks which content blocks are tool calls and tool results separately from text. When deciding what to preserve in the timeline, it keeps tool call/result pairs intact. This is why you can't implement compaction without understanding the tool loop first. Unit 1 is a prerequisite for Unit 3 — even though we built them weeks apart.

---

## The co-evolution insight

Reading the units in isolation, it's tempting to extract the techniques and apply them to any agent system. Most of them transfer. But some of the numbers — max_iterations=16, the 30-50K token compaction threshold, the 9 compaction sections — are calibrated against the specific model CC runs on, through months of production telemetry.

The comment in `compact/prompt.ts` is explicit: "Sonnet 4.6 was calling tools 2.79% of the time with weaker trailer instruction." That number is from real traffic. The fix (NO_TOOLS_PREAMBLE + maxTurns:1) was tuned against that real traffic. Our nano implementation applies the same fix without the data. It probably works. But we don't know if 2.79% is the right threshold for acting, or what the equivalent rate is for our model/prompt combination.

CC's techniques work not just because they're technically correct — but because they were developed with feedback loops (fleet telemetry, A/B experiments, model co-evolution) that we don't have. The nano implementations capture the structural insight. They can't capture the calibration.

This isn't a failure of the curriculum. It's the curriculum. Understanding why these numbers exist — and what it would take to derive them for your own system — is what separates reading production code from building production systems.

---

## What Production Does That We Don't

| Production (CC) | Nano | The gap |
|---|---|---|
| 513K lines TS+Rust | ~1000 lines Python | Scale: 500x — not complexity for its own sake, but 8 months of discovered edge cases |
| 8 months of model co-evolution | Static implementation | Feedback loop: CC's technique is inseparable from the telemetry that tuned it |
| Fleet-level telemetry (token counts, failure rates, cache hit ratios) | None | No measurement = no calibration = no principled tuning |
| A/B testing infrastructure (feature-flagged prompt sections) | None | No experimentation = techniques frozen at initial design |
| Error recovery + retry with backoff on 529 | Crash on API error | No resilience: one flaky API call ends the session |
| PreCompact hook (SDK-exposed, external injection) | No hook protocol | No extensibility: compaction algorithm is locked |
| Rust crate boundary (runtime vs tools vs prompts) | Single flat module | No separation of concerns: loop.py, context.py, coordinator.py all import each other |
| Cross-layer integration tests (350+ in claw-code) | 4 unit test files | Unit tests verify components; integration tests verify interactions |

---

## The one-sentence insight

The layers are not features you add — they're constraints you compose, and the composition creates behaviors that none of the layers produces alone.

---

## Comprehension check

1. Why can't compaction be implemented without understanding the tool loop first?
2. The three-layer enforcement pattern (prompt → consequence → code) appears in every unit. Find one instance in memory (Unit 2) that wasn't explicitly called out above.
3. Why doesn't "apply CC's techniques to your own agent" fully transfer — what specifically is lost?
4. In the flow diagram above, at what point does the coordinator actually decide whether to spawn a subagent — and what does that decision look like in the code?
