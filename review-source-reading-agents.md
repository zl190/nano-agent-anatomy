# Review: Multi-Agent Source Code Reading at Scale

**Status:** Draft v0 — 2026-04-01
**Scope:** How should AI agents read large codebases? Survey of approaches, our experience, experiment design, optimization opportunities.

---

## 1. Problem Statement

Reading a large codebase (50K-500K+ lines) is a prerequisite for almost every downstream task: bug fixing, feature development, architecture understanding, code review, migration. Yet current LLM agents face a fundamental constraint: **context window is finite, codebases are not**.

A single agent on a 50K+ line codebase fills 80-90% of its context window just loading relevant files, leaving almost no headroom for reasoning (Bruniaux 2026). At 500K lines (e.g., Claude Code's own TypeScript source), single-agent reading is physically impossible.

**The core question:** What is the optimal multi-agent architecture for reading and understanding a large codebase?

---

## 2. Landscape: Existing Approaches

### 2.1 Single-Agent Strategies

| Approach | Mechanism | Limitation |
|----------|-----------|------------|
| **Repo Map (Aider)** | tree-sitter AST → dependency graph → graph ranking → token-budgeted summary | Lossy compression; no deep reading; ranking is heuristic |
| **Codebase Packing (Repomix)** | Entire repo → single AI-friendly file with token counts | Exceeds context at scale; no selective reading |
| **Plan Mode (Claude Code)** | Read-only exploration with Glob/Grep/Read tools | Serial; context fills during exploration |
| **RAG + Embeddings** | Pre-embed codebase → retrieve relevant chunks | Requires preprocessing; retrieval quality varies; stale embeddings |

**Consensus shift (2025→2026):** The field moved from "RAG everywhere" to **agentic search** — letting agents use traditional tools (grep, file read) rather than pre-embedding. Modern 1M-token windows make this viable for medium codebases but still insufficient for large ones.

### 2.2 Multi-Agent Strategies

| Approach | Architecture | Coordination | Quality Control |
|----------|-------------|--------------|-----------------|
| **Our SOP v1** | Scout → Reader×N → Synthesizer | Scout provides file paths | None |
| **Addy Osmani's Orchestra** | Orchestrator → Specialists → @Reviewer | Dependency graph, task list | Plan approval, Reviewer per 3-4 builders, Reflection |
| **MindStudio Pipeline** | Orchestrator → Sub-agent extractors → Consolidator | Parallel batch (5-10), JSON schema | Validate output before upstream, token cap, goal-driven exit |
| **Codebase Analyzer Agent** | Code Analyzer + Task Specialist | AutoGen conversation, max 3 review cycles | Peer review, self-assessment, convergence logic |
| **Claude Code Agent Teams** | Team Lead → Teammates (isolated worktrees) | File-based mailbox, shared task list | Dependency tracking, file locking |
| **SoA (Self-Organized Agents)** | Dynamic agent multiplication by complexity | Independent operation + seamless collaboration | Each agent manages constant code volume |
| **Lingma SWE-GPT** | Understanding → Localization → Patching (3 sub-agents) | Sequential pipeline | Stage-specific evaluation |

### 2.3 Synthesis: The Design Space

We identify **6 orthogonal dimensions** that define a source-reading agent system:

| Dimension | Options | Trade-off |
|-----------|---------|-----------|
| **1. Mapping strategy** | File list / AST repo map / Dependency graph / Embedding index | Accuracy vs. cost |
| **2. Split granularity** | By file / By directory / By concept-layer / By dependency cluster | Coherence vs. parallelism |
| **3. Reader budget** | Fixed lines / Fixed tokens / % of context window / Adaptive | Simplicity vs. scalability |
| **4. Output schema** | Free text / Structured JSON / Typed extraction + interpretation layers | Flexibility vs. verifiability |
| **5. Quality gates** | None / Schema validation / Reviewer agent / Human checkpoint | Speed vs. reliability |
| **6. Synthesis method** | Single pass / Goal-driven / Iterative with reflection | Cost vs. depth |

No existing approach explores the full design space. Most systems optimize 2-3 dimensions and leave the rest at defaults.

---

## 3. Our Experience: What We Know

### 3.1 Validated Findings (N=1, claw-code Python rewrite, 2138 lines)

| Finding | Evidence | Confidence |
|---------|----------|------------|
| Scout → Reader×N → Synthesizer beats single agent | Single agent failed (context overflow at 6 min); 4 parallel agents succeeded (~1.5 min each) | Medium (N=1, small scale) |
| Giving exact file paths beats letting agents search | Observed: agents waste 30-50% of tool calls on search when not given paths | Medium (qualitative) |
| 3-8 files per reader is sweet spot | >8 files → agent starts summarizing instead of analyzing | Low (single observation) |
| Concept-based splitting > file-based splitting | Readers grouped by layer produced more coherent output than readers given random file sets | Low (qualitative) |

### 3.2 Gaps Identified by Self-Audit (PUA Review)

| Gap | Severity | Root Cause |
|-----|----------|------------|
| Scout produces file list, not structural map | High | Didn't know about aider's repo map approach |
| "2000 lines max" hardcoded from single experiment | High | Overfitted to claw-code's size |
| No output validation between stages | High | "Trust the model" assumption |
| No persona — reader doesn't know its perspective | Medium | Didn't separate extraction from interpretation |
| Synthesizer has no procedure or template | High | Under-specified; relied on model capability |
| N=1 validation claimed as "validated" | Medium | Premature generalization |

### 3.3 Unique Contributions We Can Make

| Contribution | Why unique |
|-------------|-----------|
| **Panoramic framework mapping** | Template/Persona/Procedure/Enforcement applied to source reading — no one else has this lens |
| **Cross-validation protocol** | Reading same codebase via original TS + Python rewrite + Rust port — 3 independent views |
| **Scale stress test** | Same SOP on 2K lines (claw-code) vs 513K lines (CC TS) — measures scaling behavior |
| **Cost-quality frontier** | Model tiering experiment: Haiku extraction vs Sonnet extraction vs Opus extraction |
| **Practitioner grounding** | Not synthetic benchmark — real codebase, real reading goal, real output (blog + skill) |

---

## 4. Experiment: SOP v1 vs v2

### 4.1 Research Question

**Does adding structured output schema, architecture persona, and validation gates (SOP v2) improve multi-agent source reading quality over free-form output (SOP v1)?**

This tests three v2 additions simultaneously: JSON schema (dimension 4 in our design space), validation gates (dimension 5), and persona assignment. Cost is held constant (same model, same file splits).

### 4.2 Experimental Setup

**Codebase:** Claude Code TS source (513K lines, 1892 files).

**Conditions (N=1 per condition, same-day execution):**

| | SOP v1 (Baseline) | SOP v2 (Treatment) |
|---|---|---|
| Output format | Free-form Markdown | JSON with typed schema |
| Persona | None | Architecture perspective |
| Quality gate | None | JSON schema validation |
| Model | Sonnet x6 readers | Sonnet x6 readers |

**Protocol:** Blind evaluation — outputs randomly assigned to labels A/B, evaluated by independent agent with no knowledge of condition mapping. Unblinding revealed: A = v1, B = v2.

### 4.3 Results

**Per-dimension averages (6 readers, 1-5 Likert scale):**

| Dimension | v1 | v2 | Delta | Winner |
|---|---|---|---|---|
| Extraction Completeness | 4.50 | **4.83** | +0.33 | v2 |
| Pattern Depth | **5.00** | 4.00 | -1.00 | v1 |
| Evidence Quality | 3.33 | **4.67** | +1.33 | v2 |
| Cross-Reference Quality | 4.33 | 4.33 | 0.00 | Tie |
| Actionability | **5.00** | 3.83 | -1.17 | v1 |

**Reader preference:** v1 preferred 5/6 readers + synthesis (6-1 overall).

**Automated metrics:**

| Metric | v1 | v2 |
|---|---|---|
| JSON Parseable | 0/6 | 6/6 |
| Named Symbols | 91 | 202 (2.2x) |
| Evidence Citations (file:line) | 47 | 107 (2.3x) |
| Confidence Tags | No | Yes |
| Cost | ~$3.00 | ~$3.00 |

### 4.4 Interpretation

v2's structured schema improves the mechanical dimensions (extraction +0.33, evidence +1.33) but degrades the interpretive dimensions (pattern depth -1.00, actionability -1.17). The JSON format constrains output toward catalog-like descriptions, suppressing the narrative insight that makes source reading valuable ("what would I learn from reading this code that I couldn't learn any other way?").

The core trade-off: **structure aids verification; freedom aids insight.** v2 is better for building downstream tooling (navigators, dependency graphs). v1 is better for human understanding.

### 4.5 Recommended v3 Design

Separate extraction from interpretation:

| Phase | Format | Model |
|---|---|---|
| Extraction | JSON schema (v2-style) | Haiku (mechanical) |
| Interpretation | Free-form Markdown (v1-style) | Sonnet/Opus (creative) |
| Validation | Gate on extraction only | Schema check |

### 4.6 Threats to Validity

- **N=1 per condition** — no variance estimate; results could be stochastic
- **LLM evaluator** — may systematically prefer prose over structured output
- **Blinding imperfect** — format difference (Markdown vs JSON) visible to evaluator
- **v1 not instrumented** — token/timing comparison is estimated, not measured

Full experiment report: `experiment/report/experiment-report.md`

---

## 5. Available Benchmarks

| Benchmark | Relevance | Usable? |
|-----------|-----------|---------|
| **LoCoBench** | Directly relevant — 8 task types including "architectural understanding" and "code comprehension", 10K-1M token contexts, 17 metrics including ACS and DTA | Yes — best fit. Has TypeScript tasks. |
| **LoCoBench-Agent** | Interactive version — agent uses tools to explore, not just context window | Yes — more realistic for our multi-agent setup |
| **RepoQA** | Needle-function search in 50 repos, 5 languages, 500 tests | Partial — tests retrieval, not synthesis |
| **CrossCodeEval** | Cross-file code completion, 4 languages | Partial — completion not understanding |
| **CodeScaleBench-Org** | 220 org-level tasks requiring cross-repo navigation | Yes — but tasks are SDLC, not reading |
| **SWE-bench** | Issue resolution, not reading comprehension | No — wrong task type |

**Recommendation:** Use **LoCoBench-Agent** as primary benchmark (directly measures code understanding quality at scale), supplement with **RepoQA** for retrieval accuracy, and our **CC-TS ground truth** for practitioner-grounded evaluation.

---

## 6. Optimization Opportunities

### 6.1 Low-Hanging Fruit (implement in days, high impact)

| Optimization | Expected Impact | Effort | Evidence |
|-------------|----------------|--------|----------|
| **JSON schema + validation gate between Reader and Synthesizer** | Catch garbage before synthesis; MindStudio reports "most impactful single change" | 1 day | MindStudio production data |
| **Token-based budget (not line-based)** | Scale to any codebase size without parameter tuning | 2 hours | Aider, Claude Code guide both use token budget |
| **Scout outputs Reader assignment (not just file list)** | Eliminate human step of deciding how to split | 2 hours | Already doing this informally; formalize |
| **Model tiering: Haiku for extraction, Opus for synthesis** | 10-20x cost reduction on extraction with minimal quality loss | 1 hour | MindStudio reports "10-20x cost reduction" |

### 6.2 Medium Effort (implement in 1 week, medium-high impact)

| Optimization | Expected Impact | Effort | Evidence |
|-------------|----------------|--------|----------|
| **AST-based repo map for Scout** | Dependency-aware splitting; better Reader assignments | 3 days | Aider's core innovation; tree-sitter available for TS/Python/Rust |
| **Persona-specialized Readers** | Different perspectives extract different insights from same code | 2 days | Codebase Analyzer Agent's dual-role design |
| **Reflection step after each Reader** | Capture surprising findings, update Scout's map | 1 day | Addy Osmani's Orchestra pattern |
| **Goal-driven Synthesizer with exit condition** | Stop when question answered, not when all files read | 2 days | MindStudio's goal-driven exit |

### 6.3 Research Frontier (open questions, high uncertainty)

| Question | Why Hard | Potential Approach |
|----------|----------|-------------------|
| **Optimal split granularity** | Depends on codebase structure, task, model capability | Adaptive: start coarse, refine where Reader confidence is low |
| **Cross-agent information sharing** | Readers are parallel but might benefit from early results | Agentic pub-sub: Reader publishes "discovered API X", others subscribe |
| **Incremental reading** | Full re-read on code change is wasteful | Diff-aware: only re-read changed files + dependents (aider's graph helps) |
| **Multi-language codebases** | Different languages need different AST parsers, different reading strategies | Language-specialist Readers with shared synthesis |
| **Reading for what?** | Reading for "bug fixing" vs "architecture review" vs "onboarding" needs different depth/focus | Task-conditioned personas + adaptive budget |

---

## 7. Proposed Contribution

### What this review adds to the field:

1. **First systematic comparison** of multi-agent source reading architectures (6 approaches, 6 dimensions)
2. **Panoramic framework lens** — Template/Persona/Procedure/Enforcement as analytical tool for agent workflow design (novel framing)
3. **Practitioner-grounded evaluation** — real 513K-line codebase with cross-validation against 3 independent implementations
4. **Ablation study design** — isolating the contribution of each optimization (map, budget, gate, persona, model tier)
5. **Cost-quality frontier** — first systematic measurement of $/quality trade-off for source reading agents

### What this review does NOT do:
- Not a general survey of LLM agents for SE (see Fudan survey, Vibe Coding survey)
- Not a benchmark paper (uses existing benchmarks)
- Not a tool paper (workflow design, not implementation)

---

## 8. Key References

### Benchmarks
- LoCoBench / LoCoBench-Agent (arxiv:2509.09614, 2511.13998) — long-context code understanding, 17 metrics
- RepoQA (arxiv:2406.06025) — needle-function search, 500 tests, 5 languages
- CrossCodeEval (NeurIPS 2023) — cross-file code completion
- CodeScaleBench (Sourcegraph 2026) — 370 org-level SE tasks
- SWE-bench+ (OpenReview) — enhanced issue resolution

### Multi-Agent Architectures
- Addy Osmani, "The Code Agent Orchestra" (2026) — role separation, reflection, Ralph loop
- MindStudio, "Sub-Agents for Codebase Analysis" (2026) — validated output pipeline, model tiering
- Aider repo map (2023→2026) — tree-sitter AST, graph ranking, token budgeting
- SoA: Self-Organized Agents (arxiv:2404.02183) — dynamic agent multiplication
- Lingma SWE-GPT — 3-stage pipeline (understanding → localization → patching)
- Codebase Analyzer Agent (GitHub: wirelessr) — Code Analyzer + Task Specialist, max 3 cycles

### Surveys
- "A Survey on Code Generation with LLM-based Agents" (arxiv:2508.00083)
- "LLM-Based Multi-Agent Systems for SE" (ACM TOSEM, 2025)
- "A Survey of Vibe Coding with LLMs" (arxiv:2510.12399)
- "Large Language Models for Code Generation: A Comprehensive Survey" (arxiv:2503.01245)

### Practitioner Sources
- Claude Code Ultimate Guide (Bruniaux 2026) — agent teams, context budget, CLAUDE.md
- Claude Code Official Docs — common workflows, sub-agents, agent teams
- Claude Code Source Leak Analysis (multiple sources, March 2026) — ground truth for CC architecture
