---
# model.md — Projection Model
# nano-agent-anatomy unified source of truth
# Last updated: 2026-04-02
---

thesis: >
  Reading production agent source code alongside academic curriculum, rebuilding each
  layer in ~100 lines of Python, reveals systematic gaps between what's taught and
  what's built — and the methodology of reading itself is an unsolved design problem.

status: draft

---

## Claims

### C1 — Experiment result: free-form reading wins 6-1
evidence: >
  Blind A/B experiment comparing SOP v1 (free-form Markdown) vs SOP v2 (JSON schema +
  architecture persona + validation gates) on 513K-line Claude Code TypeScript source.
  Independent Opus evaluator preferred v1 for 5/6 individual readers and the synthesis.
  Pattern depth: v1 5.00 vs v2 4.00 (-1.00). Actionability: v1 5.00 vs v2 3.83 (-1.17).
  v2 won on evidence quality (+1.33) and extraction completeness (+0.33, 2.2x symbols).
  Overall: v1 preferred 6-1.
source: experiment/report/experiment-report.md
coverage:
  - substack-issue-0.md   # primary home — full story with scores table
  - xiaohongshu-post-0.md # compressed version — 6:1 result with key trade-off

### C2 — Curriculum gap: 45 lectures, 0 context compression coverage
evidence: >
  Berkeley LLM agent curriculum audited across all three iterations: CS294 Fall 2024
  (12 lectures), CS294/194-280 Spring 2025 (12 lectures), CS294 "Agentic AI" Fall 2025
  (21 lectures). Total: 45 lectures. Context compression not covered in any. F25 Oct 1
  "Memory and Knowledge Management" is the only candidate lecture; content unconfirmed.
  S25 L5 (Yu Su) covers HippoRAG — external retrieval, not window management. The gap
  is genuine: 4/5 curriculum layers have strong MOOC matches; context compression has none.
source: notes/00-source-validation-audit.md (§ Berkeley MOOC — PARTIALLY VALIDATED)
coverage:
  - blog-curriculum-gap.md   # primary home — full curriculum audit with table

### C3 — Credence good cross-validation: 4 Berkeley F25 lectures
evidence: >
  Four Fall 2025 Berkeley lectures provide interlocking empirical support for the
  credence good thesis (submitted paper argues software quality is a credence good)
  without naming it: Bavor (Nov 10) — outcome-based pricing + 30-item Agent Iceberg;
  Wang (Oct 27) — HumanEval SNR=1.1, HumanEval+ SNR=0.50, "models are bigger sources
  of inconsistency than benchmarks"; Jiao (Sep 29) — "Environment Feedback Aligned
  Models," verifiable rewards; Brown (Oct 20) — cheap-talk theorem: language
  communication provably useless in zero-sum minimax equilibrium.
  tau-bench (pass^k metric) adopted by Anthropic and OpenAI.
source: notes/00-source-validation-audit.md (§ Agent-Economy Paper Cross-Validation)
coverage:
  - blog-credence-good-berkeley.md   # primary home — QC: PASS (no required fixes)

### C4 — Context pollution proposal: novel, no prior art found
evidence: >
  Existing frameworks handle context by volume, not correctness. Wrong model output
  stays in context after correction, competing with the correction signal via softmax
  dilution, lost-in-the-middle position effects, and self-reinforcement. Claude Code
  has three compaction layers (compact.ts, autoCompact.ts, microCompact.ts) and
  surgical targeting via collectCompactableToolIds() — the mechanism exists, aimed at
  the wrong target (tool results, not wrong outputs). ChatGPT: manual fork only.
  LangChain: memory.clear(), not selective. MemGPT: long-term store, not in-context.
  autoCompact fires at 95% capacity (confirmed: sub-agents docs). Two-stage classifier
  confirmed (Auto Mode blog): fast single-token check, then CoT reasoning.
  Proposed fix: correction-aware microCompact — detect correction signals, replace
  [wrong response + correction] pair with a compression note.
source: >
  notes/09-context-pollution-rewind.md;
  notes/00-source-validation-audit.md (§ Source 3 and § Source 4);
  blog-context-pollution.md (prototype: context_v4.py)
coverage:
  - blog-context-pollution.md   # primary home — QC: PASS WITH FIXES, fixes applied

