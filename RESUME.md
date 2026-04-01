# nano-agent-anatomy — Resume Point

> Read the latest brief, execute from there.
> Rationale logs exist for audit — read only when a decision is questioned.

## Three-Layer Handoff Structure

briefs/session6-brief.md      ← Layer 1: READ THIS.
briefs/session6-rationale.md  ← Layer 2: On demand.
session.jsonl                 ← Layer 3: Auto-saved. Forensic only.

## Latest Session

**Session 6** — 2026-04-01 — `briefs/session6-brief.md`

## Session Index

| Session | Date | Brief | Key Outcome |
|---------|------|-------|-------------|
| 6 | 2026-04-01 | session6-brief.md | Source audit (5 sources), 4 blogs, Unit 6+gap doc, context pollution proposal, handoff v2.2 |
| 5 | 2026-04-01 | session5-brief.md | All P0: 15 code progression, 76 tests, 5 exercises, 6 notes, Unit 5 |
| 4 | 2026-04-01 | session4-brief.md | Experiment (v1 wins 6-1), SOP v3, competitive research, ROADMAP V2 |
| 3 | 2026-04-01 | session3-brief.md | SOP v2 on CC TS, experiment designed + partially run |
| 2 | 2026-04-01 | session2-brief.md | claw-code source, 17 patterns, code+notes rewrite |
| 1 | 2026-04-01 | session1-brief.md | Repo created, distribution design, publish content |

## Critical Corrections (check before acting)

| Wrong | Right | Source |
|-------|-------|--------|
| Compaction is deterministic | CC TS uses LLM prompt (claw-code is simplified) | compact/prompt.ts |
| Agent SDK is a framework | SDK is a control protocol over CC CLI binary | subprocess_cli.py |
| "9-section compaction" is cross-validated | Internal implementation only; official docs say 5 categories | Anthropic eng blog |
| "Anthropic Academy" is a source | Academy too basic; "Anthropic Docs & Eng Blog" is the real source | session 6 audit |
| Berkeley MOOC covers context compression | Zero coverage across 3 semesters (F24, S25, F25) | mooc-researcher × 2 |
| Subagents can spawn sub-agents | CC hard limit: subagents cannot spawn subagents | Tested 3 ways + docs |

## Constraints (cumulative)

- No research-institute/research-lab names in public content
- Each .py ≤ 150 lines
- Publishing requires template + procedure + independent QC
- Gumroad BLOCKED until course complete
- Handoff includes corrections section (session 4 lesson)

## Resume Command

read ~/Developer/personal/nano-agent-anatomy/briefs/session6-brief.md then execute next steps
