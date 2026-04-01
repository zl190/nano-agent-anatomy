# Agent Reliability Triad: Three Problems CC Solves

Source: CC TS leaked source (513K lines) + claw-code + experiment data.
Cross-validated against: Anthropic Docs & Eng Blog, Agent SDK, CC TS source, claw-code (4 sources).
Berkeley MOOC lecture numbers appear below as suggested reading — they are not cross-validated (lecture content was not extracted or verified against code).

## The Three Problems

Every agent system faces three reliability problems. CC addresses all three with layered defenses.

```
1. 不服从 (Non-compliance)     — Model knows what to do but doesn't do it
2. 说了不做 (Intent-execution gap) — Model says it will do X but doesn't actually do X
3. Context degradation           — Model's capability degrades as context grows
```

---

## Problem 1: Non-Compliance ("知道但不做")

**The symptom:** Model is instructed "don't use tools" but uses tools anyway. 2.79% failure rate on Sonnet 4.6 with "weaker trailer instruction" (CC source comment in compact/prompt.ts).

### CC's Three-Layer Defense

**Layer 1: Prompt instruction**
```
"Do not rubber-stamp weak work"
"Resume directly — do not acknowledge the summary"
```
Relies on model cooperation. Insufficient alone (2.79% failure on Sonnet 4.6).

**Layer 2: Consequence framing**
```
CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.
- Tool calls will be REJECTED and will waste your only turn
  — you will fail the task.
```
Source: `src/services/compact/prompt.ts:19-25`

Not "please don't" — "you will fail." Makes compliance the model's optimal strategy via game-theoretic framing. The model is told the consequences, not just the rule.

**Layer 3: Code enforcement**
| Mechanism | Source | Bypassable? |
|-----------|--------|-------------|
| `maxTurns: 1` for compaction | compact/prompt.ts:16 | No — tool call wastes the only turn |
| `is_error: true` on denied tools | conversation.rs:130-217 | No — model perceives rejection |
| `max_iterations = 16` | conversation.rs hard ceiling | No — runtime stops loop |
| Feature flag DCE | `feature('KAIROS')` at bundle time | No — code physically absent |
| `formatCompactSummary()` strips `<analysis>` | compact implementation | No — post-processing |
| Permission check BEFORE execution | permissions.rs | No — tool never runs |
| `sed -i` interception | FileEditTool | No — sed never executes |

**Key insight:** CC never relies on any single layer. Every critical behavior has all three layers. The 2.79% that bypass Layer 1 are caught by Layer 2 (most decide compliance is optimal) and Layer 3 (the rest are physically blocked).

---

## Problem 2: Intent-Execution Gap ("说了但没做")

**The symptom:** Model says "I'll fix the bug" but the fix is wrong, incomplete, or never actually executed. Model says "I checked" but didn't actually check.

### CC's Three Architectural Patterns

**Pattern 1: Actions = Tool Calls (not text)**

In CC, "doing" something requires calling a tool. The model cannot claim to have edited a file — it must call FileEditTool, and the tool returns the actual diff or error. Text is not action. Tool results are ground truth.

```
Model says "I fixed the bug"
  → Insufficient. Must call FileEditTool.
    → Tool returns actual diff (observable ground truth)
      → Diff is in context — model and user both see what happened
```

