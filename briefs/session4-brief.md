# Session 4 Brief — 2026-04-01

> Execution agent reads ONLY this. Brief like a smart colleague who just walked into the room.

## What Happened in Session 3+4

Session 3 designed and partially ran the v1-vs-v2 blind experiment. Session 4 completed the experiment, analyzed results, did competitive research, read CC prompts/SDK source, researched pedagogical models, and redesigned the entire course structure.

**Experiment result:** v1 (free-form) wins 6-1 blind. v2 (JSON) wins on evidence (+1.33) and extraction (+0.33). Core insight: structure aids verification, freedom aids insight. SOP v3 written: dual-channel (extraction JSON + interpretation Markdown).

**Competitive landscape:** 60+ Chinese articles in 72 hours, all surface-level architecture lists. English: Alex Kim (quirks), Code Pointer (KAIROS), Raschka (harness>model). Nobody has experiment data, nobody has cross-validated curriculum, nobody teaches prompt engineering from CC source.

**Course redesign:** From weekly drip → complete "Launch Release" with 5-source cross-validation. Modeled on CS336/nanoGPT patterns: simplify scale not algorithm, verify against production, progressive onion layers, make the gap explicit.

## What Was Decided

1. SOP v3 = dual-channel (extraction JSON + interpretation free-form). Based on experiment data, not opinion.
2. Skill packaged at `~/claude-skills/source-reading/SKILL.md`
3. Course is "learn anything" cross-validation system, not competing product. 5 sources: Berkeley MOOC, CC TS, claw-code, Anthropic Academy, Agent SDK.
4. Substack/小红书 #0 rewritten with experiment hook (not architecture overview). QC PASS.
5. ROADMAP V2: 7 units with code progression (onion layers), scenario tests, exercises, gap docs.
6. Delivery = Launch Release (all at once) → Weekly Iteration. Not weekly drip.
7. New Unit 5: Production Prompt Engineering (44 tool prompts from CC source). Zero coverage in market.

## Corrections (things we believed that turned out wrong)

| Previous belief | Corrected to | Evidence |
|----------------|-------------|----------|
| Compaction is deterministic (zero LLM calls) | CC TS uses full LLM prompt with 9 sections + `<analysis>` scratchpad | `src/services/compact/prompt.ts` in CC TS source |
| "Two weeks" designing SOP v2 | Everything happened in ~24 hours (leak March 31, all work April 1) | git log: first commit 2026-04-01 |
| "独家" content | Information is public. Differentiator = cross-validation + experiment data + curriculum format | User correction + competitive research |
| Agent SDK is a standalone framework | SDK is a control protocol wrapper around 196MB CC CLI binary. All agent behavior inside binary. | SDK source: `subprocess_cli.py` spawns `claude` subprocess |
| Substack/小红书 #0 are differentiated | Original #0 was same as 60+ existing architecture overview articles | Competitive research: WeChat 60+ articles, all surface-level |
| v2 would outperform v1 | v1 wins 6-1 on blind evaluation | experiment/report/experiment-report.md |

## What Was Completed

- Experiment: `experiment/report/experiment-report.md` (v1 wins 6-1)
- SOP v3: `~/.claude/memory/knowledge/source-reading-agent-sop-v3.md`
- Skill: `~/claude-skills/source-reading/SKILL.md`
- Panorama updated: 隔离通信模式 + experiment evidence + v3 pipeline
- Competitive research: Chinese (60+ articles) + English (all platforms)
- Agent SDK analysis: control plane vs implementation layer
- Anthropic Academy + CCA + DeepLearning.AI course mapping
- CC prompts analysis: 44 tool prompts + compaction + skillify
- Pedagogical research: `notes/00-pedagogical-research.md` (CS336, nanoGPT, nano-vLLM)
- ROADMAP V2: 7 units, 5-source cross-validation, code progression + tests + exercises
- Substack #0 + 小红书 #0 rewritten + QC PASS
- Gumroad + DISTRIBUTION.md corrected (5层→4层, 46K→删, 14 vectors→删)

## What to Execute Next

| Priority | Task | Dependency |
|----------|------|------------|
| P0 | Write remaining units code progression (loop_v0-v3, memory_v0-v2, context_v0-v3, coordinator_v0-v3) | — |
| P0 | Write scenario tests per layer (`tests/`) | Code progression done |
| P0 | Write exercises per unit (`exercises/`) | Notes + code done |
| P0 | Add "What Production Does That We Don't" to each note | — |
| P1 | Publish Substack #0 + 小红书 #0 | Human login |
| P1 | Write Unit 5 note: Production Prompt Engineering (44 tool prompts analysis) | — |
| P1 | Update notes/03-context.md with CC TS cross-validation (compaction is LLM-based) | — |
| P1 | Write blog: "From Theory to Production: What 513K Lines Taught Me About Context Degradation" | See notes/06-agent-reliability-triad.md § Blog Angle |
| P2 | Run v3 on CC TS for three-way comparison (v1 vs v2 vs v3) | — |
| P2 | Build ground truth set (~50 architectural facts) for objective recall metric | — |

## Blog Pipeline

| Blog | Angle | Status | Cross-validates |
|------|-------|--------|-----------------|
| Context degradation: theory → production | "I diagnosed the disease, CC source shows the treatment" | notes/06 written, ready to draft | Our 2 existing blogs + CC compact/prompt.ts |
| Experiment story (Substack #0) | "Structured approach lost 6:1" | QC PASS, ready to publish | SOP v1 vs v2 experiment data |
| SDK vs internals | "What Anthropic teaches vs what they build" | SDK analysis done, needs draft | Agent SDK + CC source + Academy courses |

## Key Knowledge Artifact

`notes/06-agent-reliability-triad.md` — Agent reliability triad (non-compliance / intent-execution gap / context degradation) with:
- CC's three-layer enforcement patterns (prompt → consequence → code)
- Dimension A: Science/philosophy behind each solution (game theory, Popper, neuroscience, information theory)
- Dimension B: CS system design patterns + tradeoffs (OCC, circuit breaker, cache partitioning, lossy compression)
- Blog angle: "From Theory to Production" bridging existing context degradation blogs with CC source

## Constraints

- No research-institute/research-lab names in public content
- Each .py ≤ 150 lines
- Publishing requires template + procedure + independent QC
- Gumroad BLOCKED until course complete
- Handoff must include corrections section (prevent error propagation)
