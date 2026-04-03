# Session 22 Rationale Log — 2026-04-03

> Key reasoning chains preserved for audit. Not for execution agents.

## Decision evidence

1. **settings.json symlink** — P0 from session 21 brief. Diff showed only absolute→portable path changes. Created backup before symlinking. Done at session start to minimize mid-session risk.

2. **paper-reading SKILL.md** — Session 21 auditor found: (a) budget cap $10.00 but actual = $0.80×11×2 + $2.00 = $19.60, (b) Steps 2-4 hardcoded sonnet despite DEPTH table. Fix: conditional model selection using bash `[[ ]]`, budget formula changed to N×$1.60+$2.00.

3. **publish-xhs SKILL.md** — Session 21 auditor found: (a) Step 2+3 gates were prose-only, (b) Step 7 fix path skipped persona QC (Step 5), (c) no retry limits on persona QC. Fix: inline script checks for gates, Step 7 re-runs 4+5, max 2 retries with escalation.

4. **pipeline-orchestration-spec** — Session 21 auditor identified 7 issues; session 22 explorer agent found 9 total:
   - Exit code harmonization: added Section 4.0 with 0/1/2 mapping
   - Escalate semantic collision: single definition (model upgrade only), fixed QC step from `escalate` to `retry`
   - Artifact passing contradiction: clarified path-based bookkeeping + content in prompts
   - Gate block signal: split into Gate REVISE (exit 1) and Gate REJECT (exit 2)
   - Retry+escalate conflict on build step: changed to `retry` with comment
   - Agent gate verdict: unified PASS/REVISE/REJECT across evaluate, audit, QC steps
   - on_failure routing: added "sequential, all run" comment
   - Parallel group detection: expanded algorithm (explicit + implicit mechanisms)
   - Artifact validation timing: addressed in Section 3.4 ("runs BEFORE gate")

5. **Harness landscape blog** — Delegated to sonnet Builder agent with: synthesis.md as source, blog-content.md style guide, narrative arc from synthesis "What the Blog Should Say" section, personal experience data (5087 hook fires, session 21 failure). Agent produced 2700w draft following the 4-phase evolution structure.

6. **22/22 blog** — Delegated to sonnet Builder agent with: the complete incident story, style guide, credence good angle, AgentBreeder citation requirement. Agent produced 1050w draft with hook-first structure.

7. **Dotfiles push** — Committed pipeline spec fix (65023c0), 43/43 pre-push hook tests passed.

## Unconfirmed proposals

- Blog "You Need More Than Auto-Compact" — Context VM + handoff gates angle (session 21)
- Four daemon loops as always-on architecture — user vision (session 21)
- Agent OS Control Panel — TUI first (session 21)
- Corpus-level session analysis — Zalando pattern (session 21)

## Rejected

- Use source-reading skill as-is for papers — Audited REVISE (session 20)

## Discoveries

| Finding | Source |
|---------|--------|
| Pipeline spec had 9 issues not 7 — parallel detection algorithm + artifact validation timing were the extras | Session 22 explorer agent |

## Constraint reasoning

| Constraint | Reason |
|-----------|--------|
| No research-institute/research-lab in public content | Privacy — permanent |
| QC mandatory before publishing | Dual QC prevents credence good problem — permanent |
| Never modify settings.json mid-session | Resets permission cache — permanent |
| Agent artifacts are claims not facts | Session 20-21 evidence — permanent |
| jq -cn --arg for JSONL | Prevents JSON injection — permanent |

## Prior handoff quality assessment (session 21 → session 22)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Completeness | 4/5 | All tasks were clearly specified. Minor: said "7 REVISE" but was actually 9 |
| Accuracy | 5/5 | All verified decisions held true. Symlink, files, settings all confirmed |
| Usefulness | 4/5 | Next steps were correctly prioritized. P0 was right. Brief structure clear |
| **Overall** | **4.3/5** | Strong improvement from 3.7. Key technical concepts section was well-targeted |
