# Week 3: Context Compression

Source: `claw-code/rust/crates/runtime/src/compact.rs` (485 lines)
Python port: `claw-code/src/query_engine.py` compact_messages_if_needed() + `transcript.py`
MOOC: Berkeley CS294 — NO coverage of context compression across F24/S25/F25 (confirmed gap — see below)
Cross-validation: CC TS source (primary), claw-code, Anthropic Eng Blog ("Effective Context Engineering"), Agent SDK

## The biggest surprise: no LLM call

Every tutorial that teaches context compression does this: "when conversation gets too long, call the LLM to summarize it." Production doesn't. `compact.rs` is 485 lines of pure deterministic code. Zero LLM calls.

Why? Three reasons:
1. **Cost** — summarization calls cost tokens. Over millions of sessions, this adds up.
2. **Predictability** — LLM summaries vary. Deterministic extraction is testable.
3. **Speed** — no API round-trip. Compaction is instant.

## Correction: CC TS uses LLM-based compaction

**Previous belief:** Compaction is deterministic (zero LLM calls).
**Corrected to:** CC TypeScript source uses a full LLM prompt with 9 structured sections + `<analysis>` scratchpad.

The claw-code Rust port simplified this to deterministic extraction. The real CC TS production system (`src/services/compact/prompt.ts`) sends a detailed prompt asking the LLM to analyze the conversation across 9 dimensions:

1. Conversation statistics
2. User's primary intent
3. Key decisions made
4. Tools used and their outcomes
5. Files modified or referenced
6. Errors encountered
7. Pending tasks
8. Environment state
9. Important context to preserve

The LLM outputs `<analysis>...</analysis>` (internal reasoning, stripped before storage) followed by `<summary>...</summary>` (the actual compressed context).

**Why the discrepancy?** claw-code is a simplified reimplementation. Our code progression captures both:
- `context_v1.py` = deterministic (claw-code pattern)
- `context_v2.py` = LLM-based with scratchpad (CC TS pattern)

**This validates our pedagogical approach:** build the simple version first (understand the structure), then study why production chose differently (richer context preservation at the cost of tokens and predictability).

## What deterministic compaction extracts

The summary is structured XML, not prose:

```xml
<summary>
Messages: 42 user, 38 assistant
Recent requests: "fix the auth bug"; "run the tests"; "deploy to staging"
Tools used: bash, write_file, read_file
Key files: src/auth.rs, tests/auth_test.rs, deploy.yaml
Pending: "still need to update the changelog"; "tests for edge case"
Timeline: [truncated role+content for each message]
</summary>
```

Each piece is extracted by simple code:
- **Recent requests**: last 3 user messages, truncated to 160 chars
- **Key files**: regex scan for tokens with `/` and known extensions (rs/ts/js/json/md/tsx), max 8
- **Pending work**: keyword scan for "todo", "next", "pending", "follow up", "remaining"
- **Timeline**: every message's role + content truncated, full trace

## Anthropic Eng Blog cross-validation

Source: "Effective Context Engineering for AI Agents" (Sep 2025)
URL: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

**"Context rot" (official Anthropic term):** Recall accuracy decreases as token count increases. This is the production motivation for compaction — not just cost, but quality degradation. Our code implements the compaction trigger but doesn't surface this framing.

**Tool Result Clearing (confirmed):** Lightest form of compaction. Remove tool result content while keeping the tool call record. Preserves the action trace without the bulk of outputs. Not implemented in our code.

**Compaction output categories (official Anthropic, 5 categories):** accomplished, WIP, files, next steps, constraints. The "9 sections" in CC TS `src/services/compact/prompt.ts` is internal implementation detail — NOT the 5 officially documented categories. See gap note below.

**Sub-agent summary size:** 1,000-2,000 tokens. Condensed summaries from subagents, not full transcripts. Validates `agentMemorySnapshot.ts` design (return rich summary, not raw messages).

### Gap: "9-section compaction" — internal only, not officially validated

The 9 sections documented in `src/services/compact/prompt.ts` (conversation statistics, user intent, decisions, tools used, files modified, errors, pending tasks, environment state, context to preserve) come from our CC TS source reading only. Official Anthropic docs list 5 categories. The 9 sections are real (we read the source) but should be cited as "CC TS internal implementation" not "officially documented structure."

## Berkeley MOOC — confirmed coverage gap

Context compression is not covered in any Berkeley LLM Agents course iteration:
- Fall 2024: No lecture on context compression
- Spring 2025 L5 (Yu Su): "Memory, Reasoning, Planning" covers HippoRAG (long-term RAG-based retrieval) — different mechanism, different problem. Not context window management.
- Fall 2025: Oct 1 "Memory and Knowledge Management" is the closest candidate, but slide content not verified for compression coverage.

**Conclusion:** Unit 3 has no MOOC cross-validation. Primary sources are CC TS source code + Anthropic eng blog.

## Six production patterns

### 1. Dual trigger (AND, not OR)

```rust
messages.len() > preserve_recent_messages AND estimated_tokens >= max_estimated_tokens
```

Only compress when BOTH conditions are true. Short conversations with many messages? Don't compress. Long system prompt with few messages? Don't compress. This prevents two types of false positives.

