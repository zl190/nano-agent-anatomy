# nano-agent-anatomy — Resume Point

> Read the latest brief, execute from there.
> Rationale logs exist for audit — read only when a decision is questioned.

## Three-Layer Handoff Structure

briefs/session7-brief.md      <- Layer 1: READ THIS.
briefs/session7-rationale.md  <- Layer 2: On demand.
session.jsonl                 <- Layer 3: Auto-saved. Forensic only.

## Latest Session

**Session 7** — 2026-04-02 — `briefs/session7-brief.md`

## Session Index

| Session | Date | Brief | Key Outcome |
|---------|------|-------|-------------|
| 7 | 2026-04-02 | session7-brief.md | QC all deliverables, CC enforcement gates, business model restructure (code open / analysis paid), force push clean history, 95 tests |
| 6 | 2026-04-01 | session6-brief.md | Source audit (5 sources), 4 blogs, Unit 6+gap doc, context pollution proposal, handoff v2.2 |
| 5 | 2026-04-01 | session5-brief.md | All P0: 15 code progression, 76 tests, 5 exercises, 6 notes, Unit 5 |

## Critical Corrections (check before acting)

| Wrong | Right | Source |
|-------|-------|--------|
| Everything on GitHub = good open source | Code open + analysis paid = differentiation | Session 7 content strategy |
| Tests pass = code works | Need functional tests against real API | Session 7 E2E testing |
| 小红書 images = illustrations | Images ARE the content (8-10 carousel pages) | Session 7 top post analysis |
| Framework rules = enforcement | Must use CC physical gates (exit 2) | Session 7 gate implementation |
| "泄露" is fine in Chinese content | Compliance risk on 小红書 | Session 7 XHS QC |

## Constraints (cumulative)

- No research-institute/research-lab names in public content
- Each .py file must be 150 lines or fewer
- Publishing enforced by gates (pre-publish.sh, pre-push.sh)
- Gumroad one-time purchase, not subscription
- No video content
- 小红書 = market signal testing only, no direct Gumroad links
- Full notes backup: `~/Developer/personal/nano-agent-anatomy-notes-full/`

## Resume Command

read ~/Developer/personal/nano-agent-anatomy/briefs/session7-brief.md then execute next steps
