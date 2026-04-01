# Content Strategy Research: GitHub + Substack + 小红书 Differentiation

Date: 2026-04-02

## The Problem

nano-agent-anatomy is fully open source: code, experiment data, learning notes, blog posts, and methodology are all on GitHub. If a reader can get everything for free, what is Substack for? And if Substack is free, what would justify charging later?

---

## Part 1: How Successful Technical Newsletters Coexist with Open Repos

### Simon Willison (simonwillison.net + simonw.substack.com)

**Model:** Everything free. Newsletter is a delivery mechanism, not a paywall.

- Blog: All content lives on simonwillison.net (Django + PostgreSQL). Every post is free, forever.
- Substack: Weekly-ish digest that repackages blog content for email delivery. Free.
- Paid tier: $10/month GitHub Sponsors get a monthly curated summary of the most important trends. He calls this "paying him to send you less" — the value is curation, not exclusive content.
- Sponsorship: Unobtrusive weekly banner on blog + top of newsletter. No sponsored content.
- Open source: Datasette, llm, sqlite-utils — all fully open. The newsletter discusses them but never gates them.

**What they sell:** Curation of a prolific output stream. Simon publishes so much (often daily) that the paid monthly summary is genuinely useful. The volume creates the need for the filter.

**Relevance to you:** Low. Simon's model works because his output volume is extreme (300+ posts/year). You publish weekly. There's not enough volume to make "paying for curation" work at your scale.

### The Pragmatic Engineer (Gergely Orosz)

**Model:** Hard paywall on most content. No open repo.

- Free: One full article per month + first half of paid articles as preview.
- Paid ($15/month, $150/year): Full deepdives on Tuesdays + "The Pulse" on Thursdays (industry analysis). ~4x the content of free tier.
- No advertising, no sponsorships. Revenue is 100% subscriptions.
- Reduced rates for non-US/EU readers + student discounts.
- No open source component.

**What they sell:** Insider access. Gergely interviews engineers at Google, Stripe, Uber about how things actually work internally. His competitive advantage is his network — you cannot replicate his sourcing by reading public repos.

**Relevance to you:** Medium-high. The structure is instructive: free tier gives a taste (half-articles), paid tier gives the full thing. But Gergely's moat is access to people. Your moat is access to a process (your reading methodology, your experiment data, your correction log). Different asset, same structure.

### ByteByteGo (Alex Xu)

**Model:** Free newsletter + paid course product.

- Newsletter: Originally free forever (sponsorship-funded). Later added a paid tier ($10/month) with extra Wednesday deep dives.
- Free: Saturday issue with system design diagrams.
- Paid: Wednesday deep dive + full course access on bytebytego.com.
- GitHub: No public repo of course content. The diagrams are the product.
- Revenue: Mixed — newsletter sponsorships + course subscriptions.

**What they sell:** Visual explanations of complex systems. The diagrams (system design cheat sheets) are the irreplaceable asset — they take significant effort to produce and are the thing people share on LinkedIn.

**Relevance to you:** Medium. Alex's visual assets (diagrams) serve the same role your experiment data could serve — they're the thing that took real effort and can't be replicated by reading the text. Your blind experiment scoring tables, the code progression diffs (v0 -> v3), the cross-validation discrepancy maps — these are your "diagrams."

### Latent Space (swyx + Alessio)

**Model:** Free podcast + mixed Substack.

- Podcast: Free on all platforms. Weekly interviews with AI leaders.
- Substack: Includes AI News (daily/frequent), podcast episodes (weekly), essays (occasional). Some content is paid-subscriber-only.
- Paid tier: Supports operations. Benefits include some exclusive content.
- GitHub: No primary repo — the content IS the product.

**What they sell:** Network + synthesis. swyx and Alessio talk to the people building AI, then synthesize across conversations. The value is the cross-pollination across guests — patterns you wouldn't see from reading any single source.

**Relevance to you:** High on synthesis, low on network. Your cross-validation methodology (reading the same concept across 4 sources and mapping where they disagree) is structurally similar to what Latent Space does across interviews. You synthesize across codebases; they synthesize across people.

### Lenny's Newsletter (Lenny Rachitsky)

**Model:** Hard paywall on most content.

- Free: 1 issue per month + previews of paid posts.
- Paid ($15/month, $150/year): Weekly deep dives + Slack community + product perks (free Perplexity Pro, Kagi, etc.).
- "I Can Expense It" tier at $300/year.
- Revenue: From $56K ARR in month 1 to $360K+ ARR by year end.

**What they sell:** Practitioner's playbook. Lenny packages what product managers actually do at successful companies into repeatable frameworks. His Slack community creates network effects — paid subscribers help each other.

