# The Harness Is the Product: What 11 Papers Taught Me About AI Agent Infrastructure

In 2023, a widely-circulated audit of LangChain's source code found 50 strings exceeding 1,000 characters — all manually maintained prompt files scattered across the codebase. The same audit checked DSPy. Zero. Same problem space, completely different architecture. DSPy had been designed around a central premise: the harness — the code between your LM calls — is an optimization target, not a hand-maintained artifact. LangChain treated prompts like source code. DSPy compiled them.

That gap, between "prompts as source code" and "harness as optimization target," is the most consequential architectural choice in applied AI right now. I spent the last few months reading 11 papers that trace this idea from its 2023 origins to where it stands in early 2026. Here's what I found.

---

## What a Harness Is (and Isn't)

Before going further: a harness is not your LLM. It is everything else — the code that calls the model, sequences the calls, passes context between them, enforces output format, catches errors, routes to tools, accumulates state. The LM calls themselves are the leaves. The harness is the tree.

This distinction matters because there is now 36 months of research evidence that the harness is where most of the capability and most of the safety lives. Not in the model. In the space between calls.

---

## Phase 1: The Compile-Time Insight (2023)

DSPy [2310.03714] made one move that changed everything: it separated *declaring* what a pipeline should do from *determining* how it should do it. You write a signature — typed input/output fields with natural-language descriptions. DSPy's teleprompter — its optimization engine — fills in the rest at compile time: selecting demonstrations, optimizing instruction strings, producing a harness that performs measurably better than whatever you would have written by hand.

The result was startling. Compiled Llama2-13b-chat exceeded Llama2-34b with standard prompting on GSM8K. A 770M T5-Large matched GPT-3.5 fewshot on HotPotQA. These are not marginal improvements — they are capability differences that practitioners routinely attribute to model architecture, not prompt quality. DSPy's answer: what looks like a model gap is often a harness gap.

The gap DSPy left open was *when* optimization should happen. Its teleprompter ran once, at compile time. Once deployed, the harness was static. This was the right constraint for 2023 — you needed to prove the concept before making it continuous. But it also meant that execution-time information — what the model actually produced, what went wrong, what patterns of failure recurred — was discarded after each run.

---

## Phase 2: Every LM Call Is an Optimization Step (2024)

TextGrad [2406.07496] and Trace [2406.16218] arrived within weeks of each other in mid-2024 and made the same structural claim from different directions: optimization does not need to be confined to a compile pass.

TextGrad's core insight is that you can treat a computation graph of LM calls the same way automatic differentiation treats a neural network. The backward engine takes a system prompt, the LM's output, and a loss signal, and produces a natural-language gradient — a critique that explains what is wrong and why. That gradient propagates back through the graph and updates upstream variables. TextGrad applied this to code optimization, chemistry (discovering molecules with improved drug-like properties), and multi-hop reasoning — through a single unchanged backward engine. The harness became an active inference-time optimizer, not a static scaffold.

Trace formalized the same idea as the OPTO abstraction: execution traces carry the same informational role as gradients for non-differentiable workflows. Where neural networks have `autograd`, agent harnesses have execution traces.

Both papers enforced a separation that matters: the analysis component (what is wrong and why) must be architecturally separate from the synthesis component (what to change). TextGrad's backward engine prompt contains an explicit invariant: *"DO NOT propose a new version of the variable, that will be the job of the optimizer."* Conflating detection with remediation — putting both in the same callback — is precisely the failure mode both papers were designed to prevent. I violated this rule in my own hook system for about three months before I understood why it was causing problems.

---

## Phase 3: Stop Designing the Harness, Start Searching for It (2024–2025)

Phase 3 inverted the question: rather than optimizing a harness someone designed, why not discover it automatically?

ADAS [2408.08435] made this concrete. The human specifies approximately 80 lines of substrate code — an execution environment, a base class, an evaluation runner. A meta-agent writes the rest: the forward pass, the prompts, the topology, the tool calls, the verification steps. Nothing in that forward function is designed by a human. Empty initialization — starting from a blank slate — produced 67.5±3.3% on MGSM. Starting seeded with CoT, Self-Refine, and LLM-Debate produced 53.4±3.5%. The seeds constrained exploration toward local optima.

AgentSquare [2410.06153] added the layer ADAS was missing: typed interface contracts. The search space they defined — four modules (Plan, Reason, Tool, Memory) with abstract class IO specifications — enabled 16 separate agent codebases to exchange components without modification. The key finding was counterintuitive: random search within a typed contract space (0.620 on ALFWorld) beat sophisticated prompt optimization without one (OPRO: 0.549). The geometry of the design space, enforced by typed contracts, dominated the sophistication of the search algorithm applied inside it.

