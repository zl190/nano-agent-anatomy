# Distribution Plan

One learning session → four outputs. No extra work.

## Pipeline

```
Study session (6h/week)
  │
  ├─ notes/0N-*.md ──────→ GitHub repo (free, SEO + credibility)
  │
  ├─ notes → newsletter ─→ Substack (paid $10/month, curated delivery)
  │                         Format: same notes, light editing, weekly cadence
  │
  ├─ 2 weeks notes → blog → blog.ylab3.com (free, deep dives, portfolio)
  │                          Format: synthesized, with diagrams
  │
  └─ *.py code ──────────→ GitHub repo (free, the "runnable textbook")
```

## Substack Setup

- Name: "Agent Anatomy" or "Inside AI Agents"
- Tagline: "What 513K lines of leaked code taught me about building AI agents"
- Cadence: Weekly (matches study schedule)
- Free tier: Week 1 + Week 4 (hook readers)
- Paid tier ($10/month): All 6 weeks + source code analysis + early access to code
- Each post = that week's learning note + code snippet + one insight

## Content Calendar

| Week | Repo commit | Newsletter | Blog |
|------|-------------|------------|------|
| 0 | Experiment data | "The Structured Approach Lost" (blind A/B on reading methodology) | — |
| 1 | Rewrite loop.py | "The state machine inside QueryEngine.ts" | — |
| 2 | Rewrite memory.py | "Why your agent's memory is lying to you" | "SDK vs leaked source: what Anthropic teaches vs builds" |
| 3 | Rewrite context.py | "Zero LLM calls: how production compresses context" | — |
| 4 | Rewrite coordinator.py | "The prompt that manages other AIs" | "What leaked code taught me about agents" |
| 5 | Integration | "Full pipeline: all 4 layers working together" | "From study to system" wrap-up |

## Gumroad PDF ($10, one-time)

After Week 6, bundle everything into a PDF:
- 6 learning notes (edited)
- 6 code files with inline annotations
- ROADMAP as curriculum guide
- Architecture diagrams

Production: Pandoc/LaTeX from markdown, no manual layout.
Ship date: end of Week 6. Not before — selling incomplete material kills trust.

Two products, two audiences:
- Newsletter ($10/month): follow along weekly, get it as it happens
- PDF ($10 once): buy the finished package after it's done

They don't compete. Newsletter subscribers already paid more. PDF buyers missed the journey but get the result.

## Xiaohongshu (小红书)

Same notes, reformatted for 小红书 audience:
- Chinese, shorter, visual-heavy (screenshots of code + terminal output)
- 1 post per week, timed with newsletter
- Format: carousel (5-8 slides) or short text + code screenshot
- Hook: "拆解泄露的 Claude Code 源码" — controversial enough to get engagement
- Link to repo in bio, newsletter in comments

Content reuse: translate the one-sentence insight from each week's note.
Extra work: ~20 min per post (screenshot + translate hook + format).

## Why This Works

- Newsletter subscribers pay for curation + cadence, not information
- Blog readers get the polished version, 2 weeks later
- GitHub visitors get the code, contribute, and star
- 小红书 readers get the Chinese hook, funnel to repo/newsletter
- PDF buyers get the complete package after Week 6
- All five point to each other
- Total extra work per week: ~50 min (30 min Substack + 20 min 小红书)
