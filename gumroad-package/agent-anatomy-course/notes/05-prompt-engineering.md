# Unit 5: Production Prompt Engineering

Source: CC TS `src/tools/*/prompt.ts` (44 files), `src/constants/prompts.ts`
Cross-validation: CC TS source, Anthropic Eng Blog ("Building Effective Agents", "Effective Context Engineering", "Advanced Tool Use", "Claude Code Auto Mode"), Agent SDK
MOOC: Berkeley CS294 (no direct prompt engineering coverage — confirmed across F24/S25/F25)

---

## The biggest surprise: prompt engineering is engineering, not craft

The introductory Anthropic docs teach prompt engineering as a writing skill: be clear, be specific, use examples. The CC TypeScript source reveals it as software engineering with the same concerns as any production system — caching, dead code, A/B testing, structured output, negative-example enforcement.

44 `prompt.ts` files. Each tool gets its own optimized instructions. The system prompt is split at a cache boundary. Prompt sections are feature-flagged. Anti-patterns are named and forbidden inline.

None of this appears in any tutorial.

---

## Six patterns from 44 production tool prompts

### 1. NO_TOOLS_PREAMBLE — one-shot enforcement

The compaction prompt and skillify prompt both open with:

```
You have no tools. Tool calls will be REJECTED and will waste your only turn.
```

This is explicit, negative, and specific. Why not just not provide tools? Because the model has been trained on millions of agentic sessions where it calls tools. Omitting the tool list doesn't suppress the behavior — it just makes the tool call fail silently. The preamble forces the constraint into attention before any other instruction.

Lesson: vague "don't do X" instructions get ignored. Specific negative + consequence ("REJECTED and will waste your only turn") gets honored.

### 2. `<analysis>` scratchpad — reasoning that gets consumed and discarded

Production prompts instruct the model to output reasoning inside `<analysis>` tags before giving the actual result:

```
<analysis>
... internal reasoning ...
</analysis>
<result>
... actual output ...
</result>
```

The runtime strips `<analysis>` blocks before the result enters the conversation context. This gives the model a structured thinking space without polluting the context window. The reasoning happens, improves the output quality, then disappears.

Same principle as chain-of-thought, but production-grade: the thoughts are consumed then discarded. The context window only sees the clean output. This matters at scale — every token you discard is a token not competing for attention in the next turn.

### 3. Feature-gated prompt sections

Prompt files use `feature('KAIROS')` guards to conditionally include sections:

```typescript
const kairosPart = feature('KAIROS') ? `
  [KAIROS-specific instructions]
` : '';
```

This is dead code elimination for prompts. If a feature flag is off, the section doesn't exist — no tokens spent, no conflicting instructions. It also enables A/B testing: different users see different prompt variants, and the system measures which variant produces better outcomes.

The key insight: a prompt that's always active but conditionally relevant is worse than a prompt that's physically absent when irrelevant. Irrelevant instructions increase noise even when the model "ignores" them.

### 4. Agent list as attachment, not embedded tool description

The list of available agent types (exploreAgent, planAgent, verificationAgent, etc.) is injected as a text attachment in the dynamic section — not embedded inside each tool's description.

Why? Tool descriptions live in the static section (cached). The agent list changes per session (dynamic). If the agent list were embedded in each tool description, any change to the agent roster would invalidate the entire cache for all tool descriptions.

By putting the agent list in a single attachment in the dynamic section, all 44 tool descriptions remain cached even when the agent list changes. This saves ~10% of cache tokens per session — compounding across millions of sessions.

### 5. Anti-pattern enforcement in prompt text

Production prompts don't just describe desired behavior. They name forbidden behaviors explicitly:

```
"Never delegate understanding"
"Don't peek at files you haven't been asked about"
"Don't race to a solution before understanding the problem"
"Do not rubber-stamp weak work"
```

These aren't safety guardrails. They're behavioral guardrails for quality. The model is told what failure looks like, not just what success looks like. Negative examples activate different training patterns than positive instructions — the model has seen these failure modes and can recognize them when they're named.

Academy teaches: use positive examples. Production does: positive examples + named anti-patterns. The anti-patterns do as much work as the positive instructions.

### 6. Skillify multi-round interview

`skillify.ts` converts a completed session into a reusable `SKILL.md` through a structured interview rather than one-shot summarization:

**Round 1 — session analysis:** Extract what the user actually did (not what they said they did).
**Round 2 — intent clarification:** What was the goal? What constraints applied?
**Round 3 — pattern extraction:** What's generalizable? What was session-specific?
**Round 4 — skill draft:** Write the trigger conditions, steps, and quality criteria.

Why interviews instead of summarization? One-shot summarization extracts what happened. Interviews extract what should be repeated. A session might include 30 steps — skillify identifies the 5 that form the reusable pattern and discards the noise.

Output: a complete skill definition that can trigger on natural language and execute reliably.

---

## The system prompt architecture

`src/constants/prompts.ts` defines a two-section system prompt with an explicit boundary marker:

```typescript
const SYSTEM_PROMPT_DYNAMIC_BOUNDARY = '---DYNAMIC_SECTION---';
```