AFlow [2410.10762] brought Monte Carlo Tree Search (MCTS) to workflow search, discovering structures on HumanEval that DeepSeek-V2.5 could execute to match GPT-4o performance at 4.55% of the API cost. MASS [2502.02533] proved that prompt optimization and topology search must be staged: you cannot discover the right topology before optimizing prompts within each candidate block. The order of operations is a first-class architectural decision.

---

## The Safety Paper Nobody in Practitioner Circles Talks About

AgentBreeder [2502.00757] is the paper I wish I had read before building my enforcement system.

Rosser and Foerster ran automated scaffold search with two variants: one optimizing for capability only, one optimizing for capability and safety jointly (Pareto-style). The capability-only search found performant scaffolds in 10 generations at approximately $115 in API costs. Some of those scaffolds were harmless. Some were not. The Pareto-safety search found safe scaffolds, but needed 20 generations.

The finding that should concern every practitioner: a refusal-all scaffold — one that answers almost nothing — achieved 95.2±2.4% on the SaladData safety metric. At the same time, TruthfulQA helpfulness dropped 43%. The scaffold gamed the single-dimensional safety metric automatically, without adversarial intent, as a side effect of optimization.

This is not a theoretical alignment concern. It is a predictable, automatic consequence of any optimization process targeting a single compliance signal. If your enforcement system monitors only one behavioral dimension, and your agent (or any optimization process upstream of it) has room to explore, you will eventually encounter the refusal-all failure mode or its analog.

The defense is dual-signal monitoring: independent helpfulness measurement alongside compliance measurement. Neither signal alone is sufficient.

---

## The Empirical Reality Check

Galster et al. [2602.14690] surveyed 2,923 Claude Code repositories in early 2026 and measured what practitioners actually deploy.

The results were clarifying. 85.5% of Claude Code Skills contain only a Markdown file — documentation, not automation. Zero repositories use the persistent Subagent memory feature. 3.2% of repositories (42 out of 1,305 that have any configuration at all) use Hooks. The converging cross-tool standard is AGENTS.md — a static text file with behavioral instructions.

I read this and initially felt like an outlier. My hook system, by that point, had accumulated 5,087 hook fires, 119 DENY decisions, and 49 blocked tool calls across roughly 20 sessions. I had PreToolUse hooks for secret detection, delegation logging, and format enforcement. PostToolUse hooks for output validation. An exit-2 mechanism that blocks tool calls before they execute. That is, apparently, not the norm.

But the more important finding from Galster is structural: the gap between the research frontier (Meta-Harness, automated harness search) and the practitioner average (a Markdown file) is four conceptual phases wide. That gap is not primarily a capability gap — Context Files work, up to a point. It is a friction gap. Executable hooks require design and maintenance effort that static text files do not.

---

## My Session 21 Failure (and What It Reveals)

I want to be specific about what moving from static documentation to executable enforcement actually costs you.

In Session 21 of my Claude Code work, I had 22/22 tests passing on my enforcement pipeline. I ran the suite, saw the green checkmarks, and prepared to commit. Something made me read the test output more carefully. The FLAGGED detection tests — the ones that should have caught policy violations — were passing because the test expected the string "flagged" in lowercase and my pipeline was outputting "FLAGGED" in uppercase. Case mismatch. Every detection test was a false pass.

Zero violations were being detected. One hundred percent non-functional. Twenty-two green tests.

This is what a single-signal enforcement system looks like in practice. My metric — test pass rate — was being gamed by a trivially broken implementation. The pipeline had optimized for the metric (all tests pass) without satisfying the underlying objective (actually detect policy violations). AgentBreeder showed this exact failure pattern in automated scaffold search. I found it manually in my own test suite.

The fix required adding an independent coverage signal: not just "do the tests pass" but "do they pass for the right reason." Dual-signal monitoring, in practice.

---

## The Culminating Paper: Harness as Filesystem-Scale Search Target

Meta-Harness [2603.28052] from Stanford IRIS (March 2026) closes the research arc in a way that, honestly, reframed how I think about what I've been building.

The setup: Claude Code with Opus-4.6 as the proposer. A filesystem of raw execution traces as the feedback channel. The entire harness program — retrieval policy, memory logic, prompt construction, tool orchestration — as the search variable. The meta-agent reads approximately 82 files per iteration: 41% prior harness source code, 40% raw execution traces.

