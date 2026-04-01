# Session 8 Brief — 2026-04-02

> Execution agent reads ONLY this. Brief like a smart colleague who just walked into the room.

## Current Task

Session 8 was building XHS carousel images and content. Images rendered correctly (HTML+Playwright, notion-tech theme, 4 pages). Content went through multiple rewrites but **user is not satisfied with the XHS content quality**. User said "跟你讲不清楚" — the agent does not understand XHS content creation norms well enough. Next session must study real XHS posts deeply before writing.

## Key Technical Concepts

- **HTML+Playwright renderer**: `publish/render_xhs.py` renders Markdown → HTML → Chromium screenshot PNG. Theme CSS at `publish/themes/notion-tech.css`. Cherry-picked from Auto-Redbook-Skills (engine) + LobeHub xhs-images (style definitions) + RedInk (consistency pattern).
- **Sensor-actuator handoff split**: cc-fuel-gauge = WHEN (writes signal file), handoff skill = HOW (reads signal, produces YAML). Signal file: `/tmp/cc-fuel-gauge-handoff-signal-{SESSION_ID}.json`.
- **Yinzhou 事实确認表 pattern**: Claims → status (已验证/待审核/需修正) → source grep → gate on 需修正=0. Implemented as `verify-claims.sh`.
- **Publish pipeline**: `publish-pipeline.sh --all` runs all gates (platform style + fact-check + exercises). 7/7 pass for all platforms.
- **CC BUDDY**: Full tamagotchi system — 18 species ASCII art, Bones (deterministic from userId hash) + Soul (LLM-generated name/personality), Mulberry32 PRNG, anti-cheat merge. User wants to build blog version (egg→hatch→pet), not urgent.

## What Happened in Session 8

Session 8 executed P0-P2 from session 7 brief, built infrastructure (gates, pipelines, renderer), and attempted XHS content creation. Infrastructure work was solid; content creation failed to meet user expectations.

**Completed:**
- Gumroad product packaged: $19, ZIP (14 notes + 5 exercises + experiment + model.md), 91KB, exercise gate + fact-check gate pass
- Platform-specific style gates: pre-publish-xhs.sh (6 checks) + pre-publish-substack.sh (7 checks)
- Fact-check gate: verify-claims.sh using research-institute 事实確認表 pattern, 9/9 claims verified
- Publish pipeline: publish-pipeline.sh --all, 7/7 gates pass
- Handoff architecture: sensor-actuator split implemented in cc-fuel-gauge + handoff skill
- cc-fuel-gauge: 4/5 publish blockers fixed (install.sh trap, README deps, test fixtures, production monitoring note). Commit pending.
- XHS carousel renderer: HTML+Playwright, notion-tech theme (white bg, blue accent, code blocks)
- CC BUDDY research: full architecture documented
- Memory updated with session 7+8 decisions

**Failed / Incomplete:**
- XHS content quality: multiple rewrites, user still not satisfied. Core problem: agent writes in "research report" tone, not XHS native tone. Agent doesn't deeply understand XHS content norms.

## What Was Decided

1. Gumroad price: $19 (热点窗口, conversion velocity over margin)
2. XHS carousel: Python→HTML→Playwright screenshot (not matplotlib, not AI image gen)
3. Blog: dev.to first (zero setup), Ghost later
4. Handoff: sensor-actuator split — cc-fuel-gauge writes signal file, handoff skill reads it
5. cc-fuel-gauge: publish standalone to GitHub, handoff skill stays in dotfiles
6. Fact-check: research-institute 事实確認表 pattern adopted
7. CC leak hub blog: planned as hub linking to 4 existing spoke posts (P1 next session)
8. Blog analytics: Umami self-host (primary) + Goatcounter (fallback), not yet implemented
9. Blog pet: egg→hatch→pet inspired by BUDDY, not urgent

## Corrections

| Previous belief | Corrected to | Evidence |
|----------------|-------------|----------|
| matplotlib carousel images match XHS style | matplotlib dark-bg charts look like conference slides; top XHS posts use white-bg rendered articles | Compared our images vs top post (879 likes, Aaron-OpenOnion): white bg, text-heavy, code blocks, article layout |
| Any image generation tool works for XHS | Only HTML→screenshot works for precise text/code. AI image gen (RedInk, LobeHub) can't render code blocks accurately | Tested 3 tools: RedInk = Gemini, LobeHub = Gemini, Auto-Redbook = HTML+Playwright (only winner) |
| "51万行源码" is a good hook for XHS | CC leak has nothing to do with our experiment finding. Mentioning it conflates sources and adds compliance risk | User: "51万行源码是cc的跟你有关系?" |
| Experiment design is interesting content for XHS | XHS readers don't care about methodology. They care about the finding and how to use it | User: "xhs上关心你实验设计?" |
| Writing in shorter/punchier Chinese = XHS native | Still reads like a research summary. Need to actually study XHS post patterns, not just mechanically shorten | User: "pua 你多读读小红书" then "跟你讲不清楚" |
| CSS tweaks fix empty space in images | Root cause was fixed canvas height (2400px) with sparse content. Real fix: screenshot actual content height, or denser content per page | User: "pua 你是p8, 你是这么解决问题的?" |

