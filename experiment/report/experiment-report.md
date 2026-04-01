# Experiment Report: SOP v1 vs v2 for Multi-Agent Source Code Reading

**Date:** 2026-04-01
**Status:** Final

---

## 1. Experiment Design Summary

**Research question:** Does adding structured output schema, architecture persona, and validation gates (SOP v2) improve multi-agent source code reading quality compared to free-form output (SOP v1)?

**Codebase:** Claude Code TypeScript source (513K lines, 1892 files)

**Conditions:**

| | SOP v1 (Baseline) | SOP v2 (Treatment) |
|---|---|---|
| Output format | Free-form Markdown | JSON with typed schema |
| Persona | None | Architecture perspective |
| Quality gate | None | JSON schema validation |
| Reader prompt | Minimal: file list + goal | Structured: schema + persona + extraction instructions |

**Controlled variables:** Same model (Sonnet), same 6 reader groups with identical file assignments, same codebase, same reading goal.

**Protocol:** 4-step pipeline with blinding:
1. Run v1 baseline (v2 already completed)
2. Randomly assign v1/v2 to labels A/B, copy to `experiment/blind/`
3. Independent blind evaluation by fresh agent (no knowledge of which is which)
4. Unblind and compile report

---

## 2. Unblinding

| Blind Label | Actual Condition |
|---|---|
| **A** | **SOP v1** (free-form Markdown, no schema, no persona, no gate) |
| **B** | **SOP v2** (JSON schema, architecture persona, validation gate) |

The blind evaluator preferred **A (v1)** overall, choosing it for 5/6 individual readers and the synthesis. This was the opposite of the hypothesis that v2's structure would produce better output.

---

## 3. Per-Dimension Score Comparison

### 3.1 Individual Reader Scores (1-5 Likert)

| Reader | Dimension | v1 | v2 | Delta |
|---|---|---|---|---|
| R1 Core Runtime | Extraction | 4 | **5** | +1 |
| | Pattern Depth | **5** | 4 | -1 |
| | Evidence | 3 | **5** | +2 |
| | Cross-Reference | 4 | **5** | +1 |
| | Actionability | **5** | 4 | -1 |
| R2 Tools | Extraction | 5 | 5 | 0 |
| | Pattern Depth | **5** | 4 | -1 |
| | Evidence | 4 | **5** | +1 |
| | Cross-Reference | 4 | 4 | 0 |
| | Actionability | **5** | 4 | -1 |
| R3 AI & MCP | Extraction | 4 | 4 | 0 |
| | Pattern Depth | **5** | 4 | -1 |
| | Evidence | 3 | **4** | +1 |
| | Cross-Reference | **5** | 4 | -1 |
| | Actionability | **5** | 3 | -2 |
| R4 UI & Terminal | Extraction | 5 | 5 | 0 |
| | Pattern Depth | **5** | 4 | -1 |
| | Evidence | 3 | **4** | +1 |
| | Cross-Reference | 4 | 4 | 0 |
| | Actionability | **5** | 4 | -1 |
| R5 State | Extraction | 5 | 5 | 0 |
| | Pattern Depth | **5** | 4 | -1 |
| | Evidence | 4 | **5** | +1 |
| | Cross-Reference | **5** | 4 | -1 |
| | Actionability | **5** | 4 | -1 |
| R6 Commands | Extraction | 4 | **5** | +1 |
| | Pattern Depth | **5** | 4 | -1 |
| | Evidence | 3 | **5** | +2 |
| | Cross-Reference | 4 | **5** | +1 |
| | Actionability | **5** | 4 | -1 |

### 3.2 Dimension Averages (across 6 readers)

| Dimension | v1 Mean | v2 Mean | Delta | Winner |
|---|---|---|---|---|
| Extraction Completeness | 4.50 | **4.83** | +0.33 | v2 |
| Pattern Depth | **5.00** | 4.00 | -1.00 | v1 |
| Evidence Quality | 3.33 | **4.67** | +1.33 | v2 |
| Cross-Reference Quality | 4.33 | 4.33 | 0.00 | Tie |
| Actionability | **5.00** | 3.83 | -1.17 | v1 |

### 3.3 Synthesis Scores

| Dimension | v1 | v2 | Winner |
|---|---|---|---|
| Extraction Completeness | **5** | 4 | v1 |
| Pattern Depth | **5** | 4 | v1 |
| Evidence Quality | **4** | 3 | v1 |
| Cross-Reference Quality | **5** | 4 | v1 |
| Actionability | **5** | 4 | v1 |