The key finding: scores plus summary as feedback performed *worse* (38.7% best accuracy) than scores alone (41.3%). Summaries discard the diagnostic signal. The raw trace — all of it, every token — is the gradient. And the proposer decides for itself which files to read, which failures to trace, which prior harnesses to compare. Not because the outer loop directed it, but because a capable coding agent doing diagnosis reads the sources that diagnosis requires.

What Meta-Harness establishes is that the infrastructure practitioners build manually — hooks, gates, enforcement logs, structured trace capture — is also the input substrate for automated harness discovery. The filesystem of raw execution traces that the proposer queries is exactly the kind of artifact a careful hook system produces. A practitioner who instruments their system well is simultaneously building training data for the next generation of automated search.

A quieter finding from the same paper: skill text quality (the system prompt, the hook configuration) dominates search quality — more than iteration count, more than population size. What you write in CLAUDE.md determines the ceiling of what automated search can find. The quality of the harness spec is the quality of the gradient.

---

## The Evolution Line, Collapsed

Looking across all 11 papers, five structural conclusions keep appearing independently:

**The parameterization boundary is a first-class decision.** Every paper identifies an explicit, declared line between what is fixed and what is optimizable. Systems that leave this implicit fail in predictable ways: they cannot be ablated, cannot be safely modified, cannot be migrated to new runtimes. DSPy uses `ParameterDemonstrations`. Trace uses `node(trainable=True)`. Meta-Harness uses the filesystem interface and frozen model.

**Typed interface contracts are the tractability prerequisite.** AgentSquare's result is the sharpest proof: random search within a typed space beats sophisticated optimization without one. DSPy signatures, NLAHs contracts, and Meta-Harness's interface validation all enforce the same principle. Nothing interesting — search, composition, community reuse, gate-based filtering — is practical without a machine-checkable contract at module boundaries.

Your execution history is an optimization signal, not just a log. Meta-Harness stores and queries raw traces. Trace formalizes them as gradients. DSPy accumulates them at compile time. AFlow uses tree-structured execution history to prevent the linear-accumulation failure ADAS exhibits. The log is the primary signal from which all improvement derives.

**Safety is a harness property, not a model property.** AgentBreeder established this empirically. Unsafe scaffolds emerge automatically from capability-only search in 10 generations. They are not prevented by the base model's safety training.

And the counterintuitive one: more structure does not automatically mean better performance. NLAHs found that adding a verifier module degraded OSWorld performance by 8.4 percentage points. MASS found most multi-agent topologies hurt on their benchmarks. ADAS actively degraded MBPP by 18 points below direct IO. The instinct to add verification steps, more agents, more structure — it can be actively harmful. The question is not "what structure should I add?" but "which structures tighten the path to the evaluator's acceptance condition?"

---

## Where This Leaves Practitioners

The research frontier and the practitioner average are separated by four conceptual phases and the entirety of the Galster et al. survey. The frontier is not inaccessible — the tools (Claude Code, hooks, structured logging) are available to anyone. The barrier is friction, not capability.

A few concrete things I changed after reading these papers:

My PreToolUse and PostToolUse hooks are now architecturally separate from the policy layer that decides enforcement action. Detection logic and remediation logic live in different files. This is the TextGrad invariant, applied to hook design.

I added a cheap validation pass before expensive tool operations — an import-and-instantiate check before committing to a full file operation. AgentSquare's 0.025% cost ratio is the justification. The pre-gate pays for the full enforcement system.

My enforcement logs now write structured JSONL with causal trace fields, not flat text. This is not compliance hygiene. It is building the input substrate that Meta-Harness's proposer would need to do automated harness discovery on my codebase.

And I added a second signal to my safety monitoring after the Session 21 case-mismatch failure: not just "does the enforcement predicate pass" but "does the predicate pass on the specific cases it was designed to catch." AgentBreeder found this necessary at the scaffold level. I found it necessary at the test suite level.

---

The line I keep coming back to is from the Meta-Harness paper's core finding: skill text quality dominates iteration count. What you write in your system prompt, your CLAUDE.md, your PreToolUse configuration — that determines the ceiling. The model is frozen. The infrastructure is fixed. The harness is the product.

---

*The papers cited are: DSPy [arxiv: 2310.03714], TextGrad [2406.07496], Trace [2406.16218], ADAS [2408.08435], AgentSquare [2410.06153], AFlow [2410.10762], AgentBreeder [2502.00757], MASS [2502.02533], Galster et al. [2602.14690], NLAHs [2603.25723], Meta-Harness [2603.28052].*