**Relevance to you:** Low-medium. The community model is premature for your audience size. But the "I Can Expense It" tier is worth noting — if your audience includes engineers at companies with L&D budgets, pricing at $10-15/month is within expense-report territory.

### Ahead of AI (Sebastian Raschka)

**Model:** Free most content + paid tier for bonus.

- Free: Most articles. 175K+ free subscribers.
- Paid ($6/month, $60/year): Early access, occasional bonus articles, curated paper lists. ~30K paid subscribers.
- Open source: Raschka maintains several popular repos (though not directly tied to newsletter content).
- The newsletter is deep technical analysis of ML papers and architectures.

**What they sell:** Expert curation and synthesis of ML research. Raschka's academic credibility (PhD, author of ML textbooks) is the trust anchor. The paid tier is a "tip jar with benefits" — most content is free, paying is about supporting and getting small extras.

**Relevance to you:** HIGH. This is the closest analog to your situation. Raschka has open source repos, publishes most content free, and charges for curation + extras. The key difference: Raschka's authority comes from his credential (PhD, published author). Your authority comes from your methodology (blind experiments, correction tracking, cross-validation).

---

## Part 2: What Makes Content Worth Paying For (Patterns Across All Six)

Five value types emerged from the research, sorted by how well they match your project:

### 1. Process Narration ("Watch me think")
Nobody else studied has this. Gergely reports what others built. Alex diagrams how systems work. Raschka explains papers. But none of them run blind experiments on their own methodology and publish the results, including when they're wrong. Your correction-first philosophy ("I was wrong to stuff both into one format") is genuinely rare.

**Your version:** The learning journal as it happens — hypotheses stated before reading, predictions vs. reality, what you got wrong and why. This is not available on GitHub because GitHub has the finished notes, not the thinking that produced them.

### 2. Synthesis Across Sources ("Where they disagree")
Latent Space does this across people. You do this across codebases. Your C9 claim (4-source cross-validation discrepancy map) is the highest-value uncovered asset in your model.md — and it has no dedicated projection yet.

**Your version:** The cross-validation comparison tables. "claw-code says X, CC TS says Y, Academy says Z — here's why they disagree and what the disagreement teaches you."

### 3. Curated Delivery ("I read it so you don't have to")
Simon Willison's entire paid model. ByteByteGo's diagrams. Raschka's paper summaries.

**Your version:** You read 513K lines of TypeScript. The reader doesn't have to. But the GitHub repo already provides this for free. The newsletter version must add something the repo doesn't — narration, sequence, pacing.

### 4. Community/Access ("Talk to people like you")
Lenny's Slack. Pragmatic Engineer's network effects.

**Your version:** Premature at current scale. Don't attempt until 500+ subscribers.

### 5. Visual/Reference Assets ("The thing I bookmark")
ByteByteGo's diagrams. Raschka's paper summaries.

**Your version:** The scoring tables, the code progression diffs, the architecture comparison charts. These exist in the repo as Markdown but could be formatted as shareable visual assets.

---

## Part 3: Recommended Strategy for nano-agent-anatomy

### Core Principle: GitHub is the Artifact. Substack is the Journey.

The GitHub repo contains finished artifacts: code files, learning notes, experiment reports, blog posts. These are static. They represent what was learned.

The Substack newsletter contains the journey of learning: hypotheses stated in advance, predictions that were wrong, corrections made, the "why" behind each decision. These are temporal. They represent how it was learned.

This is the differentiation that none of the six newsletters above uses in exactly this way, because none of them study their own process as a primary subject.

### Strategy 1: The Prediction-Before-Reading Format (Unique to You)

**What it is:** Every Substack issue starts with a stated prediction about what the production source will reveal, made BEFORE reading. Then the issue walks through what actually happened, with the delta explicitly scored.

**Example for Issue #1 (tool loop):**

> **My prediction before reading QueryEngine.ts:**
> - The tool loop is a simple while loop with a tool_use check (confidence: 90%)
> - There's some kind of max iteration guard (confidence: 70%)
> - Error handling is try/catch around tool execution (confidence: 60%)
>
> **What I actually found:**
> - The while loop: correct, but it's a state machine, not a simple loop (90% -> partial match)
> - Max iterations: correct, hard ceiling at 16 (70% -> confirmed)
> - Error handling: WRONG. Permission check happens BEFORE execution, not after. Denied tools return is_error=True with the denial reason — the loop continues, it doesn't catch an exception (60% -> rejected)
>
> **Calibration score this week: 1 correct, 1 partial, 1 wrong.**