**Pattern 2: Physical Preconditions (don't trust claims)**

`readFileState: Map<path, {content, timestamp}>`

Source: FileEditTool, FileWriteTool, FileReadTool — shared state map.

```
FileReadTool  → populates readFileState
FileEditTool  → checks readFileState:
                 1. File must be in map (must have been read)
                 2. mtime must match (no stale reads)
                 3. Not in map → REJECT edit
```

> "Read-before-write is enforced, not advisory. The tool rejects edits if readFileState has no entry for the file, or if the file's mtime is newer than the last read timestamp."
> — Source reading experiment, Reader 2 analysis of FileEditTool

Model claims "I read the file" without calling FileReadTool → FileEditTool rejects. Physical evidence, not verbal claims.

**Pattern 3: Independent Verification Agent**

Source: `src/tools/AgentTool/built-in/verificationAgent.ts`

System prompt opens with:
> "Your job is not to confirm the implementation works — it's to try to break it."

Explicitly names two failure modes the verification agent itself is prone to:
1. **Verification avoidance** — finding reasons not to run checks, reading code, writing "PASS" without executing
2. **Being seduced by the first 80%** — seeing polished UI and passing, not noticing half the features don't work

Physical enforcement on the verifier:
> "The caller may spot-check your commands by re-running them — if a PASS step has no command output, or output that doesn't match re-execution, your report gets rejected."

Also: verifier is STRICTLY PROHIBITED from modifying the project. Read-only + temp scripts only. This prevents the verifier from "fixing" issues instead of reporting them.

**Design philosophy:** Model's words are not evidence. Tool results are evidence. Independent verification is evidence of evidence.

---

## Problem 3: Context Window Degradation

**The symptom:** Model performance degrades as conversation grows. At 30-50K absolute tokens, complex reasoning noticeably worsens. See: "Why Your 1M Context Window Degrades Faster Than Your Old 20K" (blog) and "Context Degradation Ate My YAML" (blog).

### What We Knew Before (Theory — from our blogs)

Three mechanisms, all absolute-token-dependent:
1. **Softmax dilution** — entropy Θ(log n), attention per token decreases with absolute n (Nakanishi 2025)
2. **Lost in the middle** — U-curve position dependence, 39% drop in multi-turn (Liu 2023, Laban 2025)
3. **Position OOD** — beyond training range, position encodings are extrapolated not learned (Du 2025)

Threshold: ~30-50K absolute tokens, regardless of window size.

### What CC Actually Does (Engineering — from leaked source)

**CROSS-VALIDATION DISCREPANCY:**
- claw-code (Rust port): DETERMINISTIC compaction. Zero LLM calls. Pure extraction of stats, recent requests, key files, pending work.
- CC TS (production): LLM-BASED compaction. Full 9-section prompt with `<analysis>` scratchpad, then strip analysis, keep summary.

The claw-code version is a pedagogical simplification. Production uses an LLM because the summary quality matters more than the cost of one LLM call.

**CC's Compaction Architecture:**

1. **Dual trigger:** `message_count > N AND tokens >= budget` (AND, not OR)
   - Prevents false positives: short conversations with many messages don't compress, long system prompts with few messages don't compress.

2. **LLM-based summary with 9 sections:**
   - Primary Request and Intent
   - Key Technical Concepts
   - Files and Code Sections (with full code snippets!)
   - Errors and Fixes
   - Problem Solving
   - All User Messages (every non-tool-result user message)
   - Pending Tasks
   - Current Work (most recent activity, verbatim quotes)
   - Optional Next Step (must directly align with most recent request)

3. **`<analysis>` scratchpad:**
   - Model first writes analysis in `<analysis>` tags (chain-of-thought for compaction)
   - `formatCompactSummary()` strips the analysis
   - Only `<summary>` reaches context
   - Internal reasoning stays internal

4. **NO_TOOLS_PREAMBLE enforcement:**
   ```
   CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.
   Tool calls will be REJECTED and will waste your only turn.
   ```
   - `maxTurns: 1` — physical enforcement
   - Sonnet 4.6 was calling tools 2.79% of the time with weaker instruction

5. **Partial compaction** (`PartialCompactDirection`):
   - Can compress only old messages, preserving recent ones
   - Two directions: compress-from-start vs compress-from-end

6. **`SYSTEM_PROMPT_DYNAMIC_BOUNDARY`:**
   - Splits system prompt into static (cached) and dynamic (uncached) parts
   - Static part: tool descriptions, base instructions — never changes mid-session
   - Dynamic part: CLAUDE.md content, MCP server list, agent definitions
   - Only dynamic part causes cache busts

7. **Agent list optimization (10.2% savings):**
   - Dynamic agent list was in tool description → description changes busted cache
   - Moved to attachment message → tool schema stays static → cache preserved
   - Comment: "The dynamic agent list was ~10.2% of fleet cache_creation tokens"

8. **PreCompact hook:**
   - External code can observe/modify before compaction fires
   - SDK exposes this: `PreCompact` hook event
   - Cannot replace the algorithm, but can inject additional context

### The Gap: Theory → Engineering

| Our blog (theory) | CC source (engineering) | The bridge |
|-------------------|----------------------|------------|
| Softmax dilution Θ(log n) | SYSTEM_PROMPT_DYNAMIC_BOUNDARY keeps critical content at start | Engineering response to mechanism I |
| Lost in the middle | 9-section summary preserves ALL user messages and current work | Engineering response to mechanism II |
| Position OOD past training range | Compaction resets absolute position by replacing old messages | Engineering response to mechanism III |
| 30-50K threshold | Dual trigger (count AND tokens) — fires in this range | Calibrated to the empirical threshold |
| "Context degradation ate my YAML" — Haiku failure | NO_TOOLS_PREAMBLE + maxTurns:1 — same pattern, different fix | Enforcement for compaction quality |

### Blog Angle: "I wrote about why context degrades. Then I read how Anthropic deals with it."

**Before (our blogs):** Three mechanisms explain WHY. Empirical threshold ~30-50K. Heuristic: plan for 200K not 1M.

**After (CC source):** Anthropic's engineering response to each mechanism. Plus the surprise: compaction uses an LLM (not deterministic), with a 9-section prompt that preserves more context than any tutorial approach, plus physical enforcement to prevent the compactor itself from degrading.

**The meta-insight:** Our blogs diagnosed the disease correctly. CC source reveals the treatment. The treatment matches the diagnosis — each engineering mechanism maps to a specific degradation mechanism. This cross-validation strengthens both: our theory predicts what CC builds, CC's code confirms our theory.

---

## Framework Mapping

| Problem | Template | Persona | Procedure | Enforcement |
|---------|----------|---------|-----------|-------------|
| Non-compliance | Output format spec | Task-specific persona | Step sequence | **Three layers: prompt → consequence → code** |
| Intent-execution gap | Tool-based action | "Try to break it" verifier | Read→Edit→Verify | **readFileState + verification agent** |
| Context degradation | 9-section summary | Compaction specialist | Dual trigger → LLM summary → strip | **maxTurns:1 + NO_TOOLS_PREAMBLE** |

---

## Dimension A: Problem → Solution → Science/Philosophy

Each CC solution maps to a problem AND a deeper scientific or philosophical principle.

| Problem | CC Solution | Underlying Science / Philosophy |
|---------|-------------|-------------------------------|
| **Non-compliance: model ignores instructions** | NO_TOOLS_PREAMBLE + consequence framing | **Game theory (mechanism design):** Make compliance the dominant strategy by altering payoffs. "You will fail" changes the reward landscape. Also: **behaviorism** — behavior shaped by consequences not intentions. B.F. Skinner: organisms don't obey instructions, they respond to contingencies. |
| **Non-compliance: model calls tools when told not to** | `maxTurns: 1` physical enforcement | **Physics of irreversibility:** A wasted turn is an irreversible loss in a finite budget. Also: **control theory** — open-loop control (instructions) fails under perturbation, closed-loop (physical feedback) is robust. |
| **Non-compliance: model uses disabled features** | Feature flag DCE at bundle time | **Information theory (absence of signal):** The model literally cannot see the code. Non-existence is the ultimate enforcement. Cf. **Kerckhoffs's principle** in cryptography: security shouldn't depend on secrecy of the algorithm, but here it does — the algorithm is removed. |
| **Intent-execution gap: model claims without acting** | Actions = tool calls only, tool results as ground truth | **Empiricism (Popper):** Claims must be falsifiable. A text claim ("I edited the file") is unfalsifiable. A tool call produces observable evidence. Also: **science philosophy** — the distinction between claim and evidence. |
| **Intent-execution gap: model acts on stale information** | `readFileState` Map with mtime check | **TOCTOU (time-of-check-to-time-of-use)** from concurrent systems. Also: **epistemology** — knowledge has a timestamp. Stale knowledge is not knowledge. Neuroscience: working memory decays and must be refreshed. |
| **Intent-execution gap: model verifies own work** | Independent verification agent ("try to break it") | **Popper's falsificationism:** Verification ≠ confirmation. You strengthen a claim by failing to falsify it, not by confirming it. Also: **adversarial systems** in ML (GANs), legal systems (prosecution vs defense), science (peer review). |
| **Context degradation: attention dilution** | `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` + prompt cache | **Information theory (Shannon):** Channel capacity is finite. Prioritize high-value bits at privileged positions (beginning of context = high attention). Also: **neuroscience** — primacy effect in human memory (first items better recalled). |
| **Context degradation: lost in the middle** | 9-section compaction preserving ALL user messages | **Cognitive psychology (Miller 1956):** Working memory holds 7±2 chunks. Compaction = chunking. The 9 sections are deliberate chunks. Also: **lossy compression** — the question is WHAT to lose, not WHETHER to lose. |
| **Context degradation: position OOD** | Compaction resets absolute position by replacing old messages | **Neuroscience (hippocampal replay):** During sleep, the brain replays and consolidates memories, resetting them into long-term storage. autoDream is literally named after this. Compaction = forced hippocampal replay. |

## Dimension B: Problem → Solution → CS System Design → Tradeoff

Each CC solution embodies a classic CS system design pattern with a known tradeoff.

| CC Solution | CS System Design Pattern | Classic System Analog | Tradeoff |
|-------------|------------------------|----------------------|----------|
| **NO_TOOLS_PREAMBLE + maxTurns:1** | **Fail-fast / circuit breaker** | Erlang "let it crash" + circuit breaker (Hystrix) | Speed vs recovery: wasted turn = fast failure detection, but no retry opportunity. CC accepts the 2.79% loss for the 97.21% speed gain. |
| **is_error: true on denied tools** | **Exception as data (not flow control)** | Go's `err != nil` vs Java's exceptions. Error returned as value in message stream. | Transparency vs complexity: model SEES the error (can adapt), but must handle it gracefully. Bad: model might argue with the denial. Good: model can choose alternative approach. |
| **Feature flag DCE** | **Dead code elimination / feature toggles** | Facebook's Gatekeeper, LaunchDarkly | Binary vs gradual: feature is either ON or OFF at bundle time. No A/B, no gradual rollout, no runtime toggle. CC trades flexibility for certainty — disabled features are provably absent. |
| **readFileState Map** | **Optimistic concurrency control (OCC)** | Database OCC: read → compute → check-version → write. Git merge: detect conflicts at write time, not read time. | Latency vs safety: every write pays a validation cost (mtime check). But prevents the stale-write bug class entirely. Also: no locking overhead (optimistic, not pessimistic). |
| **Verification agent (read-only)** | **Separation of concerns: writer vs auditor** | Database: read replicas vs write primary. Audit systems: segregation of duties (SOD). Kubernetes: admission controllers are read-only validators. | Coverage vs cost: independent agent = extra API call ($). CC justifies by: builder is biased toward own work, only adversarial review catches the last 20%. Also: verifier cannot "fix" issues = forces reporting, not silent patching. |
| **Tool call = action (not text)** | **Command pattern / message passing** | CQRS: commands (write) are distinct from queries (read). Actor model: all effects via message passing, no shared state. | Expressiveness vs auditability: model can't express "I edited 3 files" in one breath — must call 3 separate tool calls. Slower but auditable. Every action has a receipt (tool result). |
| **9-section compaction prompt** | **Lossy compression with structured schema** | Video codecs (H.264 I-frames): keep keyframes (user messages), compress inter-frames (assistant reasoning). Also: database vacuuming — reclaim space while preserving active data. | Quality vs size: more sections = better preservation but larger summary. CC's 9 sections are calibrated: experiments showed fewer sections lost critical context (user messages, pending tasks). |
| **`SYSTEM_PROMPT_DYNAMIC_BOUNDARY`** | **Cache partitioning / hot-cold separation** | CPU L1/L2 cache: hot instructions stay cached. CDN: static assets cached, dynamic requests hit origin. Redis: hot keys in memory, cold keys evicted. | Cache hit rate vs flexibility: static prompt = always cached (50-70K tokens savings). But any change to dynamic part (CLAUDE.md, MCP servers, agent list) busts the dynamic portion only, not the static. 10.2% fleet savings from moving agent list to attachment = measured ROI. |
| **`<analysis>` scratchpad stripped** | **Internal representation vs external interface** | Compiler IR: internal SSA form is richer than output assembly. HTTP: request processing state ≠ response body. Encapsulation in OOP. | Reasoning depth vs context cost: `<analysis>` lets model think deeply, but if kept in context, it wastes tokens on future turns. Strip = use the reasoning, discard the working. Tradeoff: can't debug the compactor's reasoning after the fact. |
| **Partial compaction (direction)** | **Sliding window / ring buffer** | TCP sliding window: keep recent, drop old. Log rotation: compress old logs, keep recent. Database WAL: checkpoint old, keep tail. | Recency bias vs global context: partial compact preserves recent at the cost of old. Correct for most tasks (recent context matters more) but wrong for "recall something from the beginning." |
| **autoDream consolidation** | **Background garbage collection** | Java GC (G1): concurrent marking + compaction. Log-structured merge trees (LSM): background compaction of levels. | Latency vs freshness: runs when user is idle (no interference with active work). But stale entries persist until the next idle period. Also: consolidation is itself an LLM call = cost. |

## Curriculum Position

This content belongs in:
- **Unit 3** (Context Compression) — the degradation mechanisms + CC's compaction architecture
- **Unit 5** (Production Prompt Engineering) — the three-layer enforcement pattern
- **Unit 6** (Integration + Security) — the verification agent + readFileState
- **Blog** — "From theory to production: what 513K lines taught me about context degradation"
