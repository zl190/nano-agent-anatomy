# Session 4 Rationale Log — 2026-04-01

> Key reasoning chains preserved for audit. Not for execution agents.

## Decision evidence

1. **v1 wins 6-1 blind** — experiment/report/experiment-report.md: per-reader scores, dimension averages, evaluator rationale. v2 won evidence (+1.33) and extraction (+0.33), lost depth (-1.00) and actionability (-1.17).

2. **SOP v3 dual-channel** — Logical resolution of measured v1/v2 trade-offs. Evidence-informed but not yet experimentally validated as a complete SOP.

3. **"Learn anything" positioning** — User explicitly said "不是在对标这些课, 而是把这些资源利用起来提供一站式交叉验证的类udemy的学习资料". Changed from competitive to integrative framing.

4. **Launch Release not weekly drip** — User: "我们不能等每周出, 得一次出完, 可以每周迭代, 专家评审"

5. **SDK = control protocol** — SDK source analysis: subprocess_cli.py spawns `claude` binary, JSON-over-stdio protocol, no `anthropic.messages.create()` calls.

6. **Compaction cross-validation** — claw-code compact.rs is deterministic. CC TS compact/prompt.ts uses LLM with 9-section prompt. Comment in source reveals Sonnet 4.6 ignored "no tools" instruction 2.79%.

7. **Three-layer enforcement** — Extracted from CC source: prompt → consequence framing → code enforcement. NO_TOOLS_PREAMBLE + maxTurns:1 is the canonical example.

8. **readFileState = physical enforcement** — FileEditTool rejects edits if readFileState has no entry. Timestamp comparison catches concurrent edits.

9. **verificationAgent = adversarial** — "Try to break it, not confirm it." Two named failure modes: verification avoidance, seduced by first 80%.

## Unconfirmed proposals

- Blog "From Theory to Production" — angle identified, notes written, not yet drafted
- Week 5 prompt engineering unit — in ROADMAP, content not written
- Anthropic courses as cross-validation source — researched, not tested in practice
- Three-way v1/v2/v3 comparison — designed, not run
- Ground truth set for recall metric — discussed, not built

## Rejected

- "独家" framing — user corrected: public information
- Test v3 on new repo first — user corrected: CC TS gives controlled comparison
- SOP v2 as skill — experiment showed v2 is not wholesale replacement
- Weekly drip model — user said 一次出完
- "Two weeks" timeline claim — fabricated, corrected to ~24 hours

## Discoveries

| Finding | Source |
|---------|--------|
| Sonnet 4.6 ignores "no tools" 2.79% of time | compact/prompt.ts:12-17 code comment |
| Agent list in attachment saves 10.2% cache tokens | AgentTool/prompt.ts:57 code comment |
| CC verification agent is read-only, cannot modify project | verificationAgent.ts:14 |
| CC skillify uses 3-round structured interview | skillify.ts |
| Anthropic Academy: 16 free courses, CCA: 27% agentic arch | Research agent |
| DLAI "Agent Skills" is only course covering Agent SDK | Research agent |
| "Learn by rebuilding" 7-component meta-pattern | Pedagogical research across 6 projects |
| "Simplify scale not algorithm" (Karpathy) + "ban high-level APIs" (CS336) | notes/00-pedagogical-research.md |
| Agent education gap: every tutorial stops at Layer 1 (tool loop) | Pedagogical research |

## Constraint reasoning

- Corrections in handoff: compaction cross-validation showed wrong belief persisted from session 2→3→4. Without corrections section, next session would repeat the "deterministic compaction" claim.
- Gumroad BLOCKED: incomplete material kills trust. Changed "Week 6" to "course complete" since delivery is now Launch Release not weekly.
