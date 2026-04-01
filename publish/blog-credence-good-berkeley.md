# Berkeley's Agent Course Accidentally Proves Software Quality is a Credence Good

I submitted a paper arguing software architectural quality is a credence good — the kind you can't evaluate even after you've paid for it. The thesis had no prior formalization in CS literature, which made the reviewers nervous. Then I watched Berkeley's Fall 2025 Agentic AI lectures. Four practitioners from four different companies, none of whom cite economic theory, none of whom were talking to each other about this, independently presented findings that map to credence good dynamics with uncomfortable precision.

They weren't trying to prove my thesis. They were reporting what they'd found in production.

---

## The Thesis in One Paragraph

In economics, goods split into three categories based on when buyers can evaluate quality. Search goods you can assess before purchase — you can read the label. Experience goods you can assess after use — you know if the restaurant was good. Credence goods you cannot assess even after consumption, because you lack the expertise or the counterfactual. A doctor's diagnosis. A mechanic's explanation of why you need a new transmission. Software architectural quality.

The argument in the paper is that agent software makes this problem acute in a way standard software doesn't. With a traditional application, a QA team can run test suites. With an agent, the quality you're buying is epistemic — how well does this system reason under uncertainty, handle novel inputs, fail gracefully? These properties don't have clean test coverage. They're non-verifiable. When quality is non-verifiable, the market exhibits adverse selection: sellers who cut corners can't be distinguished from sellers who don't, so buyers discount everyone, and sellers who invest in quality lose the incentive to do so. The formal machinery is Akerlof's 1970 lemons model, applied to a new domain.

That's the claim. Here's what Berkeley's practitioners found.

---

## Four Lectures, Four Pieces of Evidence

### 1. Bavor (Sierra): Outcome-Based Pricing is the Market Equilibrium

Clay Bavor's November lecture on deploying agents in production contained two findings that I'd have cited directly if the paper hadn't already been submitted.

The first is what he called "pay for a job well done" — the emerging pricing model for production agent deployments. Outcome-based contracts, where payment depends on whether the agent achieved the goal rather than on inputs consumed. Bavor presented this as a practical observation about what enterprise customers were willing to accept.

Credence good theory predicts exactly this. When buyers can't verify quality, price-per-input pricing collapses — sellers can pad inputs, buyers can't tell whether the work was necessary. The theoretical equilibrium is outcome-based contracting with third-party verification of results. Bavor found this empirically from the demand side of the market.

The second finding is the Agent Iceberg. Bavor presented a diagram: the visible surface of an agent deployment is the LLM plus some RAG plus a few tools. Submerged beneath it — roughly 30 distinct items — are the production concerns nobody sees: prompt injection defense, RBAC, compliance logging, PII detection, regression testing, memory management, fallback behavior. Twenty to thirty non-negotiable requirements that don't appear in demos, don't show up in benchmark scores, and can't be audited from outside the system.

A thirty-item catalog of non-verifiable quality dimensions. I couldn't have constructed a better list of credence good characteristics from theory alone.

### 2. Wang (Meta): The Information Asymmetry is Measurable

Sida Wang's October lecture on benchmark reliability produced a number I've since cited in several conversations: HumanEval signal-to-noise ratio equals 1.1.

To be precise about what that means: the variance in model performance across runs is nearly as large as the variance in performance between models. The signal from the benchmark barely exceeds the noise. On HumanEval+, the SNR drops to 0.50 — noise dominates signal. The conclusion Wang drew was that "models are bigger sources of inconsistency than benchmarks," meaning you can't cleanly attribute performance differences to what you think you're measuring.

For the credence good framing, this is a direct empirical measurement of information asymmetry severity. Buyers who use self-reported benchmark numbers to evaluate agent quality are in a genuinely terrible epistemic position. It's not that benchmarks are imperfect proxies for quality — that's trivially true. It's that the current benchmarks have essentially no discriminating power at the resolution buyers need to make procurement decisions.

Wang also discussed the `pass^k` metric: all k trials must succeed for credit, rather than any-k-succeeds. This is a harder bar, and it matters because production agents run repeatedly. If your agent passes a task on 7 out of 10 trials, you have a fragile system — one that will fail your customers at some predictable rate. `pass@k` (any pass counts) hides this fragility. `pass^k` (all must pass) surfaces it.

The conventional response to this finding is methodological: use better benchmarks, use `pass^k`, run paired comparisons to reduce variance. These are good engineering recommendations. But the economic implication is darker. The benchmarks that buyers actually use when making procurement decisions are the ones with SNR=1.1. Better benchmarks exist on research preprint servers. The market doesn't clear on research preprints — it clears on what marketing teams put in sales decks, which means it's been clearing on noise.

