# Session 11 Brief — 2026-04-02

> Execution agent reads ONLY this. Brief like a smart colleague who just walked into the room.

## Current Task

None in progress. Full launch completed this session.

## Key Technical Concepts

- **enforcement vs evaluation**: CC has 3 layers for safety (enforcement), zero for quality (evaluation). Quality investment is in model training (RLHF, constitutional AI), not in CC wrapper. The original "安全>>质量" claim was wrong — corrected to this framing in XHS v5.
- **pre-package gate**: `publish/gates/pre-package-gumroad.sh` — automated checks (markers, paths, references, counts, stale labels) must pass before zip. Now wired into PreToolUse hook.
- **preview = 2x scrutiny**: Free preview file is the most important in a paid product. 01-tool-loop.md had the MOST factual errors — every number must be grep-verified.
- **launch funnel**: Free repo → HN/Reddit/Twitter drive traffic → repo README links to Gumroad ($19). Never sell directly on HN.
- **Gumroad product**: "Agent Anatomy" at yclab.gumroad.com/l/agent-internals, $19, 20 markdown files, 86KB zip.

## What Was Decided

1. XHS v5 uses enforcement/evaluation framing (not "安全>>质量")
2. Gumroad product name "Agent Anatomy", $19, digital product
3. Twitter thread posted (6 tweets from @yclab3)
4. Reddit r/ClaudeAI post submitted (awaiting mod approval)
5. Blog: Buy Me a Coffee icon in left sidebar (buymeacoffee.com/ylab3)
6. Blog: Cloudflare Web Analytics (automatic, no code)
7. cc-fuel-gauge pushed with sensor-actuator handoff architecture
8. Gumroad package passed 2 independent QC rounds (25 issues total, all fixed)
9. 3 new hooks in settings.json (pre-package-gate, publish-gate, preview-scrutiny)
10. 7 failure patterns documented as rules in memory

## Corrections

| Previous belief | Corrected to | Evidence |
|----------------|-------------|----------|
| "安全>>质量, Anthropic不管质量" | CC应用层有enforcement没有evaluation。质量在模型层。 | RLHF/constitutional AI是质量投入；hooks是quality基础设施 |
| 05-local-router.md是早期规划 | 打包agent hallucinate的。CC没有local router。 | git log只在gumroad commit出现。CC用per-agent model override不是routing。 |
| max_turns=25, max_budget_tokens=0 | max_turns=8, max_budget_tokens=2000 | grep claw-code source直接验证 |
| conversation.rs 585行, 350+测试 | 584行, 188个#[test] | wc -l和grep -rc验证 |
| "compile-time constant" | Runtime configurable via with_max_iterations() builder | Source code shows pub fn with_max_iterations() |

## Files Modified

| File | State | Notes |
|------|-------|-------|
| `publish/xhs-content-v5.md` | NEW | Corrected enforcement/evaluation framing |
| `publish/gumroad-listing.md` | NEW | Product description for Gumroad |
| `publish/launch-posts.md` | NEW | HN + Reddit + Twitter content |
| `publish/reddit-r-claudeai.md` | NEW | Standalone Reddit post |
| `publish/twitter-thread.md` | NEW | 6-tweet thread |
| `publish/gates/pre-package-gumroad.sh` | NEW | Automated pre-package QC gate |
| `publish/gates/pre-publish-reddit.sh` | NEW | Reddit format gate |
| `publish/gates/pre-publish-twitter.sh` | NEW | Twitter thread gate |
| `preview/01-tool-loop.md` | NEW | Free sample for repo |
| `preview/experiment-report.md` | NEW | Free sample for repo |
| `gumroad-package/` | MODIFIED | 25 QC fixes across 2 rounds |
| `README.md` | MODIFIED | Added preview section + Gumroad link |
| Blog `SocialLinks.tsx` | NEW | GitHub + BMC icons in sidebar |
| Blog `quartz.layout.ts` | MODIFIED | Sidebar links, footer reverted |
| cc-fuel-gauge | MODIFIED | Sensor-actuator split, 14 tests |
| `~/.claude/settings.json` | MODIFIED | 3 new hooks |

## User Decisions (verbatim)

> "别管科技博主了, 我们准确接小红书的地气再有点自己的特点就行了" — XHS voice direction
> "pua 你是p8, 你定方案" — delegated all product decisions
> "I've been reading all 513K lines — 这句删了可以吗, 没人信你一天把513k lines 全看了" — credibility check, changed to factual framing

## Constraints

- No research-institute/research-lab names in public content
- Each .py file ≤ 150 lines
- Every number in product files must be grep-verified against source
- QC gate mandatory before any packaging or publishing
- Preview files get 2x scrutiny

## What to Execute Next

| Priority | Task | Dependency |
|----------|------|------------|
| P0 | Monitor Reddit mod approval + Twitter engagement | — |
| P1 | HN: register account, build karma, then Show HN | HN karma |
| P1 | Run publish gates on 4 blog posts before publishing | — |
| P1 | Calibrate XHS persona with user's voice, produce final version | User samples |
| P2 | Add cheatsheet to Gumroad package | — |
| P2 | Restructure Gumroad listing (discrepancies first) | — |
| P2 | Add $0 Gumroad tier for email capture | — |
| P2 | Register platform-style-hook.sh in settings.json | — |
| P3 | Build last30days → XHS auto-publish pipeline | last30days + XHS MCP |

## Open Questions

1. 4篇blog是走全景框架和发布管线吗？答：session 7跑了内容QC（DCAR审计），没过format gate（当时不存在）。发之前要补跑。
2. Gumroad launch-week pricing $19→$29 after April 9？用户未确认具体日期。
3. XHS内容什么时候定稿？v5 framing对了但voice还没校准。