### C5 — Production compaction uses LLM, not deterministic extraction
evidence: >
  claw-code (Rust port, 64 file:line references): compact.rs (485 lines) is
  deterministic — pure extraction of stats, recent requests, key files, pending work,
  zero LLM calls. CC TS source (24 file path references): src/services/compact/prompt.ts
  is LLM-based with 9-section structured output + <analysis> scratchpad stripped before
  reaching context. Official Anthropic docs list 5 compaction categories — the 9-section
  structure is CC TS source ONLY, not officially cross-validated. Discrepancy is real:
  claw-code is the "nano" approximation; CC TS is the production system.
  Dual trigger confirmed (CC TS): message_count AND tokens, not one or the other.
  NO_TOOLS_PREAMBLE enforces no tool calls during compaction.
source: >
  notes/03-context.md;
  notes/00-source-validation-audit.md (§ Source 2, § Source 4 — "9 sections" caveat);
  ROADMAP.md (§ Unit 3)
coverage:
  - blog-context-degradation.md   # primary home — QC: PASS WITH FIXES, fixes applied

### C6 — Context degradation: three mechanisms + 30-50K threshold
evidence: >
  Three mechanisms: (1) Softmax dilution — attention entropy scales as Theta(log n)
  (Nakanishi 2025, not in source validation audit; cited from prior research).
  (2) Lost in the middle — U-curve; 39% performance drop for middle-turn content
  (Liu 2023; Laban 2025, not in source validation audit).
  (3) Position OOD — RoPE extrapolation beyond training range (Du 2025, not in
  source validation audit). Empirical convergence at ~30-50K absolute tokens.
  Anthropic engineering blog (Sep 2025): "context rot" — recall accuracy decreases
  as token count increases. Tool Result Clearing as lightest compaction form.
  CAUTION: Nakanishi, Laban, Du are from prior research, not re-verified for this project.
  The CC TS numbers (2.79% tool non-compliance rate, 10.2% fleet token savings from
  agent list move) come from CC TS source reading — no external cross-validation.
source: >
  notes/03-context.md;
  notes/00-source-validation-audit.md (§ Source 4 — Anthropic Eng Blog);
  blog-context-degradation.md
coverage:
  - blog-context-degradation.md   # primary home

### C7 — Correction-aware microcompact implementation (context_v4.py)
evidence: >
  Prototype implementation in blog-context-pollution.md and context_v4.py.
  detect_correction() uses keyword matching (correction_patterns list).
  correction_microcompact() locates most recent assistant message, replaces it with
  a labeled correction note, preserving the correction signal without the wrong output.
  Acknowledged limitations: pattern list doesn't handle negation/sarcasm; 200-char
  truncation is arbitrary. Builds on CC's microCompact.ts selectivity pattern.
source: context_v4.py; blog-context-pollution.md (lines 53-76)
coverage:
  - blog-context-pollution.md   # only coverage — embedded as prototype

### C8 — Source reading methodology: SOP v3 dual-channel design
evidence: >
  SOP v3 design emerged from C1 experiment result. Extraction phase: JSON schema
  (v2 approach), cheap model (Haiku), mechanical work — symbols, signatures,
  dependencies, file:line evidence. Interpretation phase: free-form Markdown (v1
  approach), premium model (Sonnet/Opus), narrative depth — patterns, surprises,
  "what tutorials don't teach." Gate on extraction only; leave interpretation ungated.
  Cost increase ~20-30% over single pass. v3 not yet validated experimentally.
source: experiment/report/experiment-report.md (§ 8 Recommended SOP v3 design)
coverage:
  - substack-issue-0.md   # primary — "The Fix: Dual-Channel Output" section

### C9 — Production agent architecture: 4-source cross-validation discrepancies
evidence: >
  Four validated sources (CC TS, claw-code, Anthropic Docs & Eng Blog, Agent SDK)
  with known discrepancies as the primary finding:
  Compaction: claw-code = deterministic; CC TS = LLM with 9-section prompt (C5 above).
  Agent spawning: SDK = AgentDefinition dataclass; CC source = "Never delegate
  understanding" + fork-vs-fresh cache strategy.
  Permissions: Anthropic Docs teach 3-tier auto-mode; CC source has fail-secure
  (unknown → highest permission) + deny reason as is_error.
  Memory: SDK exposes memory flag; CC source has 2-layer architecture + autoDream
  (internal name from minified JS; official term: "memory consolidation") + semantic
  search via 256-token relevance side call.
  Berkeley MOOC: partially validated (4/5 layers strong match; context compression = 0).
source: >
  notes/00-source-validation-audit.md;
  ROADMAP.md (§ Known cross-validation discrepancies)
coverage:
  - gumroad-product.md   # partial — product framing mentions 4 layers
  - blog-curriculum-gap.md   # partial — Berkeley layer coverage table

---

## Structure

