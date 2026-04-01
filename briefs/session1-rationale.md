# Session 1 Rationale Log — 2026-04-01

> Key reasoning chains preserved for audit. Not for execution agents.

## Decision evidence

1. **nano-agent-anatomy as study journal** — User said "好的" to blog, then pivoted: "这个repo的定义是不是应该是我们拆解学习分享的过程?" Changed from finished textbook to living study journal.

2. **Economy removed** — User: "Agent economy 是一个构想不能作为教程, 我们得先把demo做了, 才能讲这个, focus在学习 claude code source code 和 berkely agent mooc 上"

3. **mindflow separate from card-terminal** — User: "开新的repo, 之前的card-terminal太重, test跑了但是还是没法用, 而且是pre全景框架和qc的产物"

4. **"1/5" corrected to "2/5"** — Fact-check agent verified: LangChain/CrewAI already teach memory and multi-agent (beginner level). Context compression and agent economy are genuinely undertaught. "1/5" was exaggerated to make content sound more revelatory.

5. **CC leak = CLI only** — Multiple sources (The Register, VentureBeat, Anthropic statement) confirm: client-side code only. No server-side inference, model weights, or customer data.

6. **Publishing framework compliance** — User asked: "有template, procedure, 和独立qc吗, 根据我们刚学到的, 有更新enforcement吗" — explicitly demanded framework panorama compliance for all publishing.

## Unconfirmed proposals

- Substack name "Agent Anatomy", handle "agentanatomy" — user was registering but didn't confirm final choice
- Gumroad $0+ launch price then $10 floor — suggested but not confirmed
- mindflow Phase 1 timeline — designed but no commitment

## Rejected

- **Merge mindflow with card-terminal** — card-terminal is legacy
- **Economy as tutorial layer** — aspiration without demo, not teachable
- **"nanoagent" as repo name** — taken by multiple existing repos

## Discoveries

| Finding | Source |
|---------|--------|
| KAIROS = CC's always-on daemon with autoDream memory consolidation | ccleaks.com, Alex Kim analysis |
| CC coordinator uses NL orchestration ("Do not rubber-stamp weak work") | ccleaks.com, VentureBeat |
| CC has 4 hook types × 31 lifecycle events with stdin JSON protocol | User's parallel session analysis |
| prompt hook type = native LLMGate for semantic evaluation | User's agent-gates analysis |
| Rust port (conversation.rs 584L, compact.rs 485L, permissions.rs 232L) is best study material | Education expert agent |
| nanoagent space crowded but all repos only implement tool loop layer | GitHub survey of 8+ repos |
| Berkeley CS294 Agentic AI MOOC: 12 lectures from OpenAI/NVIDIA/DeepMind/Meta/Stanford | Web search |

## Constraint reasoning

- **≤150 lines per .py** — if the file is longer, the concept isn't simplified enough to be educational. This is a learning repo, not production code.
- **Publishing requires persona QC** — session 7 demonstrated that automated checks (word count, AI smell) catch surface issues but not content quality. Independent persona review needed per channel.
