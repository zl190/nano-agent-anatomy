# nano-agent-anatomy — Resume Point

> Read the latest brief, execute from there.
> Rationale logs exist for audit — read only when a decision is questioned.

## Three-Layer Handoff Structure

briefs/session22-brief.md      <- Layer 1: READ THIS.
briefs/session22-rationale.md  <- Layer 2: On demand.
session.jsonl                  <- Layer 3: Auto-saved. Forensic only.

## Latest Session

**Session 22** — 2026-04-03 — `briefs/session22-brief.md`
Profile: wide, 6done/2new, prior_handoff_quality: 4.3/5

## Session Index

| Session | Date | Brief | Rationale | Profile | Summary |
|---------|------|-------|-----------|---------|---------|
| 22 | 2026-04-03 | session22-brief.md | session22-rationale.md | wide 6/2 q:4.3 | Execution: 3 SKILL fixes + 2 blog drafts + symlink. Dotfiles pushed. |
| 21 | 2026-04-03 | session21-brief.md | session21-rationale.md | wide 7/9 q:3.7 | Audit-driven: 4 opus auditors, 9/14 REVISE fixed. 11/11 papers+synthesis. SRP+system-map+handoff v2.3. |
| 20 | 2026-04-03 | session20-brief.md | session20-rationale.md | wide 8/3 | Executed session 19 backlog. Trust-damaging errors. |
| 19 | 2026-04-02 | session19-brief.md | session19-rationale.md | — | Statusline, system-context, Design Stage Guard, dual-QC, noGlaze v0.2 |

## Constraints (cumulative)

- No research-institute/research-lab names in public content
- QC gate mandatory before publishing (dual QC: mechanical + persona)
- Never modify settings.json mid-session
- Agent-produced artifacts are claims, not facts
- All hook JSONL logging must use `jq -cn --arg`

## Top-Level Architecture

For the full system map (12 ideas + connections): `~/.claude/memory/knowledge/system-map.md`

## Resume Command

read ~/Developer/personal/nano-agent-anatomy/briefs/session22-brief.md then execute next steps