hook: >
  The leak happened on March 31, 2026. 513,000 lines of TypeScript across 1,892 files.
  The methodology question (how do you read this?) turned into the first experiment.
  The experiment produced a counter-intuitive result. The result pointed at a deeper
  gap: what production builds that the curriculum doesn't teach.

sections:
  - "0. The experiment — what the methodology found (C1, C8)"
  - "1. The tool loop — max_iterations, is_error, permission before execution (C9)"
  - "2. Memory — 2-layer architecture, autoDream consolidation (C9)"
  - "3. Context — degradation mechanisms, compaction discrepancy, pollution proposal (C5, C6, C4, C7)"
  - "4. Coordinator — NL orchestration, not code-based (C9)"
  - "5. Curriculum audit — what Berkeley covers vs. skips (C2, C3)"

close: >
  The 513K-to-1000-line ratio captures the gap between understanding and building.
  What the nano implementation doesn't have is not the algorithms — it's the
  measurement infrastructure that produced the calibrated numbers. The methodology
  problem (how to read source code effectively) is still open. v3 is not yet validated.

---

## Projections

blog-context-degradation:
  path: publish/blog-context-degradation.md
  qc: PASS WITH FIXES
  qc_source: publish/qc-report-session7.md (Post 1)
  fixes_applied: true
  claims_covered: [C5, C6]
  primary_claims: [C5, C6]
  status: ready to publish (pending author fix verification)

blog-context-pollution:
  path: publish/blog-context-pollution.md
  qc: PASS WITH FIXES
  qc_source: publish/qc-report-session7.md (Post 2)
  fixes_applied: true
  claims_covered: [C4, C7]
  primary_claims: [C4, C7]
  status: ready to publish (pending author fix verification)

blog-credence-good-berkeley:
  path: publish/blog-credence-good-berkeley.md
  qc: PASS
  qc_source: publish/qc-report-session7.md (Post 3)
  fixes_applied: false   # no required fixes
  claims_covered: [C3]
  primary_claims: [C3]
  status: ready to publish

blog-curriculum-gap:
  path: publish/blog-curriculum-gap.md
  qc: PASS WITH FIXES
  qc_source: publish/qc-report-session7.md (Post 4)
  fixes_applied: true
  claims_covered: [C2, C9]
  primary_claims: [C2]
  status: ready to publish (pending author fix verification)

xiaohongshu-post-0:
  path: publish/xiaohongshu-post-0.md
  qc: pending
  claims_covered: [C1]
  primary_claims: [C1]
  status: published (posted to 小红书)

substack-issue-0:
  path: publish/substack-issue-0.md
  qc: pending
  claims_covered: [C1, C8]
  primary_claims: [C1, C8]
  status: drafted, not published

gumroad-product:
  path: publish/gumroad-product.md
  qc: N/A
  claims_covered: [C9]
  primary_claims: []   # product listing, not claim vehicle
  status: blocked (content not complete — notes and code not all shipped)
  blocker: >
    Product promises 4 learning notes + Python files. Not all units are complete.
    Do not list until all deliverables exist.

---

## Gap Analysis

### Claims with no projection coverage

C7 (correction-aware microcompact / context_v4.py):
  coverage: blog-context-pollution.md only (embedded code snippet, not the main claim)
  gap: >
    context_v4.py is mentioned as a prototype but not showcased as a standalone
    finding. No projection treats C7 as its primary claim. The blog focuses on the
    problem (context pollution) and the framework proposal; the implementation is
    a secondary artifact. If context_v4.py is developed further, it warrants its own
    projection (technical deep-dive or GitHub README section).

