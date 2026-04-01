---
# model.md — Projection Model
# nano-agent-anatomy unified source of truth
# Last updated: 2026-04-02
---

thesis: >
  Reading production agent source code alongside academic curriculum, rebuilding each
  layer in ~100 lines of Python, reveals systematic gaps between what's taught and
  what's built — and the methodology of reading itself is an unsolved design problem.

status: validated

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
  notes/00-source-validation-audit.md (§ claw-code vs CC TS compaction discrepancy)
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
  notes/00-source-validation-audit.md (§ Key discoveries)
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