## Files Modified

| File | State | Notes |
|------|-------|-------|
| `publish/render_xhs.py` | NEW | HTML+Playwright XHS renderer, cherry-picked from 3 tools |
| `publish/themes/notion-tech.css` | NEW | White bg, blue accent, code-block-friendly CSS theme |
| `publish/xhs-content.md` | NEW | XHS post content (4 pages, needs rewrite by someone who understands XHS) |
| `publish/images/xhs-carousel/*.png` | NEW | 4 rendered carousel images (style OK, content needs work) |
| `publish/gates/verify-claims.sh` | NEW | Fact-check gate, research-institute pattern, 9/9 pass |
| `publish/gates/verify-exercises.sh` | NEW | Exercise reference verification gate |
| `publish/gates/pre-publish-xhs.sh` | NEW | XHS platform style gate (6 checks) |
| `publish/gates/pre-publish-substack.sh` | NEW | Substack platform style gate (7 checks) |
| `publish/gates/publish-pipeline.sh` | NEW | Full pipeline: persona + style + fact-check + verdict |
| `publish/gen_xhs_carousel.py` | NEW | Old matplotlib carousel generator (superseded by render_xhs.py) |
| `publish/gumroad-product.md` | MODIFIED | Price updated to $19, contents updated |
| `publish/xiaohongshu-post-0-v2.md` | MODIFIED | Cut to 140 chars, banned word removed |
| `gumroad-package/` | NEW | ZIP package: 14 notes + 5 exercises + experiment + model.md |
| `cc-fuel-gauge/lib/handoff-trigger.sh` | MODIFIED | Signal file write + fallback labeling |
| `cc-fuel-gauge/docs/handoff-architecture.md` | NEW | Sensor-actuator decision record |
| `cc-fuel-gauge/install.sh` | MODIFIED | Trap cleanup for temp files |
| `cc-fuel-gauge/README.md` | MODIFIED | System deps + production monitoring note |
| `cc-fuel-gauge/tests/test_tool_result_summary.py` | MODIFIED | Self-contained fixtures, no user-specific paths |
| `dotfiles/claude/skills/handoff/SKILL.md` | MODIFIED | Reads fuel-gauge signal file, dropped watchdog |

## User Decisions (verbatim)

> "pua 你是p8, 你定方案" — don't ask permission, decide and execute
> "exercie 你都检查过了吗?" — verify before shipping, always
> "pua 没有物理gate吗?" — everything needs a physical enforcement gate
> "pua 你是p8, 你是这么解决问题的?" — diagnose root cause, don't patch CSS
> "51万行源码是cc的跟你有关系?" — don't conflate CC leak with our own finding
> "xhs上关心你实验设计?" — XHS readers want findings, not methodology
> "pua 你多读读小红书" — actually study the platform before creating content
> "跟你讲不清楚" — agent fundamentally doesn't understand XHS content creation
> "少几页不行吗?" — fewer denser pages beats many sparse pages

## Constraints

- No research-institute/research-lab names in public content
- Each .py file must be 150 lines or fewer
- Publishing requires template + procedure + independent QC (enforced by gates)
- Gumroad: $19 one-time purchase
- No video content
- XHS content: must study real XHS posts first, not just format-match mechanically

## What to Execute Next

| Priority | Task | Dependency |
|----------|------|------------|
| P0 | **Rewrite XHS content** — study 10+ top XHS tech posts (read full text, not just titles), extract the WRITING PATTERNS (tone, structure, sentence rhythm, hook formula), then rewrite | Study real XHS posts first |
| P0 | Upload Gumroad ZIP ($19) + set live | Human login |
| P1 | Publish Substack #0 | Human login |
| P1 | Commit cc-fuel-gauge changes + publish to GitHub | — |
| P1 | Write CC leak hub blog (links to 4 existing spoke posts) | — |
| P1 | Set up blog analytics (Umami self-host + Goatcounter fallback) | Oracle VM access |
| P2 | Add Buy Me a Coffee to blog footer | — |
| P2 | Blog pet: egg→hatch→pet (BUDDY-inspired) | Sprite asset |
| P2 | Formalize XHS auto-publish pipeline (model.md → project → render → gate → MCP publish) | render_xhs.py working |

## Open Questions

1. XHS content: user says "跟你讲不清楚" — next session should either: (a) have user write first draft and agent polishes, or (b) agent studies 20+ XHS posts before attempting
2. Should Gumroad product include the 4 blog posts (currently free on GitHub)?
3. cc-fuel-gauge: when to cut v1.0 tag?