### 2. Summary is System role, not User

Tutorials inject `{"role": "user", "content": "[Summary]..."}` plus a fake assistant reply. Production inserts a System role message. This avoids breaking the user/assistant alternation requirement and doesn't waste a user turn.

### 3. Suppress follow-up questions

After compaction, LLMs want to say "Let me summarize where we were..." This wastes tokens. Production injects:

> "Resume directly — do not acknowledge the summary, do not recap what was happening, and do not preface with continuation text."

The more specific the wording, the better the LLM obeys.

### 4. Token estimation is intentionally crude

```python
estimated_tokens = len(text) // 4 + 1  # ~20% error, and that's fine
```

Precise counting needs a tokenizer call. The ~20% error is acceptable for a trigger decision. Real token counting comes from API response headers (`usage` field).

### 5. `<analysis>` tags get stripped

Production LLMs sometimes emit `<analysis>` scratchpad before `<summary>`. `format_compact_summary()` strips the analysis, keeping only the summary. Internal reasoning stays internal.

### 6. Key files cap at 8, summaries at 160 chars

The summary itself has a token budget. Without caps, a compaction summary could be bigger than the conversation it replaces. 8 file paths and 160-char truncation per entry keep the summary small.

## Correction: "14 cache break vectors" are NOT in the code

The previous draft claimed claw-code tracks "14 cache break vectors" with "sticky latches." **These terms do not appear in the claw-code source.** Full-text search for `cache_break`, `sticky`, `latch` returns zero results.

These concepts come from [Alex Kim's analysis](https://alex000kim.com/posts/2026-03-31-claude-code-source-leak/) of the original TypeScript source, which was deleted from claw-code. The claw-code Rust port only has:
- `TokenUsage.cache_creation_input_tokens` + `cache_read_input_tokens` (API response fields)
- `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` in prompt.rs (static/dynamic split for cache)
- `autoCompactEnabled` config flag (name only, no implementation)

The 14-vector and sticky-latch claims need the original TS or Alex Kim's article as source, not claw-code.

## Theory (from our own research)

These papers explain WHY compression matters:
- Softmax entropy grows O(log n) with sequence length (Scalable-Softmax, Nakanishi 2025)
- Lost in the Middle: U-curve position dependence (Liu 2023)
- Multi-turn degradation: 39% performance drop (Laban 2025)
- Context length hurts even with perfect retrieval (Du 2025)

## What I changed in context.py

1. **Replaced LLM summary with deterministic extraction** — stats, recent requests, key files, pending work
2. **Added dual trigger** — message count AND token estimate
3. **Added suppress_follow_up_questions** — specific wording from production
4. **Added key file extraction** — regex scan with extension whitelist
5. **Added pending work inference** — keyword matching

Still using user/assistant pair instead of System role (API constraint — System role goes in the `system` parameter, not `messages` array). Production handles this at the runtime layer.

## Production → Our code mapping

| Production concept | Our implementation | Gap |
|---|---|---|
| Deterministic summary | summarize_messages() in context.py | **Done** |
| Dual trigger (AND) | should_compress() checks both | **Done** |
| Suppress follow-up | Specific wording in continuation | **Done** |
| Key file extraction | extract_file_paths() with regex | **Done** |
| Pending work inference | infer_pending_work() keyword scan | **Done** |
| System role for summary | User/assistant pair (API constraint) | Architectural |
| `<analysis>` tag stripping | Not needed (we don't use LLM) | N/A |
| Full key timeline | Only stats + recent requests | Nice-to-have |
| Transcript separate from messages | Single list | Week 2 (with memory) |

## Code progression files

- `context_v0.py` — LLM summarization (tutorial: "summarize this conversation")
- `context_v1.py` — deterministic extraction (compact.rs pattern)
- `context_v2.py` — LLM-based with `<analysis>` scratchpad (CC TS pattern)
- `context_v3.py` — add `NO_TOOLS_PREAMBLE` enforcement + dual trigger
- `context_v4.py` — correction-aware microcompact (novel, see notes/09)
- `context.py` — latest integrated version

## What Production Does That We Don't

| Production feature | Why it matters | Why we skip it |
|---|---|---|
| LLM-based compaction with 9-section prompt (CC TS) | Richer, more nuanced summaries than deterministic | Covered in context_v2.py progression |
| `<analysis>` scratchpad stripped from output | LLM reasons internally without polluting context | Covered in context_v2.py progression |
| `NO_TOOLS_PREAMBLE` enforcement | Prevents tool calls during compaction | Covered in context_v3.py progression |
| `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` | Separates cacheable vs dynamic prompt sections | Cache optimization — production scale concern |
| Prompt cache break detection | Knows when cache is invalidated | Needs tokenizer + cache API integration |
| Partial compaction (keep some old messages) | Preserves important context beyond keep_recent | Adds selection logic complexity |
| System role for summary (not user/assistant pair) | Avoids breaking message alternation | API constraint — System goes in `system` param |

## Comprehension check

1. Why doesn't production use an LLM to generate the summary?
2. Why is the trigger AND (both conditions) rather than OR?
3. What happens if you don't suppress follow-up questions after compaction?
4. Why cap key files at 8 and summaries at 160 chars?
