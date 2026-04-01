# Session 7 Rationale Log — 2026-04-02

> Key reasoning chains preserved for audit. Not for execution agents.

## Decision evidence

1. **Code open / analysis paid** — Content strategy research: 6 successful newsletters studied (Willison, Pragmatic Engineer, ByteByteGo, Latent Space, Lenny, Raschka). Pattern: "GitHub is what you learned. Substack is how you learned it." User confirmed with "重点就是结合5个source."
2. **Gumroad one-time, not Substack subscription** — User: "我现在就想蹭这波热点, 试一下内容付费." Claude Code source leak is time-sensitive. Subscription needs sustained content; one-time captures the moment.
3. **Force push clean history** — User explicitly authorized: "force push 吧" then "就把notes 全部去掉呗, 干净." Notes backup at `~/Developer/personal/nano-agent-anatomy-notes-full/`.
4. **CC enforcement gates** — Session 7 discovered we had 100% non-compliance with our own framework. CC's Sonnet was 2.79% non-compliant with prompts → solved with maxTurns:1. Our solution: exit code 2 in PreToolUse hooks. User asked for this: "怎么用这次从cc学到的来强制执行这些."
5. **小红書 v2 repost** — XiaohongshuReviewer persona flagged "泄露源码" as P0 compliance risk. MCP has no edit function. User: "没有编辑就删除, 再发." Republished with "公开源码" + emoji formatting + interaction prompt.
6. **context_v4 bug fix** — Independent opus code reviewer found: after compaction, chat() still appended user correction as separate message (3 consecutive user messages). Fix: skip append when compaction succeeds. 13 unit tests added to verify.
7. **E2E + functional tests** — User: "pua test是完整测试吗" and "pua 对api能跑通, 功能能实现吗?" Led to: (a) 5 E2E smoke tests against real API, (b) functional test proving correction microcompact actually changes model behavior (Canberra test: correct answer + 25% fewer messages).

## Unconfirmed proposals

- cc-dashboard as standalone project (brainstormed but not executed — 6 panels: memory browser, skills registry, publishing pipeline, source reading pipeline, deliverables tracker, knowledge graph)
- Platform-specific style gates (designed but not implemented — need pre-publish-xhs.sh, pre-publish-substack.sh)
- Ghost MCP + Substack MCP installation (researched, not installed)

## Rejected

- Truncated notes in GitHub with "full version on Gumroad" CTA — user: "这样还不如不放" then "就把notes 全部去掉呗, 干净"
- Substack as paid platform — replaced by Gumroad one-time purchase
- Keeping 00-* methodology files in notes/ — user wanted everything gone: "干净"

## Discoveries

| Finding | Source |
|---------|--------|
| 小红書 top tech posts use 8-10 images as carousel (images ARE the content, text is hook) | MCP search: top 3 posts analyzed |
| Top image ratio: 3:5 (1440x2400) or 3:4 (1080x1440) | Engagement data from 24 posts |
| Top post text: 50-150 words only | Post detail analysis |
| "泄露" word triggers compliance risk on 小红書 | XiaohongshuReviewer persona |
| CC hooks protocol uses exit code 2 to block tool execution | CC source leak findings |
| Our framework compliance was ~0% before gates (published without QC, claimed open-source without pushing, no style checks) | Session 7 self-audit |
| Successful newsletters sell curation/process/calibration, not information | 6 newsletter case studies |

## Constraint reasoning

- No research-institute/research-lab names — compliance requirement, permanent
- 150 lines per .py — pedagogical clarity, permanent for this project
- Publishing requires gates — enforced by hooks now (not just a rule)
- Gumroad one-time — user decision based on热点 timing
- No video — user constraint: "肯定没有视频"
