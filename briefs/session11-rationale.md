# Session 11 Rationale Log — 2026-04-02

> Key reasoning chains preserved for audit. Not for execution agents.

## Decision evidence

1. **enforcement vs evaluation framing** — User asked "这个claim靠谱吗" about "安全>>质量". Analysis: quality investment is in model training (RLHF, constitutional AI), not CC wrapper. CC hooks system IS quality infrastructure. The claim had a logical jump. Corrected to: enforcement有, evaluation没有.

2. **Gumroad product naming** — Content expert: drop "Leaked Source" from title (liability: legal concern, date-stamps product, not searchable). Marketing expert: use "Agent Anatomy" as product name, long hooks for launch posts. Both agreed.

3. **$19 pricing** — Content expert: content worth $49 but markdown zip format limits perceived value. $19 ok, could push to $29-39 with better packaging. Marketing expert: $19 launch, $29 after April 9. Gumroad data: courses avg 115 sales at $95.74, median $13.

4. **Free preview strategy** — Both experts: give away 01-tool-loop.md. Zero-audience creator cannot sell analysis sight-unseen. "Give away the first chapter" strategy. Also give experiment report (builds credibility, not core product).

5. **Twitter before Reddit** — Twitter had no barriers. Reddit needed mod approval. HN needed account + karma. So: Twitter first (done), Reddit second (submitted), HN last (needs karma).

## Unconfirmed proposals

- Launch-week pricing $19→$29 after April 9 (marketing expert recommended, user didn't confirm date)
- Add $0 Gumroad tier for email capture (content expert recommended, not implemented)
- XHS voice calibration with user samples (user said "先别管了" this session)

## Rejected

- Self-host Plausible: user doesn't have Oracle VM, Cloudflare already free and automatic
- Reddit API via PRAW: blocked by Responsible Builder Policy review
- Flashcards in product: "不需要。这是technical deep dive不是备考材料"

## Discoveries

| Finding | Source |
|---------|--------|
| Chrome MCP blocks reddit.com (safety restriction) | Attempted navigation |
| Reddit API app creation now requires Responsible Builder Policy review | User showed error |
| HN has no submission API (read-only); new accounts need karma for visibility | Research agent |
| Gumroad digital downloads average 293 sales; courses 115 at $95.74 | 146K product analysis |
| No competing CC leak analysis products on Gumroad | WebSearch |
| CC source has per-agent model override (AgentDefinition), not local routing | experiment reader data |
| Gumroad needs Stripe/PayPal connected before publishing paid products | User hit this blocker |

## Constraint reasoning

- **Every number grep-verified**: max_turns=25 shipped when actual was 8. Buyer would verify. Single most damaging error type.
- **QC mandatory**: 25 issues across 2 rounds. First round missed factual errors. Second round found wrong config values in the FREE PREVIEW file.
- **Preview 2x scrutiny**: 01-tool-loop.md had more errors than any other file. It's the only thing buyers see before paying.

## Session 11 retro: 7 failure patterns

1. Every number needs a grep (not memory)
2. QC gate is mandatory, not optional
3. Never speculate without evidence
4. Builder and Reviewer must be separate contexts
5. "不太会在意" = red flag, fix it
6. Pre-launch checklist for every platform
7. Preview file gets 2x scrutiny

All 7 documented in `~/.claude/memory/feedback_product-launch-retro.md` and 3 wired as hooks in settings.json.