### 3.4 Reader Preference Tally

| Reader | Preferred | Rationale (key factor) |
|---|---|---|
| R1 Core Runtime | **v2** | Explicit symbol signatures + data flow edges |
| R2 Tools | **v1** | Exceptional production insights (sed interception, security 4:1 ratio) |
| R3 AI & MCP | **v1** | Broader coverage, "skills are agents in disguise" insight |
| R4 UI & Terminal | **v1** | "Game engine in disguise" narrative, non-obvious implementation details |
| R5 State | **v1** | 34-line store revelation, memory A/B test results, onChangeAppState pattern |
| R6 Commands | **v1** | Individual skill analysis, "What Tutorials Don't Teach" section |
| Synthesis | **v1** | Pattern density map, 10 surprising findings with depth, "What Tutorials Will Never Teach" |

**Overall: v1 preferred 6-1 (readers + synthesis)**

---

## 4. Automated Metrics Comparison

| Metric | v1 | v2 | Winner | Notes |
|---|---|---|---|---|
| JSON Parseable Readers | 0/6 | **6/6** | v2 | v2 designed for machine-readable output |
| Named Symbols Extracted | 91 | **202** | v2 | 2.2x more; v1 embeds symbols in prose |
| Patterns Identified | **128** | 45 | v1 | v1 identifies patterns inline throughout; v2 in discrete sections |
| Evidence Citations (file:line) | 47 | **107** | v2 | 2.3x more; v2 uses file:line format consistently |
| Labeled Surprises | 4 | **58** | v2 | v1 embeds surprises in narrative; v2 labels explicitly |
| Confidence Tags | No | **Yes** | v2 | v2 schema requires confidence on every claim |
| Total Output (bytes) | 186K | 195K | Comparable | Similar volume, different structure |

**Interpretation caveat:** The pattern/surprise count disparity is partly an artifact of format, not substance. v1 weaves insights throughout prose (hard to count automatically), while v2 isolates them in labeled fields (easy to count). The blind evaluator noted this explicitly: "A embeds surprising findings throughout 'Production insight' sections rather than in labeled 'surprise' sections."

---

## 5. Cost & Time Comparison

| Metric | v1 | v2 | Notes |
|---|---|---|---|
| Model | Sonnet x6 | Sonnet x6 | Same |
| Total Tokens | ~540K (est.) | 540,030 | v1 estimated from comparable output volume |
| Total Tool Uses | N/A | 333 | v1 logs not captured |
| Max Parallel Duration | N/A | ~348s (5.8 min) | v1 logs not captured |
| Cost Estimate | ~$3.00 | ~$3.00 | Same model, similar volume |
| Scout Overhead | None | Minimal (Explore agent) | v2 adds scout phase |
| Gate Overhead | None | 6 validation checks | v2 adds per-reader validation |
| Files Read | N/A | 189 | v1 not tracked |
| Lines Deep-Read | N/A | 81,084 (15.8% of 513K) | v1 not tracked |

**Limitation:** v1 was run without instrumentation (no token/timing logs captured). Cost estimates are based on comparable model usage and output volume. The lack of v1 metrics is itself a finding: SOP v1 had no instrumentation requirement; SOP v2 mandated metrics collection.

---

## 6. Key Findings

### 6.1 What v2 Improved

1. **Evidence quality (+1.33 on 5-point scale):** The largest improvement. JSON schema with explicit `evidence` arrays forced every claim to cite file:line references. v1 readers often made claims without specific citations.

2. **Extraction completeness (+0.33):** Structured symbol arrays captured 2.2x more named symbols with full signatures, dependencies, and types. v1 embedded symbols in prose, making them harder to verify and count.

3. **Machine readability:** 6/6 v2 outputs parse as valid JSON. This enables downstream tooling (codebase navigators, dependency graphs, verification pipelines) that v1's Markdown cannot support.

4. **Confidence calibration:** v2 tags every pattern claim with a confidence level. v1 presents all claims with equal implicit confidence.

5. **Instrumentation:** v2 mandated metrics collection (tokens, tool uses, timing, gate pass rates). v1 had no instrumentation, making retrospective analysis harder.

### 6.2 What v2 Made Worse

1. **Pattern depth (-1.00):** The most consistent regression. Every single reader scored lower on pattern depth under v2. The JSON schema constrained output to catalog-like descriptions. v1's narrative freedom allowed deeper exploration of *why* patterns exist and *what they mean* for practitioners.