**Why this can't live on GitHub:** The repo has loop_v0.py through loop_v3.py and notes/01-tool-loop.md. Those are the outcome. The prediction-before-reading format is the process. It's ephemeral — once you've read the source, you can't un-read it. The Substack issue captures the moment of not-knowing-yet that the GitHub note can never reconstruct.

**Why this is worth paying for:** Calibration is a skill. Watching someone systematically predict, get it wrong, and adjust teaches calibration by example. No other AI agent newsletter does this.

### Strategy 2: The Correction Log (Your Existing Strength, Underexploited)

**What it is:** A running correction log across issues. Each issue includes a "Corrections from previous issues" section where you fix things you got wrong.

**Example:**

> **Corrections from Issue #0:**
> - I said "lost 6 to 1" in the lede. More precisely: preferred on 5 of 6 readers + the synthesis. The "6-to-1" framing is technically defensible but misleading. Fixed.
> - I conflated the 2.2x named symbol count (automated metric) with the Extraction Completeness Likert score (+0.33). These measure different things. Fixed.

**Why this can't live on GitHub:** Git commits show file diffs. They don't explain WHY a change was made or what the author got wrong. The correction log is editorial narration on top of the diff.

**Why this is worth paying for:** Corrections are the highest-signal content in any technical publication. Most newsletters never correct themselves. Yours does it as a feature, not a bug.

### Strategy 3: The Cross-Validation Comparison (Your C9 Gap)

**What it is:** Dedicated issues that map the same concept across all 4 sources, with a comparison table showing where they agree and disagree.

**Example issue: "What Four Sources Say About Memory"**

| Aspect | CC TypeScript | claw-code | Anthropic Docs | Agent SDK |
|--------|-------------|-----------|----------------|-----------|
| Architecture | 2-layer: MEMORY.md + per-file | Same (memdir/) | "memory flag" | `memory` parameter |
| Consolidation | autoDream: Orient-Gather-Consolidate-Prune | Same | Not documented | Not exposed |
| Search | 256-token semantic side call | Not implemented | Not documented | Not exposed |
| Gap | What SDK hides | What Rust simplifies | What docs skip | Surface only |

> **The insight:** The SDK exposes a boolean. The TypeScript source has a 4-phase consolidation algorithm. The Rust port simplifies it. The docs pretend it's simple. Each source teaches a different lesson. The disagreement IS the lesson.

**Why this can't live on GitHub:** The individual notes (notes/02-memory.md) cover each source. But no file in the repo synthesizes all four into a single comparison view. This synthesis is editorial work.

**Why this is worth paying for:** This is the "discrepancy map" your model.md calls "the gold." It's the most labor-intensive content you produce and the hardest to replicate.

### Strategy 4: Chinese-First Deep Dives for 小红书 -> Substack Funnel

**What it is:** Write select issues in Chinese first (not translated from English), covering the same concepts but for a Chinese developer audience.

**Example for 小红书:**
- Post: 5-slide carousel with the Memory comparison table (visual, scannable)
- Hook: "Anthropic SDK 文档说 memory 是一个 bool。源码里是 4 阶段算法。文档在骗你。"
- CTA: "完整对比表在 newsletter 里" (link in comments)

**Example for Substack (Chinese issue):**
- Full comparison table with code examples
- Chinese-native explanation of why the discrepancy matters
- Link to English version for bilingual readers

**Why this works:** There is virtually no Chinese-language content doing source-level analysis of production AI agent architectures. The 小红书 posts are hooks; the Substack issue is the payload. This is a separate funnel from the English audience.

### Strategy 5: The "What I'd Do Differently" Retrospective

**What it is:** Every 4 issues, publish a retrospective: what you learned about your own learning process, what you'd change if starting over, and what's still open.

**Example (after Issues 0-3):**

> **What I'd do differently:**
> - Read the Rust port (claw-code) FIRST, not the TypeScript. The simplified version gives you the mental model; the production version gives you the details. I went production-first and got lost in 513K lines before I had a map.
> - Don't run the blind experiment on all 6 subsystems at once. Run it on 2, check calibration, THEN scale. I wasted $3 on a v2 run that was DOA by subsystem 3.
>
> **What's still open:**
> - SOP v3 (dual-channel) is not validated. The next experiment is planned but not run.
> - The correction-aware microcompact (context_v4.py) is a prototype. It works on keyword matching. That's fragile.

**Why this can't live on GitHub:** The repo doesn't have a "hindsight" section. The notes are written in the order of discovery, not in the order of understanding.

**Why this is worth paying for:** Retrospectives from someone who tracks their own errors are rare. Most technical content presents the final understanding. This presents the path, including the dead ends.