C8 (SOP v3 dual-channel design):
  coverage: substack-issue-0.md (solid coverage in "The Fix" section)
  gap: >
    v3 has not been validated experimentally. The projection (Substack issue) presents
    it as a recommendation, explicitly flagging it as unvalidated ("I haven't validated
    v3 yet. That's the next experiment."). No blog post makes v3 its primary claim.
    The gap is intentional — claiming v3 works before testing it would be premature.

C9 (4-source cross-validation discrepancies):
  coverage: partial across gumroad-product.md and blog-curriculum-gap.md
  gap: >
    No single projection synthesizes all four cross-validation discrepancies (compaction,
    agent spawning, permissions, memory) into a unified finding. The ROADMAP calls this
    "the gold" — WHERE THEY DISAGREE. No blog post is written yet that makes the
    discrepancy map its primary subject. This is the highest-value uncovered claim
    in the model.

### Projections making claims not fully in the model

blog-context-degradation.md:
  extra_claims:
    - >
      2.79% tool non-compliance rate (from CC TS source; no external cross-validation;
      used to motivate NO_TOOLS_PREAMBLE redesign). Not registered as a model claim
      because evidence is single-source CC TS reading. QC flagged; fix applied.
    - >
      10.2% fleet token savings from agent list move to attachment (from CC TS source
      comment; no external cross-validation). Same status. QC flagged; fix applied.
    - >
      Nakanishi (2025), Laban (2025), Du (2025) — academic citations from prior
      research, not re-verified in this project's source validation audit. Posts
      treat them as established; model treats them as provisional.

blog-context-pollution.md:
  extra_claims:
    - >
      Self-reinforcement mechanism (model anchors on its own prior output) — presented
      as observation but no citation given. QC flagged; fix applied (reframed as
      personal observation, not established finding).

blog-curriculum-gap.md:
  extra_claims:
    - >
      F25 Oct 1 "Memory and Knowledge Management" covers HippoRAG — source audit says
      F25 Oct 1 content is unconfirmed; HippoRAG finding is from S25 L5. QC flagged;
      fix applied (softened to expected-content-based-on-S25-parallel).

blog-credence-good-berkeley.md:
  extra_claims:
    - >
      "No prior formalization in CS literature" for credence good thesis — stated about
      the paper's claim. Strong universal negative. QC noted as caution; not required fix.
      Not registered as model claim; belongs to the agent-economy paper, not this project.

### Coverage matrix

| Claim | blog-ctx-deg | blog-ctx-poll | blog-credence | blog-curr-gap | xhs-0 | substack-0 | gumroad |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| C1 experiment 6-1 | - | - | - | - | PRIMARY | PRIMARY | - |
| C2 curriculum 45/0 | - | - | - | PRIMARY | - | - | - |
| C3 credence good Berkeley | - | - | PRIMARY | - | - | - | - |
| C4 context pollution proposal | - | PRIMARY | - | - | - | - | - |
| C5 LLM vs deterministic compaction | PRIMARY | - | - | partial | - | - | - |
| C6 degradation mechanisms + 30-50K | PRIMARY | partial | - | - | - | - | - |
| C7 context_v4.py | - | secondary | - | - | - | - | - |
| C8 SOP v3 dual-channel | - | - | - | - | - | PRIMARY | - |
| C9 4-source discrepancy map | - | - | - | partial | - | - | partial |

Legend: PRIMARY = main claim of this projection. partial = touched but not primary. secondary = mentioned as artifact. - = not covered.

### Priority gaps to close

1. C9 — No blog post synthesizes the cross-validation discrepancy map. This is the
   project's central methodological finding and has no dedicated projection. Recommended
   next projection: "What Four Sources Disagree About" (working title). Covers all four
   discrepancies (compaction, agent spawning, permissions, memory) with the insight that
   WHERE THEY DISAGREE is more valuable than what any single source teaches.

2. C7 + C8 together — context_v4.py and SOP v3 are both unvalidated proposals. A single
   projection could cover both: "Two Problems We Haven't Solved" — context pollution
   (C4/C7) and reading methodology (C8). Sets up the next experiment naturally.

3. Substack issue 0 QC — currently pending. Runs the same QC protocol that covered the
   four blog posts. Should be gated before publish.

4. xiaohongshu QC — published without QC. Retroactive QC recommended before more posts
   go up to 小红书 to establish baseline standard.

---

## Source Registry

| Source | Status | Evidence |
|--------|--------|----------|
| CC TS leaked source (513K lines) | VALIDATED | 24 file path references across 8 notes |
| claw-code (Rust port) | VALIDATED | 64 file:line references across 9 notes |
| Anthropic Docs & Engineering Blog | VALIDATED | 7 official sources with URLs |
| Agent SDK | VALIDATED | Full subprocess protocol architecture verified |
| Berkeley MOOC (CS294, F24/S25/F25) | PARTIALLY VALIDATED | 4/5 layers strong match; context compression = no coverage across all iterations |

## Accepted Foundations (justification stops here)

- CC TS source was genuinely read: Source 2 in audit is VALIDATED. Claims about what the
  production code does are grounded, even when the specific finding (e.g., 9-section
  compaction, 2.79% tool non-compliance) has no external cross-validation.
- The experiment was properly blinded: same model, same file splits, independent evaluator
  with no label knowledge. The 6-1 result is the experiment's result.
- Berkeley curriculum audit is grounded for F24 (slides read for L1-L3, L11) and for
  five F25 slide decks. The gap claim (no context compression) is confirmed for all
  three iterations.
- Academic citations (Nakanishi, Laban, Du) are from prior research, not re-verified
  here. Model treats them as provisional; projections should flag them as such.
