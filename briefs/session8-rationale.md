# Session 8 Rationale Log — 2026-04-02

> Key reasoning chains preserved for audit. Not for execution agents.

## Decision evidence

- **Gumroad $19**: User said "蹭热点" (session 7) — time-sensitive, lower price = faster conversion. $10 (original) too low, $29 risks friction.
- **Sensor-actuator handoff**: cc-fuel-gauge has real token measurement; handoff skill has conversation context. Neither can do both. Signal file `/tmp/cc-fuel-gauge-handoff-signal-{SESSION_ID}.json` is the contract.
- **HTML+Playwright for XHS**: Tested 3 tools — RedInk (Gemini AI gen, can't render code accurately), LobeHub xhs-images (Gemini AI gen, same problem), Auto-Redbook-Skills (HTML+Playwright, precise text). Only Auto-Redbook works for technical content.
- **Yinzhou fact-check pattern**: User pointed to ~/Downloads/research-institute project. 事实確認表 has 81 claims, 6 categories, status taxonomy. Applied as verify-claims.sh.
- **Content-fit height**: Originally used fixed 2400px canvas → empty bottom half. User called out "你是p8,你是这么解决问题的". Root cause: `max(height, actual_height)` forces minimum 2400px. Fix: `max(actual_height, width)` = minimum 1:1 ratio, grow with content.
- **4 pages not 8**: User said "少几页不行吗". 8 pages × ~100 chars each = too sparse. Hot posts have 5000+ chars across 18 pages. Our content fits 4-5 dense pages.

## Unconfirmed proposals

- CC leak hub blog as "hub" linking to 4 spoke posts — discussed, user seemed positive but no explicit confirmation
- n8n for workflow orchestration — user raised as analogy, concluded CC hooks are the equivalent ("CC 有没有管线" → "hooks 就是管线")
- Blog pet egg→hatch→pet — user said "好玩" and "不急", listed features to steal from BUDDY, but no "做" instruction

## Rejected

- Optimizing the publish pipeline further ("我们需要优化吗" → "不需要。先发出去。")
- Publishing cc-fuel-gauge and handoff skill together ("分开发")
- AI image generation (Gemini) for XHS carousels — can't render code blocks accurately

## Discoveries

| Finding | Source |
|---------|--------|
| Top XHS tech posts are rendered articles (white bg, text-heavy, code blocks), not data dashboards | Downloaded and viewed covers from top 2 search results (879 likes, 160 likes) |
| CC BUDDY is a full tamagotchi: 18 species, Bones/Soul anti-cheat split, Mulberry32 PRNG, CLI Ink component | Web research + source analysis |
| Auto-Redbook-Skills uses HTML+Playwright (only tool with precise rendering); RedInk and LobeHub both use Gemini AI image gen | Cloned and analyzed all 3 repos |
| CC hooks system IS the pipeline (event-driven middleware), making publish-pipeline.sh redundant for enforcement (but useful for dry-run audit) | User insight: "CC 有没有管线" |
| XHS content creation requires deep platform understanding, not mechanical format matching | User frustration across multiple rewrites |

## Constraint reasoning

- "Study XHS posts first": Session 8 showed that format-matching (dimensions, char count, banned words) passes gates but doesn't produce content users actually want to read. The missing layer is understanding XHS writing NORMS — sentence rhythm, hook formulas, tone, what counts as "interesting" on the platform.
