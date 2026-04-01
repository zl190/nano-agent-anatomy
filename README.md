# nano-agent-anatomy

[![Tests](https://img.shields.io/badge/tests-95%20passing-brightgreen?style=flat-square)]()
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)]()

A study notebook for understanding how production AI agents actually work — from the inside.

## Why This Exists

On March 31, 2026, [Claude Code's source leaked via npm](https://www.theregister.com/2026/03/31/anthropic_claude_code_source_code/) — 512K lines of TypeScript. Most "nano-agent" tutorials stop at the tool loop. Production agents have four layers on top of that: memory, context compression, and multi-agent coordination. This notebook rebuilds each layer small enough to fit in your head, cross-validated against the actual production source.

This is not a framework. It is a study notebook you learn from by reading.

## Quick Start

```bash
git clone https://github.com/your-handle/nano-agent-anatomy  # update with your remote
cd nano-agent-anatomy
pip install anthropic

python main.py                     # basic agent loop
python main.py --memory            # with cross-session persistence
python main.py --memory --compress # with context compression
python main.py --coordinate "task" # multi-agent
```

Run the tests to verify your environment:

```bash
pip install pytest
pytest tests/
# 76 passed in 0.8s
```

## What It Does

Most agent tutorials give you one file with a `while True` loop. This notebook gives you the full stack — each layer introduced progressively, each file under 150 lines.

**The four layers:**

```
4. coordinator.py — multi-agent orchestration        (Unit 4)
3. context.py     — compress old turns               (Unit 3)
2. memory.py      — persist across sessions          (Unit 2)
1. loop.py        — LLM → tool → result → repeat    (Unit 1)
```

**What makes this different from other nano-agent repos:**

- Every implementation is cross-validated against production source (CC TypeScript, 513K lines) — not invented from API docs
- Discrepancies between sources are made explicit and explained, not glossed over
- Found a genuine curriculum gap: Berkeley's 45 lectures across 3 semesters have zero coverage of context compression
- Ran a blind A/B experiment on the reading methodology itself (free-form vs. structured schema); free-form wins 6-1 — the result that shaped the final SOP
- Includes a novel contribution not in any production framework: correction-aware microcompact (`context_v4.py`)

## Course Structure

7 units, progressive. Each unit has a learning note, code progression, tests, and an explicit "what production does that we don't" gap analysis.

### Unit 0: Methodology

How to systematically read production source with AI agents. Includes the blind experiment data comparing free-form vs. structured-schema reading (see `experiment/`). Hypothesis: structured schema improves quality. Result: free-form wins 6-1. The SOP that came out of this is more useful than the original hypothesis.

### Unit 1: The Tool Loop

The `while True` loop that every tutorial shows you is already wrong. Production adds: max iterations (hard ceiling at 16), `is_error` flag for denied tools, and permission checks before execution — not after.

Code progression: `loop_v0.py` (bare loop) → `loop_v1.py` (max iterations + is_error) → `loop_v2.py` (streaming + token budget) → `loop_v3.py` (permission check before execution)

```python
# loop_v1.py — the part tutorials skip
if result.type == "tool_use":
    if not permissions.check(result.name):
        # denied tools return is_error=True with the denial reason
        # not an exception — the loop must continue
        messages.append(tool_result(result.id, deny_reason, is_error=True))
        continue
```

### Unit 2: Memory and Consolidation

Memory in production is not a growing list. CC uses a two-layer architecture: a `MEMORY.md` index that is always loaded, and per-topic files that are loaded on demand. Consolidation (autoDream) runs four phases: Orient, Gather, Consolidate, Prune — entries older than 30 days with no references get removed.

Code progression: `memory_v0.py` (append-only) → `memory_v1.py` (MEMORY.md index + per-file) → `memory_v2.py` (autoDream consolidation)

### Unit 3: Context Compression

The biggest surprise in the source: context compression in production is LLM-based, not deterministic. The claw-code Rust port (the clean reimplementation with tests) does deterministic extraction. CC TypeScript sends a structured 9-section prompt with an `<analysis>` scratchpad that gets stripped before the result reaches context. That discrepancy — two implementations of the same feature with completely different approaches — is where the learning is.

Also documented: Berkeley's absence of coverage. All three iterations of CS294 (Fall 2024, Spring 2025, Fall 2025 — 45 lectures total) have zero coverage of context compression. See `publish/blog-curriculum-gap.md`.

Code progression: `context_v0.py` (naive summarize) → `context_v1.py` (deterministic, claw-code pattern) → `context_v2.py` (LLM-based, CC TS pattern) → `context_v3.py` (NO_TOOLS_PREAMBLE + dual trigger) → `context_v4.py` (correction-aware microcompact — novel)

`context_v4.py` is the one contribution that goes beyond the production source. When a user corrects a wrong model output, both the wrong answer and the correction stay in context — causing softmax dilution, lost-in-the-middle interference, and self-reinforcement. Microcompact collapses the pair into a single correction note. Not yet in CC or any framework as of April 2026.

### Unit 4: Multi-Agent Coordination

The surprising finding: orchestration in production is a natural language system prompt, not a programmatic API. The coordinator prompt includes phrases like "Brief like a smart colleague," "Never delegate understanding," and "Do not rubber-stamp weak work." Workers get isolated histories. The coordinator rejects bad work.

Code progression: `coordinator_v0.py` (hardcoded decomposition) → `coordinator_v1.py` (LLM-driven decomposition) → `coordinator_v2.py` (worker isolation + scratch directories) → `coordinator_v3.py` (CC prompt patterns)

### Unit 5: Production Prompt Engineering

44 production tool prompts from the CC source, analyzed for patterns: `NO_TOOLS_PREAMBLE` enforcement, `<analysis>` scratchpad stripping, feature-gated conditional sections, and how the agent list moved from tool descriptions to an attachment (saving 10.2% cache tokens).

### Unit 6: Integration and Verification

All four layers running together. Security audit from `permissions.rs` (232 lines). Final gap analysis: `notes/08-final-gap.md`.

## The Sources

Every claim is cross-validated across four validated sources. The value is where they disagree.

| Source | What it teaches | Status |
|--------|----------------|--------|
| **CC TypeScript source** (513K lines) | Real implementation: prompts, permissions, memory, compaction | Primary — validated |
| **claw-code** (Rust port, 21 files) | Clean reimplementation with tests; simplifications documented | Validated |
| **Anthropic Academy + Agent SDK** | Official teaching + control protocol surface | Validated |
| **Berkeley MOOC** (CS294, 45 lectures) | Theory: ReAct, multi-agent, planning, safety | Reference only — not validated against code |

**Known discrepancies (the gold):**
- Compaction: claw-code = deterministic, CC TS = LLM with 9-section prompt
- Agent spawning: SDK = `AgentDefinition` dataclass, CC source = "Never delegate understanding" + fork-vs-fresh cache strategy
- Permissions: Academy teaches 5 modes, CC source has fail-secure (unknown → highest) + deny reason as `is_error`
- Memory: SDK exposes a `memory` flag, CC source has 2-layer architecture + autoDream + semantic search

## File Layout

```
nano-agent-anatomy/
├── loop.py, loop_v0.py ... loop_v3.py      # Unit 1: tool loop
├── memory.py, memory_v0.py ... memory_v2.py # Unit 2: memory
├── context.py, context_v0.py ... context_v4.py # Unit 3: context
├── coordinator.py, coordinator_v0.py ... coordinator_v3.py # Unit 4: coordinator
├── permissions.py                          # permission check layer
├── main.py                                 # full pipeline runner
├── tests/                                  # 76 tests
│   ├── test_loop.py
│   ├── test_memory.py
│   ├── test_context.py
│   └── test_coordinator.py
├── notes/                                  # methodology + source analysis
│   ├── 00-pedagogical-research.md          # design rationale (Karpathy method)
│   └── 00-source-validation-audit.md       # 5-source audit with URLs
├── experiment/                             # blind A/B reading experiment data
└── publish/                                # 4 blog posts
    ├── blog-context-degradation.md
    ├── blog-context-pollution.md
    ├── blog-credence-good-berkeley.md
    └── blog-curriculum-gap.md
```

## Rules

- Each `.py` file is 150 lines or under. If it is longer, the concept is not simplified enough.
- No dependencies beyond `anthropic`. Zero-framework understanding.
- Comments explain why (the production insight), not what (the code is readable).

## Preview

Read a full sample note and the blind experiment report before buying anything:

- [`preview/01-tool-loop.md`](preview/01-tool-loop.md) — Unit 1: The 6 things tutorials skip about production agent loops
- [`preview/experiment-report.md`](preview/experiment-report.md) — Blind A/B experiment on source reading methodology

## Full Analysis

The code is open. The detailed notes, exercises, cross-validation audit, and correction log are available separately:

**[Agent Anatomy — Full Analysis →](https://yclab.gumroad.com/l/agent-internals)**

What's in the course that's not in this repo:
- Full 5-source cross-validation analysis per unit (CC TS × claw-code × Berkeley MOOC × Anthropic Eng Blog × Agent SDK — where they disagree is where the insight is)
- Complete exercises with solutions
- Correction log: what I got wrong at each stage and why
- Production gap analysis: what each layer does in production that our 150-line version skips

## See Also

- [Berkeley CS294: Agentic AI](https://rdi.berkeley.edu/agentic-ai/f25)
- [claw-code](https://github.com/instructkr/claw-code) — Rust clean-room reimplementation
- [CC source leak coverage](https://www.theregister.com/2026/03/31/anthropic_claude_code_source_code/) — The Register

## License

MIT
