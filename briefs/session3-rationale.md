# Session 3 Rationale Log — 2026-04-01

> Key reasoning chains preserved for audit. Not for execution agents.

## Decision evidence

1. **SOP v2 gate pass rate 6/6** — Every reader returned valid JSON matching the prescribed schema. extraction.symbols ≥1 per file read, interpretation.patterns all have evidence + confidence. This validates that JSON schema enforcement works as a quality gate.

2. **11 cross-cutting patterns from Synthesizer** — Patterns span 3-5 readers each. Top: Feature-flag DCE via bun:bundle (Readers 1,3,4,6), Fail-closed security (1,2,4,5), Memoization as architecture (1,3,4,5,6). These are genuinely cross-cutting — no single reader could discover them.

3. **v1 vs v2 needs physical isolation** — User caught that cross-validating TS findings against claw-code 17 patterns is confounded (two variables: source + SOP). For clean comparison, need same codebase, different SOP, different sessions. Multi-session file-based pipeline achieves this.

4. **claude -p single-session failure** — First run-experiment.sh used one `claude -p` for all 6 readers + synthesis. Produced only 2/6 readers then stopped silently. Root cause: too complex for non-interactive mode. Fix: one `claude -p` per reader with resume support.

## Unconfirmed proposals

1. **Operator pipeline formalization** — Session discussed mapping Scout/Reader/Reviewer/Synthesizer to run(storage, in_key, out_key). User said "是" (conceptual agreement) but no implementation done. Would strengthen paper from "practitioner workflow" to "formal composable model with 3-domain validation."

2. **Tree-sitter auto-generated ground truth** — Proposed as Option C for paper standards. Would provide objective symbol coverage metric without human annotation. Not implemented.

3. **LoCoBench-Agent as external benchmark** — Identified as best-fit benchmark (code understanding, not generation). 8000 scenarios, 10K-1M tokens, 17 metrics including ACS and DTA. Not yet run.

## Rejected

1. **Cross-validation of v2 TS findings against claw-code 17 patterns** — User's PUA caught the confound: claw-code patterns extracted with SOP v1 from Python rewrite, TS readers used SOP v2 on original TypeScript. Two variables changed simultaneously. Cannot attribute discovery differences to SOP improvement vs source difference. Need same-codebase comparison.

## Discoveries

| Finding | Source |
|---------|--------|
| CC TS: 1892 files, 513K lines, custom React reconciler + Yoga for terminal UI | Scout + Reader 4 |
| Prompt cache (50-70K tokens) is system-wide architectural invariant | Synthesizer: Readers 1,3,4 |
| Model-calling-model recursion: WebSearch, BASH_CLASSIFIER, memory recall | Synthesizer: Readers 2,3,5 |
| SOP v1 "2000 lines max" needs 256 readers for 513K codebase | PUA review calculation |
| Industry: aider uses tree-sitter repo map, MindStudio uses validated JSON pipeline | Web research (6 sources) |
| claude -p with multi-agent prompt fails silently | Experiment: first script produced 2/6 then stopped |
| CC uses bun:bundle feature() for static DCE — feature flags removed at build time, not runtime | Readers 1,3,4,6 cross-cutting |
| CC security is 9 layers deep with asymmetric allow/deny normalization | Readers 1,2,4,5 cross-cutting |

## Constraint reasoning

- **v1 isolation**: Agent that designed v2 and saw v2 results has confirmation bias. If same agent writes v1 prompts, may unconsciously weaken them (strawman). Physical session isolation via file-based communication eliminates this.
- **Gumroad BLOCK**: DISTRIBUTION.md says "Ship date: end of Week 6." Selling incomplete material kills trust. GumroadReviewer gave 4/10 BLOCK.

## Key metrics from v2 run

| Metric | Value |
|--------|-------|
| Total tokens (6 readers) | 540K |
| Total tool uses | 333 |
| Wall clock (max parallel) | 5.8 min |
| Files read | 189 / 1892 (10%) |
| Lines read | 81K / 513K (16%) |
| Symbols extracted | 200 |
| Patterns found | 45 |
| Surprises | 58 |
| Gate pass rate | 6/6 (100%) |
| Cost | ~$3.00 |
| Synthesizer: cross-cutting patterns | 11 (9 high, 2 medium) |
| Synthesizer tokens | 23K |
| Synthesizer cost | ~$1.00 |

## PUA review of SOP v1 (7 gaps)

1. Scout output spec incomplete — missing reader assignments and must-read list
2. Reader params hardcoded (2000 lines) — doesn't scale
3. Output schema not verifiable — extraction and interpretation mixed
4. Synthesizer has no procedure — "trust the model"
5. Persona layer empty — reader doesn't know its perspective
6. Gate layer empty — no validation between stages
7. Enforcement layer empty — no physical blocking
