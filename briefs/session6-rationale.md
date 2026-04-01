# Session 6 Rationale Log — 2026-04-01

> Key reasoning chains preserved for audit. Not for execution agents.

## Decision evidence

1. **Source naming correction** — "Anthropic Academy" → "Anthropic Docs & Engineering Blog"
   - Evidence: academy-researcher found Skilljar has 16 courses, all too introductory. Real cross-validation comes from 7 engineering blog posts: "Building Effective Agents" (Dec 2024), "Effective Context Engineering" (Sep 2025), "Claude Code Auto Mode" (Mar 2026), "Claude Code Sandboxing" (Oct 2025), "Advanced Tool Use" (Nov 2025), sub-agents docs, tool use API docs.

2. **"9-section compaction" is internal only**
   - Evidence: Official Anthropic eng blog lists 5 compaction categories (accomplished, WIP, files, next steps, constraints). The 9-section structure is from our own CC TS reading of compact/prompt.ts. Not contradicted, but not officially documented.

3. **Context compression curriculum gap**
   - Evidence: mooc-researcher read 3 course iterations (F24: 12 lectures, S25: 12 lectures, F25: 21 lectures). Zero cover context compression. Closest: Yu Su's HippoRAG lecture (S25 L5) = RAG-based retrieval, NOT context window management.

4. **Agent-economy cross-validation from Berkeley F25**
   - Evidence: 4 independent lectures provide interlocking support without citing economic theory:
     - Bavor (Sierra): outcome-based pricing = credence good equilibrium
     - Wang (Meta): benchmark SNR=1.1 = information asymmetry is severe
     - Jiao (NVIDIA): verifiable rewards = making quality observable
     - Brown (OpenAI): cheap-talk theorem = language claims untrustworthy

5. **Subagent spawn limit is CC hard limit**
   - Evidence: Tested 3 approaches, all 0 spawns: (a) mid-flight messages 0/3, (b) initial prompt "MANDATORY" 0/1, (c) explicit Scout→Reader×N structure 0/1. Sub-agents docs confirm: "Subagents cannot spawn other subagents."

6. **Handoff v2.2 sections from CC compaction**
   - Evidence: CC compaction preserves 9 sections including "Key Technical Concepts" (section 2), "Files and Code" (section 3), "All User Messages" (section 6). Our handoff brief lacked these. Added to dotfiles/claude/skills/handoff/SKILL.md.

## Unconfirmed proposals

1. **Context pollution feature as context_v4.py**
   - Context: User proposed extending microCompact to wrong model outputs. Prototype spec written in notes/09. Not yet implemented.

2. **Bundle cc-fuel-gauge blog with nano-agent launch**
   - Context: Carried from session 5. Still makes sense — fuel-gauge shows the problem, nano-agent shows the anatomy.

## Rejected

- **Downgrade to 4-source without reading MOOC** — User PUA'd: "pua 这个领域发展这么快, 你看2024年的?" Correct response was to actually read the lectures, not take the lazy path.

## Discoveries

| Finding | Source |
|---------|--------|
| Context compression absent from ALL Berkeley MOOC iterations (F24, S25, F25) | mooc-researcher + mooc-researcher-2 across 45 lectures |
| Agent-economy paper has implicit cross-validation from 4 F25 lectures | f25-readers: Bavor (Sierra), Wang (Meta), Jiao (NVIDIA), Brown (OpenAI) |
| MCP = vertical (agent↔tool), A2A = horizontal (agent↔agent) | Dawn Song F25 intro slides |
| τ-bench uses pass^k not pass@k | Bavor lecture: "at millions of conversations, reliability > peak performance" |
| Subagents cannot spawn subagents — CC hard limit | 3 tests + sub-agents documentation |
| Correction-aware microcompact has no prior art | Searched CC, AutoGen, LangChain, MemGPT — none do automatic correction rewind |
| "9-section compaction" is internal implementation, official docs say 5 | Anthropic eng blog vs CC TS compact/prompt.ts |
| Handoff and compaction serve different scopes (inter vs intra session) | Analysis: compaction = within context window, handoff = across sessions |
| Game theory (Noam Brown) provides formal basis for CC's consequence framing | Cheap-talk theorem: language claims useless in adversarial settings |
| ReAct formal definition: Â = A ∪ L (reasoning as internal action) | Shunyu Yao F24 L2 slides |
| Generative Agents retrieval scoring: recency × importance × relevance | Yao F24 L2 slides 41-43 |
| ASL framework = origin story for CC permission tiers | Ben Mann F24 L11 slides |

## Constraint reasoning

- All constraints carried from session 5. No new constraints added.
- Handoff v2.2 template change is a process improvement, not a constraint.
