# Session 5 Rationale Log — 2026-04-01

> Key reasoning chains preserved for audit. Not for execution agents.

## Decision evidence

### Code progressions (15 files)
- **loop_v0-v3.py**: v0 (135 lines, bare while True) → v1 (104 lines, MAX_ITERATIONS=16 + is_error from conversation.rs) → v2 (121 lines, token budget + stop_reason from CC TS query_engine) → v3 (132 lines, full PermissionPolicy from permissions.rs). Import chain: v1-v3 import TOOLS/execute_tool from v0.
- **memory_v0-v2.py**: v0 (82 lines, in-memory list, no dedup) → v1 (116 lines, MEMORY.md index + per-file, marker-based dedup, FIFO eviction at 50 lines) → v2 (147 lines, autoDream 4-phase consolidation, wipe-after-parse safety).
- **context_v0-v3.py**: v0 (112 lines, LLM summarization — the tutorial version) → v1 (140 lines, deterministic extraction from compact.rs, no Anthropic dep, dual trigger) → v2 (145 lines, LLM with 9-section schema + analysis scratchpad from CC TS) → v3 (149 lines, NO_TOOLS_PREAMBLE + dual trigger restored).
- **coordinator_v0-v3.py**: v0 (150 lines, self-contained, hardcoded "Research: X" + "Execute: X") → v1 (111 lines, LLM decomposition + synthesis) → v2 (138 lines, make_scoped_execute_tool closure for scratch dir isolation) → v3 (148 lines, CC prompt patterns + quality_check function).

### Test suite (76 tests)
- Anthropic module stubbed with `types.ModuleType` to avoid API key requirement
- Tests cover structural/deterministic aspects: permission logic, dual trigger conditions, file path extraction, analysis tag stripping, prompt pattern presence, function signatures
- memory_v1 tests use `tempfile.TemporaryDirectory` + `unittest.mock.patch.object` for INDEX_FILE

### Note updates
- "What Production Does That We Don't" tables: 7-8 rows per note, format: Feature | Why it matters | Why we skip it
- Note 03 CC TS correction: inserted after "The biggest surprise: no LLM call" — documents the claw-code vs CC TS discrepancy
- Note 05: 6 patterns (NO_TOOLS_PREAMBLE, analysis scratchpad, feature-gated sections, agent list as attachment, anti-pattern enforcement, skillify interview), cross-validation table, production gap table

## Unconfirmed proposals

- **Bundle cc-fuel-gauge blog with nano-agent launch**: Session 5 suggestion. Fuel-gauge shows the problem (context degradation), nano-agent shows the anatomy. Cross-link for reinforcement.
- **"Why CC methods don't solve our problems" as course section**: Session 5 brainstorm. Three layers of gap: (1) scale makes techniques effective, (2) prompts co-evolved with model, (3) real lesson is principles not patterns.
- **Update cc-fuel-gauge Phase 3 with CC TS compaction findings**: Phase 3 assumed deterministic compaction (from claw-code). CC TS uses LLM-based 9-section prompt. This changes the optimization strategy.
- **Berkeley MOOC gap**: Notes reference lecture numbers as placeholders. notes/00-pedagogical-research.md:293 self-diagnoses. Either read key lectures or downgrade to 4-source.

## Rejected

No new rejections in session 5.

## Discoveries

| Finding | Source |
|---------|--------|
| CC's methods work because of model co-evolution + infrastructure scale, not just technique | Session 5 brainstorm on why studying CC anatomy doesn't produce CC-quality agents |
| cc-fuel-gauge Phase 3 assumed deterministic compaction; CC TS uses LLM-based | Cross-referencing cc-fuel-gauge-strategy.md with session 4 CC TS finding |
| Berkeley MOOC cross-validation is placeholder, not real — 5-source claim partially unearned | notes/00-pedagogical-research.md:293 self-diagnosis |

## Constraint reasoning

All constraints carried from session 4. No new constraints added.