This is adverse selection in action. Sellers who invest in genuine quality cannot credibly demonstrate that quality over sellers who don't, because the measurement instrument lacks discriminating power. The incentive to invest in real quality deteriorates. The market converges toward the lowest quality that's indistinguishable from the highest quality — which, at SNR=1.1, is almost everything.

### 3. Jiao (NVIDIA): Supply-Side Response to the Credence Problem

Jiantao Jiao's September lecture on post-training for verifiable agents approached the problem from the other direction.

His framing: agentic models trained on verifiable rewards are "Environment Feedback Aligned Models." The key word is verifiable. Verifiable rewards require that you can determine, without ambiguity, whether the agent achieved the goal. Jiao noted that verifier quality is critical — false positives and false negatives in reward signals degrade training. The engineering challenge of building good verifiers is substantial.

From a market perspective, this is the supply-side response to the credence good problem. If you can train a model against rewards that can actually be verified, you've moved quality from the credence dimension toward the experience dimension. The quality is still invisible before deployment, but now there's a technical mechanism anchoring it to observable outcomes during training. Sellers who use this training approach can, in principle, offer stronger quality guarantees than sellers who don't.

Jiao didn't frame it this way. He was talking about RLVR methodology. But the economic logic runs underneath: verifiable rewards are the technical precondition for quality becoming observable.

### 4. Brown (OpenAI): Language Claims Don't Count

Noam Brown's October lecture on multi-agent game theory contained the most theoretically rigorous piece of evidence.

The cheap-talk theorem: in a zero-sum minimax equilibrium, language communication between agents is provably useless. An agent that can gain by lying will lie. Messages have no credible commitment, so rational recipients assign them zero informational weight. The theorem applies to adversarial multi-agent settings, but the implication generalizes.

For agent evaluation, the implication is direct: language claims about quality are not evidence of quality. A vendor who asserts that their agent is "robust," "reliable," or "enterprise-grade" has made no credible claim. The only valid evidence is outcomes — measured, third-party verified, repeated. This is what the cheap-talk theorem says, translated from game theory into procurement language.

Brown's context was adversarial AI agents in competitive settings. But the adversarial structure he describes is exactly the structure of the vendor-buyer relationship when quality is non-verifiable. Vendors have an incentive to overstate quality. Buyers can't verify claims. Rational buyers should discount verbal assurances to near-zero and demand outcome evidence. The game theory formalizes what should already be obvious, and finds it's not.

### Bonus: Third-Party Certification Begins

Berkeley's intro lecture by Dawn Song mentioned that τ-bench — Sierra's evaluation benchmark, introduced in Bavor's work — has been adopted by both Anthropic and OpenAI as an independent evaluation standard.

Credence good markets develop quality certification institutions when private contracting mechanisms fail. For professional services, this produces licensing boards and accreditation bodies. For financial products, it produces rating agencies (with their own problems, but that's a separate analysis). For agent quality, τ-bench represents an early move in this direction: an external benchmark that multiple major vendors have adopted, with `pass^k` as its primary metric.

This is preliminary. One benchmark, adopted by a few large players, is not a certification regime. But the economic pressure it responds to — buyers can't evaluate quality, so a neutral third party needs to — is the textbook credence good response. The fact that it emerged from a practitioner trying to solve a deployment problem, rather than from economists designing a market institution, makes it more interesting as evidence.

---

## The Meta-Insight

None of these lectures mentions credence goods. None mentions adverse selection, information asymmetry as an economic category, or Akerlof. The agent economics literature they cite, where it exists, is thin and mostly descriptive.

This is not a criticism. Bavor was reporting deployment findings. Wang was presenting statistical methodology. Jiao was explaining RLVR training. Brown was introducing game theory to an ML audience. They were each doing their jobs well.

The interesting thing about the convergence is that it's overdetermined. Any one of these lectures, in isolation, might be coincidence — maybe practitioners just happen to rediscover economic concepts. But four independent practitioners from Sierra, Meta, NVIDIA, and OpenAI, approaching quality verification from four different angles (pricing, measurement, training, game theory), arriving at findings that interlock into a coherent market structure analysis? That's the empirical footprint of a real phenomenon. The credence good problem in agent markets isn't a theoretical possibility. It's already shaping how serious practitioners design their systems.

The gap isn't in the empirical findings. It's in the theoretical vocabulary that would let the field accumulate those findings into actionable market structure insights. That's what formalization adds. Knowing that benchmark SNR=1.1 is a fact about measurement. Knowing that it implies buyers are operating under severe information asymmetry, which implies market failure, which implies specific institutional responses, is a different kind of knowledge. The economic framework provides the inference chain.

---

## The Takeaway

The market for agent quality will develop certification mechanisms by necessity — not because economists designed them, but because the alternative is buying from people who've learned to game the benchmarks they know buyers rely on.