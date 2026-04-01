# QC Report — Session 7 Blog Audit

**Reviewer:** Independent QC agent (clean context, did not write these posts)
**Date:** 2026-04-02
**Style guide:** `~/.claude/memory/knowledge/output-styles/blog-content.md`
**Source validation:** `notes/00-source-validation-audit.md`

---

## Post 1: blog-context-degradation.md

**Word count:** 2,099 (Deep dive range: 2000-4000. PASS.)

### AI Smell Check

Clean. No hedge cascades, no transition filler, no sycophantic openings. The prose reads as first-person practitioner voice throughout. Paragraph lengths range from 4 to 92 words — good variation.

Two minor flags:
- Line 55: "The reason is worth sitting with" — slightly precious phrasing. Not AI smell exactly, but reads a touch writerly. Minor.
- Line 153: "The cross-validation works in both directions" — this sentence plus the two that follow it have a summarizing cadence. Not a premature summary per se (it's in the final section), but it re-explains the thesis rather than adding new information.

**Verdict:** PASS.

### Factual Accuracy

| Claim | Source audit status | Verdict |
|-------|-------------------|---------|
| Nakanishi (2025): attention entropy Theta(log n) | Not in source validation audit. **No cross-validation.** | FLAG |
| Liu (2023): U-curve, lost in the middle | Referenced indirectly in audit (Wang lecture discusses benchmark issues). Liu (2023) is a well-known paper. | PASS (but no direct audit entry) |
| Laban (2025): 39% performance drop middle turns | Not in source validation audit. **No cross-validation.** | FLAG |
| Du (2025): position OOD / RoPE extrapolation | Not in source validation audit. **No cross-validation.** | FLAG |
| 30-50K threshold | Stated as empirical convergence of the above three papers. If papers aren't individually verified, the threshold claim is also ungrounded. | FLAG |
| 9-section compaction prompt | Source audit explicitly states: "9 sections is NOT cross-validated by any source except our own CC TS reading. Official Anthropic docs list 5 categories." | CAUTION — the post presents this as fact from "the TypeScript production source," which is valid since the post's framing is "I read the source code." But this is CC TS source only. |
| Sonnet 4.6 tool-call rate 2.79% | Not in source validation audit. Presumably from CC TS source reading. No external verification. | FLAG |
| 10.2% fleet savings from agent list move | Not in source validation audit. | FLAG |
| "claw-code" as Rust port | Source audit confirms: "64 file:line references across 9 notes." | PASS |
| LLM-based compaction (not deterministic) | Source audit confirms CC TS source has LLM-based compaction: "src/services/compact/prompt.ts — LLM-based compaction with 9 sections." | PASS |
| Dual trigger: message_count AND tokens | Not explicitly in source audit. Presumably from CC TS reading. | UNVERIFIED |
| SYSTEM_PROMPT_DYNAMIC_BOUNDARY | Not in source audit. From CC TS reading. | UNVERIFIED |

**Summary:** The post has two layers of claims — (1) research papers (Nakanishi, Liu, Laban, Du) and (2) CC TS source code findings. The source audit validates the CC TS source as genuinely read (Source 2: VALIDATED), so claims about what the code does are grounded. But the academic citations (Nakanishi 2025, Laban 2025, Du 2025) are **not individually verified** in the source validation audit. The 2.79% and 10.2% figures have no external source.

**Action required:** Either add these papers to the source validation audit, or add a disclaimer that the paper references are from the author's prior research and not re-verified for this post. The 2.79% and 10.2% figures need source attribution (which CC TS file or commit?).

### Structure

Follows the style guide structure:
1. Hook (lines 1-6) — the insight, no throat-clearing. PASS.
2. Context (lines 9-15) — why it matters. PASS.
3. Main content — four parts with concrete examples. PASS.
4. Takeaway (line 161) — single sentence. PASS.

No "In this post I will..." introduction. PASS.

### Voice

First-person throughout. "I spent three weeks," "I was confident," "I hadn't thought through." Commits to claims. Flags uncertainty explicitly ("I want to be precise here"). Includes personal experience (reading 513K lines, the surprise about claw-code vs production).

One weakness: the post is more essayistic than the reference models (Cunningham, Willison, Evans). It reads like a research narrative. This is a stylistic choice, not a failure, but it trends toward "academic" on the "Technical but not academic" axis.

**Verdict:** PASS.

### Length

2,099 words. Deep dive range (2000-4000). Appropriate for a multi-part argument with evidence.

**Verdict:** PASS.

### Hard Fails

- No research-institute/research-lab mentions. PASS.
- No AI smell patterns detected by regex or manual scan. PASS.

### Post 1 Verdict: PASS WITH FIXES

**Required fixes:**
1. Source-attribute the 2.79% tool-call rate and 10.2% fleet savings figures to specific CC TS files or evidence.
2. Acknowledge that Nakanishi (2025), Laban (2025), and Du (2025) are cited from prior research, not re-verified for this post — OR add them to the source validation audit.

---

## Post 2: blog-context-pollution.md

**Word count:** 1,310 (Standard range: 1000-2000. PASS.)

### AI Smell Check

Clean overall. No hedge cascades, no transition filler. Good paragraph variation (10-65 words).

One flag:
- Line 93: "I find it genuinely surprising that this doesn't exist yet." — the word "genuinely" is a mild intensifier that doesn't add information. Consider cutting to "I'm surprised this doesn't exist yet." Very minor.

**Verdict:** PASS.

### Factual Accuracy

| Claim | Source audit status | Verdict |
|-------|-------------------|---------|
| Softmax dilution as finite attention budget | Conceptual claim consistent with Nakanishi (2025) referenced in post 1. Same verification gap. | CAUTION |
| Lost in the middle / U-curve | Liu (2023) — same note as post 1. Well-known result. | PASS |
| Self-reinforcement of model's own prior output | No citation given. Presented as observation ("the most counterintuitive"). | FLAG — needs citation or explicit "this is my observation" framing |
| Claude Code has three compaction layers: compact.ts, autoCompact.ts, microCompact.ts | Source audit confirms: community source confirms "three-file compaction (compact.ts + autoCompact.ts + microCompact.ts)." | PASS |
| microCompact.ts does surgical compression; collectCompactableToolIds() | From CC TS source reading. Source 2 validated. | PASS (CC TS source) |
| ChatGPT has message editing / forking | Common knowledge, verifiable. | PASS |
| LangChain has memory.clear() but nothing selective | Claim about external framework. Not in source audit. | UNVERIFIED — low risk (easily checkable) |
| MemGPT has memory editing at long-term store level | Claim about external framework. Not in source audit. | UNVERIFIED — low risk |
| "No system does automatic correction-aware compression" | Broad negative claim. Difficult to verify. | CAUTION — qualifier like "no system I've found" would be safer |
| autoCompact fires at 95% capacity | Source audit confirms: "Auto-compaction at ~95% capacity" from sub-agents docs. | PASS |
| Two-stage classifier (fast single-token check, then CoT reasoning) | Source audit confirms: "Two-stage classifier: Stage 1 fast filter (single token), Stage 2 chain-of-thought" from Auto Mode blog. | PASS |

**Summary:** Most claims are grounded in CC TS source (validated) or well-known research. The self-reinforcement mechanism (line 18-19) lacks a citation and is presented as stronger than "I noticed this" — it reads like an established finding. The broad negative claim ("No system does automatic correction-aware compression") could use softening.

### Structure

1. Hook (lines 1-6) — the concrete experience of correction failing. Good. PASS.
2. Context (lines 8-11) — why it matters for production. PASS.
3. Main content — mechanisms, existing tools, proposed fix. PASS.
4. Takeaway (lines 101-102) — single sentence closing. PASS.

**Verdict:** PASS.

### Voice

Strong first-person voice. "Here is something that bothered me for weeks," "I found three mechanisms," "I spent time reading through." The prototype code section (lines 53-76) is a nice practitioner touch — showing rough working code, explicitly calling out its limitations.

The git analogy (lines 96-97) is well-chosen and feels natural, not forced.

**Verdict:** PASS.

### Length

1,310 words. Standard range. PASS.

### Hard Fails

None.

### Post 2 Verdict: PASS WITH FIXES

**Required fixes:**
1. Line 18-19: Either cite a source for "self-reinforcement" (model anchoring on its own prior output) or reframe as personal observation: "In my experience, when a model sees its own prior output..."
2. Line 94: Change "no current framework does anything about that automatically" or similar broad claims to "no framework I've found does..." — hedging a universal negative is not the same as hedge-cascading.

---

## Post 3: blog-credence-good-berkeley.md

**Word count:** 1,749 (Standard range: 1000-2000. PASS.)

### AI Smell Check

This is the post with the highest AI-smell risk due to its argumentative structure. Four subsections, each making a claim and connecting it to a thesis. The pattern could easily become robotic.

Assessment: it avoids the worst patterns. Each subsection has different internal structure (Bavor has two findings, Wang has a statistical deep-dive, Jiao is shorter and more conceptual, Brown connects to game theory). The lengths differ. The voice stays consistent.

Flags:
- Line 83: "That's the empirical footprint of a real phenomenon." — This sentence is doing work, but it's also the kind of phrase that sounds a bit like a TED talk conclusion. Minor.
- Line 86: "That's what formalization adds." — Same register. Two instances of the "That's [big claim]" construction in one section feels slightly pat.
- The four-lecture structure risks feeling like a listicle despite the connective tissue. The post is aware of this risk and handles it by varying section depth and by making the meta-insight section do genuine synthesis rather than just re-listing. Acceptable.

**Verdict:** PASS (borderline — the four-part structure is inherently risky but handled well enough).

### Factual Accuracy

| Claim | Source audit status | Verdict |
|-------|-------------------|---------|
| Bavor: "pay for a job well done" — outcome-based pricing | Source audit confirms: "Outcome-based pricing ('pay for a job well done')" from Nov 10 slide deck. | PASS |
| Agent Iceberg: ~30 submerged production concerns | Source audit confirms: "visible = LLM+RAG+tools; submerged = ~30 production concerns." | PASS |
| Wang: HumanEval SNR=1.1 | Source audit confirms: "HumanEval SNR=1.1, HumanEval+ SNR=0.50." | PASS |
| Wang: HumanEval+ SNR drops to 0.50 | Source audit confirms. | PASS |
| Wang quote: "models are bigger sources of inconsistency than benchmarks" | Source audit confirms. | PASS |
| pass^k metric definition | Source audit confirms: "pass^k (ALL k trials succeed) not pass@k." | PASS |
| Jiao: "Environment Feedback Aligned Models" | Source audit confirms: "Agentic models = 'Environment Feedback Aligned Models' (verifiable rewards)." | PASS |
| Brown: cheap-talk theorem — language communication provably useless in zero-sum minimax | Source audit confirms: "Cheap-talk theorem: In zero-sum minimax equilibrium, language communication is provably useless." | PASS |
| tau-bench adopted by Anthropic and OpenAI | Source audit confirms: "tau-bench... adopted by Anthropic and OpenAI as independent evaluation standard." | PASS |
| Akerlof 1970 lemons model | Well-known economics. No audit needed. | PASS |
| "I submitted a paper arguing software architectural quality is a credence good" | Personal claim. Not verifiable from audit. Consistent with project context (the paper is referenced in audit's "Agent-Economy Paper Cross-Validation" section). | PASS |
| "The thesis had no prior formalization in CS literature" | Strong claim. Not verified. | CAUTION — this is a claim about the state of a literature. If the paper has been submitted and reviewed, the author should know. But it's still an unverified universal negative. |
| Bavor's lecture was November, Wang's was October, Jiao's was September, Brown's was October | Source audit confirms: Nov 10 (Bavor), Oct 27 (Wang), Sep 29 (Jiao), Oct 20 (Brown). | PASS |

**Summary:** This is the best-sourced post. Every Berkeley lecture claim maps directly to the source validation audit entries. The one caution is the "no prior formalization in CS literature" claim, which is the kind of thing a reviewer would flag but which is defensible if the paper submission is real.

### Structure

1. Hook (lines 1-6) — the surprise of independent convergence. PASS.
2. Context (lines 10-16) — the thesis in one paragraph. PASS.
3. Main content — four subsections plus bonus. PASS.
4. Takeaway (lines 90-91) — single sentence. PASS.

**Verdict:** PASS.

### Voice

First-person throughout. "I submitted a paper," "I've since cited in several conversations," "I couldn't have constructed a better list." Takes sides (the economic interpretation is presented as the author's contribution, not as obvious). Includes personal failure/limitation: the paper was already submitted before this evidence appeared.

The audience check is the one concern: this post assumes familiarity with credence goods, adverse selection, Akerlof. The style guide says "Would an empirical researcher (not a CS major) understand this?" An empirical researcher in economics would. An empirical researcher in ML might not. The definitions are provided (search/experience/credence in paragraph 3), but the subsequent analysis assumes comfort with economic reasoning.

**Verdict:** PASS — the definitions are there, and the audience for this post is probably closer to the econ/policy side.

### Length

1,749 words. Standard range. PASS.

### Hard Fails

None.

### Post 3 Verdict: PASS

No required fixes. Two minor suggestions:
1. Line 83: Consider varying the "That's [big claim]" construction to avoid the repeated pattern.
2. The "no prior formalization in CS literature" claim (line 2) — if this can be softened to "no formalization I found" without undermining the paper's contribution, do so. If the paper explicitly makes this claim and it survived review, leave it.

---

## Post 4: blog-curriculum-gap.md

**Word count:** 1,242 (Standard range: 1000-2000. PASS.)

### AI Smell Check

Clean. Strong opening (line 7: "45 lectures across 3 semesters. Zero mention of context compression.") — punchy, declarative, no throat-clearing. No hedge cascades. No transition filler.

Flags:
- Line 9: "It's a serious curriculum. The instructors are serious people:" — the word "serious" appears twice in two sentences. Minor repetition, but reads as intentional emphasis rather than AI pattern.
- Lines 47-49: The three-mechanism paragraph (`autoCompact.ts handles...`; `microCompact.ts handles...`; `compact.ts handles...`) has a parallel structure that could read as listicle. But the sentences vary in length and the detail differs, so it passes.

**Verdict:** PASS.

### Factual Accuracy

| Claim | Source audit status | Verdict |
|-------|-------------------|---------|
| 45 lectures across 3 semesters | Source audit: F24 = 12 lectures, S25 = 12 lectures, F25 = 21 lectures. 12+12+21 = 45. | PASS |
| Zero mention of context compression across all iterations | Source audit explicitly confirms: "Context compression is a genuine curriculum gap across ALL Berkeley LLM agent courses." | PASS |
| CS294 Fall 2024, CS294/194-280 Spring 2025, CS294 "Agentic AI" Fall 2025 | Source audit confirms all three iterations with these names. | PASS |
| Instructors: Shunyu Yao (OpenAI), Noam Brown (OpenAI), Dawn Song (Berkeley), Clay Bavor (Sierra) | Source audit confirms these names and affiliations in lecture listings. | PASS |
| ReAct framework: A-hat = A union L | Source audit confirms: "ReAct formal definition: A-hat = A union L." From F24 L2. | PASS |
| Cheap-talk theorem in S25 | Source audit confirms: "L7 (Noam Brown, OpenAI): Multi-agent game theory." And F25 Oct 20 slides confirm cheap-talk theorem. | PASS |
| "Memory and Knowledge Management" in F25 covers HippoRAG | Source audit confirms: "HippoRAG (long-term RAG-based memory, NOT context compression)" for S25 L5. The blog says F25's Oct 1 lecture — source audit says F25 Oct 1 is unconfirmed for content. | CAUTION — blog says "I looked at what that lecture actually covers: HippoRAG." But source audit says F25 Oct 1 content is NOT verified. The HippoRAG finding is from S25 L5, not F25. This is a potential conflation. |
| Anthropic published engineering blog post about "context rot" | Source audit confirms: "'Context rot' — recall accuracy decreases as token count increases" from "Effective Context Engineering for AI Agents" (Sep 2025). | PASS |
| Three compaction mechanisms: compact.ts, autoCompact.ts, microCompact.ts | Source audit confirms. | PASS |
| Sub-agents return condensed summaries of 1,000-2,000 tokens | Source audit confirms from sub-agents documentation. | PASS |
| Yao's short-term/long-term memory split | Source audit confirms: "Short-term = context window... Long-term = external storage" from F24 L2 slides 37, 44-45. | PASS |
| 4/5 layers had a MOOC match | Source audit confirms: Layer coverage table shows 4 strong matches, 1 no match (context compression). | PASS |
| Tool loop -> Yao ReAct, Memory -> L2, Coordinator -> Wang AutoGen, Permissions -> Ben Mann ASL | Source audit confirms all four mappings. | PASS |
| Retrieval scoring: recency x importance x relevance | Source audit confirms from L2 slides 41-43. Blog says "Berkeley's L2 notes give the formula." | PASS |

**Summary:** Strong sourcing. One concern: the claim about F25's "Memory and Knowledge Management" lecture covering HippoRAG (line 41) may conflate the S25 HippoRAG lecture (L5, Yu Su) with the F25 Oct 1 lecture whose content was NOT verified per the source audit. The blog presents this as direct knowledge ("I looked at what that lecture actually covers"), but the audit says the F25 Oct 1 content is unconfirmed.

### Structure

1. Hook (lines 7-12) — the gap, stated immediately. PASS.
2. Context (lines 16-26) — what context compression is. PASS.
3. Main content — Berkeley coverage, why it matters, memory vs. compression distinction. PASS.
4. Takeaway — implicit in the final paragraph (lines 74-75), with an explicit repo link (line 79). The style guide says "one sentence the reader remembers." The final paragraph is more of a call-to-action than a distilled takeaway. | MINOR CONCERN |

No "In this post I will..." introduction. PASS.

**Verdict:** PASS with minor note on takeaway.

### Voice

Excellent practitioner voice. "I've been auditing Berkeley's LLM agent curriculum," "I started this audit while building a study journal," "The practical implication for anyone building agents." Commits to the claim (the gap is real, stated directly). Includes personal methodology (the 4/5 layer match).

The post does something the style guide values highly: it names what it doesn't know. "Not confirmed for Oct 1 lecture" (line 39). "I looked at what that lecture actually covers" implies direct reading. This is honest about evidence quality — good.

**Verdict:** PASS.

### Length

1,242 words. Standard range. PASS.

### Hard Fails

None.

### Post 4 Verdict: PASS WITH FIXES

**Required fix:**
1. Lines 40-41: The claim that F25's "Memory and Knowledge Management" lecture covers HippoRAG needs to be reconciled with the source audit. The audit says F25 Oct 1 content is **unconfirmed**. Either (a) confirm the content and update the source audit, or (b) soften the claim: "The closest lecture title is 'Memory and Knowledge Management' in Fall 2025. Based on the Spring 2025 version of this topic (Yu Su, L5), which covered HippoRAG, I expect similar content — not context compression."

**Minor suggestion:**
2. Add a one-sentence explicit takeaway at the end, before the repo link. The current ending is a practical recommendation, not a distilled insight.

---

## Consolidated Verdicts

| Post | Words | AI Smell | Accuracy | Structure | Voice | Verdict |
|------|-------|----------|----------|-----------|-------|---------|
| blog-context-degradation.md | 2,099 | PASS | FLAGS (academic citations unverified, 2.79%/10.2% unsourced) | PASS | PASS | **PASS WITH FIXES** |
| blog-context-pollution.md | 1,310 | PASS | FLAGS (self-reinforcement uncited, broad negative) | PASS | PASS | **PASS WITH FIXES** |
| blog-credence-good-berkeley.md | 1,749 | PASS | PASS (all Berkeley claims verified) | PASS | PASS | **PASS** |
| blog-curriculum-gap.md | 1,242 | PASS | FLAG (F25 HippoRAG conflation) | PASS (minor takeaway weakness) | PASS | **PASS WITH FIXES** |

## Required Fixes Before Publish

### blog-context-degradation.md
1. **Source-attribute specific numbers.** The 2.79% tool-call rate and 10.2% fleet savings need a source annotation — even if it's just "(from CC TS source: [filename])" inline or a footnote.
2. **Academic citation gap.** Nakanishi (2025), Laban (2025), and Du (2025) are not in the source validation audit. Either verify them and add to the audit, or add a note: "These citations are from my earlier literature review and were not re-verified for this post."

### blog-context-pollution.md
1. **Self-reinforcement claim (line 18-19).** Add citation or reframe as observation. Current phrasing presents it as established fact without source.
2. **Broad negative (line 98).** Soften "no current framework" to "no framework I've found."

### blog-curriculum-gap.md
1. **F25 HippoRAG conflation (lines 40-41).** Reconcile with source audit. The audit says F25 Oct 1 content is unconfirmed; the blog presents it as read. Fix the claim or confirm the source.

### blog-credence-good-berkeley.md
No required fixes. Two minor style suggestions noted above.

---

## Cross-Post Observations

**Strengths across all four posts:**
- Zero AI smell patterns detected (automated and manual scan)
- Consistent first-person practitioner voice
- Good paragraph length variation (4-111 words)
- Every post starts with insight, not throat-clearing
- No forbidden names (research-institute/research-lab)
- No hype words, no sycophantic patterns

**Recurring pattern to watch:**
- The posts rely heavily on CC TS source code as a primary source. The source audit validates that the code was genuinely read, but individual claims from the code (2.79%, 10.2%, specific function names) are inherently single-source. This is fine for a practitioner blog (the author read the code), but if any of these posts are adapted for academic submission, the single-source claims need flagging.
- Three of four posts use the three-mechanism framework (softmax dilution, lost-in-the-middle, position OOD). This is good for coherence across the series but creates a dependency: if any of the three academic sources (Nakanishi, Liu, Du) turns out to be mischaracterized, all three posts need revision.

**Gate status:** 3 posts PASS WITH FIXES, 1 post PASS. No FAILs. All fixes are addressable without structural rewrites.