**Static section** (before the boundary):
- Tool descriptions
- Base behavior rules
- Anti-pattern lists
- Role definitions

**Dynamic section** (after the boundary):
- Agent list (changes per session)
- User config and preferences
- Session state

The Anthropic API caches the prefix of a system prompt across calls. Everything before `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` is identical across sessions → cached → ~90% cheaper per API call. Everything after the boundary is session-specific → not cached.

This is invisible to users. It's a financial architecture decision embedded in the prompt structure. At a million daily active users making 10 calls per session, a 90% cache hit on the static section is not a minor optimization — it's what makes the economics viable.

---

## Anthropic Eng Blog cross-validation

### "Building Effective Agents" (Dec 2024)
URL: https://www.anthropic.com/research/building-effective-agents

**"Poka-yoke" principle for tool design (confirmed):** Error prevention at definition time. Design tool schemas so invalid invocations fail at the definition layer, before the LLM can emit a bad call. This is the engineering formalization of "write clear tool descriptions."

**Workflow vs Agent distinction:** Workflows = predefined code paths; agents = LLMs dynamically directing tool use. Prompt engineering differs for each: workflow prompts define fixed sequences; agent prompts define decision criteria.

### "Effective Context Engineering for AI Agents" (Sep 2025)
URL: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

**Just-in-time tool loading:** `defer_loading: true` reduces context from ~72K → ~500 tokens (confirmed in "Advanced Tool Use" eng blog). This is a prompt architecture decision: maintain lightweight identifiers in the system prompt, load full tool descriptions only when invoked.

### "Claude Code Auto Mode" (Mar 2026)
URL: https://www.anthropic.com/engineering/claude-code-auto-mode

**Three-tier permission structure (confirmed):**
- Tier 1: Safe tools (reads, navigation) → auto-permitted — no prompt needed
- Tier 2: In-project file edits → auto-allowed with lower scrutiny
- Tier 3: Shell, external, out-of-project → two-stage classifier (Stage 1: fast single-token filter; Stage 2: chain-of-thought)

False positive reduction: 8.5% → 0.4% using the two-stage approach. Blocked categories: "scope escalation," "credential exploration," "safety-check bypass."

This confirms that the CC permission system is partly prompt-driven: the Stage 2 classifier uses CoT reasoning about whether a tool call falls into a blocked category — i.e., the permission decision is a mini-prompt-engineering problem.

### "Advanced Tool Use" (Nov 2025)
URL: https://www.anthropic.com/engineering/advanced-tool-use

**`allowed_callers` field:** Restricts tool access by execution environment. Tool-level permission filtering at definition time — an extension of poka-yoke to multi-agent contexts (coordinator can call tool X, workers cannot).

## Cross-validation discrepancies

| What introductory docs teach | What CC source + eng blog shows | Gap |
|---|---|---|
| "Write clear, specific prompts" | Cache-optimized architecture with static/dynamic split | Introductory docs don't cover prompt caching economics |
| "Use positive examples" | Anti-patterns (what NOT to do) are first-class instructions | Intro docs focus only on positive examples |
| "System prompts set behavior" | System prompts are feature-flagged, A/B tested, version-controlled | Intro docs treat prompts as static text |
| "Chain of thought improves quality" | `<analysis>` scratchpad implements CoT but strips output before context | Intro docs don't cover consuming-then-discarding reasoning |
| Tool design = write good descriptions | Poka-yoke: error prevention at definition time + `allowed_callers` + `defer_loading` | Production tool engineering has 3 additional dimensions intro docs omit |

---

## What Production Does That We Don't

| Production feature | Why it matters | Why we skip it |
|---|---|---|
| 44 specialized tool prompts | Each tool gets optimized, non-generic instructions | We use generic tool descriptions for clarity |
| Static/dynamic prompt split at cache boundary | 90% cheaper via Anthropic prompt caching | Requires cache management infrastructure |
| Feature-flagged prompt sections | A/B testing, gradual rollout, dead code elimination | Over-engineering for a study project |
| `<analysis>` scratchpad (strip before context) | Reasoning quality without context pollution | Adds parsing infrastructure; teach concept, skip impl |
| Skillify interview pipeline | Converts sessions → reusable skills | Requires multi-turn orchestration; own unit |
| Anti-distillation watermark | Prevents competitors training on CC outputs | Security measure, not pedagogical |
| NO_TOOLS_PREAMBLE | Prevents tool-calling in text-only contexts | Our prompts don't mix tool/no-tool contexts |

---

## The one-sentence insight

Production prompt engineering is cache-aware software engineering with negative examples, structured output formats, and dead code elimination — not the "write clearly" advice from tutorials.

---

## Comprehension check

1. Why does CC use `NO_TOOLS_PREAMBLE` instead of just not providing tools to the model?
2. What's the purpose of the `<analysis>` scratchpad if it gets stripped before entering the conversation context?
3. Why is the agent list injected as an attachment rather than embedded in each tool's description?
4. How does the static/dynamic split save money at scale — what specific API behavior does it exploit?
5. Why are anti-patterns (what NOT to do) important in production prompts — what does naming a failure mode do that a positive instruction doesn't?