2. **Actionability (-1.17):** v1 readers consistently produced "What Tutorials Don't Teach" and "Patterns We Can Adopt" sections. v2's structured output reads like an API reference -- useful for navigation but less for understanding.

3. **Synthesis quality:** v1 synthesis scored 5/5 on all dimensions; v2 scored 3-4. The narrative form enabled cross-cutting pattern analysis (pattern density map, surprise ranking) that JSON aggregation could not match.

### 6.3 What Didn't Change

1. **Cross-reference quality (tied at 4.33):** Both conditions identified cross-subsystem connections at similar quality. v2's explicit `cross_references` arrays and v1's narrative cross-cutting sections were equally effective.

2. **Cost (~$3.00 each):** Same model, similar token consumption. The schema/persona/gate overhead was negligible.

3. **Coverage:** Both conditions read the same files and produced similar output volume (~190K bytes).

### 6.4 The Core Trade-off

**v1 optimizes for human understanding.** Narrative prose, production insights, "what would I learn from reading this code that I couldn't learn any other way?" The evaluator called v1's output "the kind of output that justifies spending time reading source code."

**v2 optimizes for machine processing.** Structured data, verifiable citations, typed extraction. The evaluator noted v2 "would be better for building automated tooling on top of the reading (e.g., a codebase navigator, dependency graph, or verification pipeline)."

These are different goals. The experiment tested them against a human-oriented rubric ("could someone use this to navigate the codebase?"), which inherently favors narrative output.

---

## 7. Threats to Validity

| Threat | Severity | Mitigation | Residual Risk |
|---|---|---|---|
| **N=1 per condition** | High | Same codebase, same file splits, same model | No variance estimate; results could be stochastic |
| **Single evaluator (LLM)** | High | Blind protocol, detailed rubric, per-reader rationale | LLM evaluator may have systematic biases (e.g., prefer prose) |
| **Evaluator bias toward prose** | Medium | Rubric dimensions are specific; "actionability" and "extraction" are measurable | "Pattern depth" and "overall preference" may favor narrative |
| **v1 lack of instrumentation** | Medium | Output volume comparable; same model | Cannot confirm token/time parity |
| **Blinding imperfect** | Low | Evaluator saw "A=markdown, B=JSON" in format but not condition labels | Format difference itself reveals the treatment |
| **Rubric designed pre-experiment** | Low | Based on literature, not v1/v2 specifics | Dimensions may not capture all relevant quality aspects |
| **Same-day execution** | Low | Fresh sessions, no shared context | API-level variance (load, caching) possible |

**Most serious threat:** The evaluator is an LLM judging prose vs. structured JSON on a rubric that includes subjective dimensions. An LLM evaluator may systematically prefer the output format closer to its own training distribution (natural language prose). A human expert evaluation would be needed to confirm these findings.

---

## 8. Conclusion: Is v2 Worth the Additional Complexity?

**Short answer: Not as a wholesale replacement. Yes as a component.**

v2's structured schema delivers clear wins on evidence quality and extraction completeness -- the mechanical dimensions of source reading. These are real improvements: a claim backed by `commands.ts:449-468` is more useful than a claim backed by "the commands system." The validation gate ensures output is machine-parseable, enabling downstream automation.

But v2's schema constrains the very output that makes source reading valuable: non-obvious production insights that change how you think about building systems. The evaluator's preference for v1 was driven by pattern depth and actionability -- exactly the dimensions that justify the effort of reading source code rather than just reading documentation.

**Recommended SOP v3 design:**

| Phase | Format | Rationale |
|---|---|---|
| **Extraction** | JSON schema (v2) | Symbols, signatures, dependencies, file:line evidence |
| **Interpretation** | Free-form Markdown (v1) | Pattern depth, production insights, "what tutorials don't teach" |
| **Validation** | Gate on extraction only | Verify evidence exists; don't constrain narrative |

This separates the two concerns v2 conflated: **extraction** (what exists in the code) benefits from structure, while **interpretation** (what it means) benefits from freedom. The ideal output is v2's structured extraction feeding into v1's narrative analysis -- not one format replacing the other.

**Cost of v3:** Approximately 2x the current cost (extraction + interpretation passes), but the extraction pass could use a cheaper model (Haiku) since it's mechanical, keeping the premium model (Sonnet/Opus) for interpretation.