---

## Part 4: Concrete Content Routing

### GitHub (stays free, always)

- All `.py` code files (loop_v0 through coordinator_v3)
- All learning notes (notes/01 through notes/09)
- All experiment data (experiment/ directory)
- All blog posts (publish/blog-*.md)
- README, ROADMAP, tests, exercises
- **Role:** SEO, credibility, "show your work," portfolio piece

### Substack Free Tier

- Issue #0 (the experiment story — your best hook)
- Every 4th issue (hooks for the retrospective cycle)
- First half of cross-validation comparison issues (Pragmatic Engineer model: preview the table, paywall the analysis)
- All correction logs (build trust with free readers too)
- **Role:** Acquisition. Give enough that free readers tell others about you.

### Substack Paid Tier ($8/month or $80/year)

Don't launch this until you have at least 200 free subscribers and 8+ published issues. Launching paid before you have an audience costs you nothing in revenue (you'd convert ~0 people) and risks signaling "this is a business" before you've earned trust.

When you do launch paid:

- Full prediction-before-reading format (the prediction, the reading, the delta, the calibration score)
- Full cross-validation comparison issues (all 4 sources, complete table + analysis)
- Retrospectives every 4 issues
- Early access to blog posts (2 weeks before they go to GitHub/blog)
- The "What Production Does That We Don't" gap analysis in narrative form (not just the bullet points in the repo)

**Pricing rationale:** $8/month ($80/year) is below Pragmatic Engineer ($15) and Lenny ($15) but above Raschka ($6). Your audience is niche (AI agent builders who want production-level understanding, not tutorials). Niche + high-intent = price above $5 floor. But you have no established brand yet = don't price at $15.

### 小红书 (Chinese audience funnel)

- Carousel posts (5-8 slides): visual versions of comparison tables, experiment results, code progression diffs
- Hook format: "X文档说Y。源码里其实是Z。" (What docs say vs. what code does — controversy drives engagement)
- CTA: Always points to newsletter (评论区), never directly to GitHub (GitHub is foreign to 小红书's audience)
- Cadence: 1 post per week, synced with Substack issue but reformatted, not translated
- Chinese Substack issues: 1 per month, longer-form, for the audience that upgraded from 小红书
- **Role:** Top of funnel for Chinese developers. Convert to newsletter subscribers, not GitHub stars.

---

## Part 5: What NOT to Do

1. **Don't paywall code or experiment data.** Your credibility comes from open methodology. The moment you gate the experiment report behind a paywall, you lose the "show your work" advantage that differentiates you from every other AI newsletter.

2. **Don't launch paid before Issue #8.** You need a corpus of free issues that proves the format works. Launching paid on Issue #1 signals desperation, not confidence.

3. **Don't translate between English and Chinese.** Write natively in each language. The 小红书 audience needs Chinese-native framing, not translated English. The Substack English audience doesn't need Chinese cultural context. Two audiences, two voices, one source of truth (model.md).

4. **Don't compete with Raschka on paper summaries or with ByteByteGo on diagrams.** Your unique asset is the process documentation: predictions, corrections, cross-validation, calibration. Nobody else does this. Double down on it.

5. **Don't add a Slack/Discord community yet.** Wait until 500+ subscribers. Premature community creation means you'll be the only one talking, which looks worse than no community at all.

---

## Part 6: Implementation Sequence

```
NOW (Issue #0-#3, April-May 2026):
  - Publish Issue #0 on Substack (free)
  - Publish 小红书 post #0 (already done)
  - Issues #1-#3: free, establish the prediction-before-reading format
  - Start correction log from Issue #1
  - DO NOT launch paid tier

MONTH 2 (Issue #4-#7, May-June 2026):
  - Issue #4: First retrospective (free — hooks new readers)
  - Issues #5-#7: Continue building corpus
  - First cross-validation comparison issue (Issue #5 or #6)
  - Chinese Substack issue: translate the retrospective
  - Assess subscriber count. If <200 free, keep everything free.

MONTH 3+ (Issue #8+, June+ 2026):
  - If 200+ free subscribers: launch paid tier at $8/month
  - Paywall: full prediction format + full comparison issues + retrospectives
  - Free tier: every 4th issue + correction logs + first half of comparisons
  - 小红书: continue weekly, start linking to paid Substack in CTA
  - Consider Gumroad PDF bundle after all units complete
```

---

## Summary: The One-Sentence Differentiation

**GitHub is what you learned. Substack is how you learned it — including what you got wrong.**

The repo is the textbook. The newsletter is the lab notebook. Textbooks are commodities. Lab notebooks from someone who tracks their own calibration errors are not.
