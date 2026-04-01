# Pedagogical Research: "Learn by Rebuilding" Educational Projects

Research conducted 2026-04-01. Informs the design of nano-agent-anatomy.

---

## 1. Project-by-Project Analysis

### 1.1 Stanford CS336 — Language Modeling from Scratch

**Source:** [cs336.stanford.edu](https://cs336.stanford.edu/), [GitHub org](https://github.com/stanford-cs336), student blog posts

**What it is:** A 5-unit Stanford course (Spring 2024, 2025, 2026) where students build every component of an LLM from scratch: BPE tokenizer, transformer architecture, AdamW optimizer, training loop, FlashAttention2 in Triton, scaling laws, data processing on Common Crawl, and alignment via SFT/RLHF/DPO.

**Pedagogical structure:**
- **Bottom-up sequencing.** A1 (Basics) -> A2 (Systems) -> A3 (Scaling) -> A4 (Data) -> A5 (Alignment). Each builds on the previous; A2 explicitly tells students "copy your code from A1 as a starting point."
- **Constraint-driven learning.** Students may NOT use `nn.MultiheadAttention`, `nn.Transformer`, or most `torch.nn.functional` / `torch.optim`. Only `torch.nn.Parameter`, container classes, and `torch.optim.Optimizer` base class are allowed. This forces confrontation with what high-level APIs hide.
- **Adapter-pattern scaffolding.** Students implement arbitrary internals, then connect them through `tests/adapters.py` functions. Tests initially throw `NotImplementedError`. This gives freedom in implementation while enforcing correctness via snapshot tests against expected outputs.
- **Leaderboard motivation.** Assignments include competitive leaderboards (e.g., submit your perplexity on OpenWebText). This creates intrinsic motivation beyond grades.

**How it bridges theory/implementation:**
- Lectures precede assignments by ~1 week. Theory establishes "why," then assignment demands "how."
- The scaling assignment (A3) is unusual: students fit scaling laws by querying an API at small scale, then predict optimal hyperparameters for large-scale training. Theory (Chinchilla scaling laws) becomes a tool, not just knowledge.
- Percy Liang stated the motivation: "Researchers are becoming detached from the technical details of how LMs work. In CS336, we try to fix that by having students build everything."

**What it deliberately excludes:**
- Inference optimization (no KV cache, no speculative decoding)
- Deployment / serving
- Multi-modal inputs
- Agent systems

**Simplification vs accuracy trade-off:**
- The course does NOT simplify the algorithm. Students implement the real BPE, real RoPE, real FlashAttention2 kernel in Triton. What gets simplified is SCALE (train on TinyStories not WebText) and INFRASTRUCTURE (no distributed checkpoint, no fault tolerance).
- Key insight: **simplify the data and compute, not the algorithm.**

**What makes it work:**
- "Operating systems course" analogy — the pedagogical lineage is explicit. Like OS courses that build a kernel, CS336 builds an LLM.
- Minimal scaffolding forces genuine understanding. Unlike courses that provide 90% of the code with TODOs, CS336 provides adapter stubs and tests only.
- AI autocomplete is "strongly discouraged" — they recognize that outsourcing cognition to Copilot defeats the purpose.

---

### 1.2 nanoGPT / build-nanogpt / nanochat / microgpt (Karpathy)

**Source:** [nanoGPT](https://github.com/karpathy/nanoGPT), [build-nanogpt](https://github.com/karpathy/build-nanogpt), [nanochat](https://github.com/karpathy/nanochat), [microgpt blog](http://karpathy.github.io/2026/02/12/microgpt/)

**What they are (the Karpathy progression):**

| Project | Lines | Purpose | Year |
|---------|-------|---------|------|
| micrograd | ~150 (engine 94 + nn 60) | Autograd on scalars | 2020 |
| minbpe | ~400 (base 165 + basic 74 + regex 164) | BPE tokenizer | 2024 |
| nanoGPT | ~660 (model 330 + train 336) | GPT-2 training | 2023 |
| build-nanogpt | ~44 commits | Step-by-step GPT-2 reproduction | 2024 |
| microgpt | 200 lines, zero dependencies | Entire GPT in pure Python | 2026 |
| nanochat | ~15 modules | Full stack: pretrain + SFT + RL + chat UI | 2025 |

**Pedagogical philosophy:**
- Feynman's "What I cannot create, I do not understand."
- Karpathy explicitly distinguishes "reading" from "replicating": "you read a formula in the book and it makes perfect sense, but now close the book and try to write it down, and you will find this process is completely different."
- Learning "should look a lot more like a serious session at the gym than quick workout videos."
- Anti-"shortification": YouTube/TikTok give "the appearance of education" but are "really just entertainment."

**Structural patterns across the Karpathy repos:**

1. **Single-file clarity.** micrograd is one file. nanoGPT is two files. microgpt is one file. The constraint forces conceptual clarity.

2. **Progressive commit history.** build-nanogpt has 44 clean commits, each introducing one concept. The YouTube video walks through each commit. This is the "git log as curriculum" pattern.

3. **Production references in docstrings.** nanoGPT's model.py opens with:
   ```
   References:
   1) the official GPT-2 TensorFlow implementation released by OpenAI
   2) huggingface/transformers PyTorch implementation
   ```
   The code maps to the paper AND the production implementation.

4. **"Onion layer" progression.** microgpt blog has 6 files: train0.py through train5.py, each adding one layer of complexity. This is the most explicit version of "progressive layers."

5. **Verify against production.** micrograd tests against PyTorch. minbpe tests against tiktoken (GPT-4's tokenizer). nanoGPT reproduces GPT-2's loss curve. The nano version must MATCH the production version on some observable metric.

**The "nano vs production" gap, per Karpathy (from microgpt blog):**
- The gap is: data (32K names -> trillions of tokens), tokenizer (chars -> BPE), hardware (scalar Python -> GPU tensors), scale (4K params -> hundreds of billions).
- "None of them alter the core algorithm and the overall layout."
- **This is the key claim:** the nano version preserves algorithmic fidelity while simplifying everything else.

**What nanoGPT deliberately excludes:**
- Modern position encodings (RoPE, ALiBi) — uses absolute position embeddings
- Advanced optimizations (FSDP, gradient checkpointing)
- Post-training (SFT, RLHF, DPO)
- Inference optimization
- nanochat later adds some of these back, showing the progression path

**Why nanoGPT got 38K+ stars:**
- 600 lines total — readable in one sitting
- Reproduces GPT-2 loss curve (proves it's not a toy)
- Can train on Shakespeare in 3 minutes on a MacBook (instant gratification)
- Easy to hack — no abstractions, no config system, no model factories
- Companion video (2hr YouTube) for those who prefer watching

---

### 1.3 nano-vLLM

**Source:** [GeeeekExplorer/nano-vllm](https://github.com/GeeeekExplorer/nano-vllm), [HuggingFace blog](https://huggingface.co/blog/zamal/introduction-to-nano-vllm), [BoringBot analysis](https://boringbot.substack.com/p/nano-vllm-a-tiny-inference-engine)

**What it is:** ~1,200 lines of Python reimplementing vLLM's core inference engine. Built by a DeepSeek researcher as a personal project. Pure Python + Triton (no C++/CUDA extensions).

**What it implements from vLLM:**
- PagedAttention (simplified to manual Triton kernel with slot mapping)
- KV caching with paged memory management
- Continuous batching
- Prefix caching
- Tensor parallelism
- Torch compilation + CUDA graphs

**What it deliberately excludes:**
- Distributed serving
- Advanced scheduling
- Speculative decoding
- Full model compatibility (tested subset only)
- API server / production deployment stack

**Pedagogical approach: "intentional incompleteness"**
- The BoringBot analysis identifies THREE pedagogical layers:
  1. **Problem framing** — articulate real pain points (latency, VRAM, batching) BEFORE solutions
  2. **Mechanism isolation** — each optimization (KV cache, PagedAttention, continuous batching) is presented with its specific problem, not as a feature list
  3. **Code as clarification** — simplified pseudocode bridges theory and execution without production complexity

- The HuggingFace blog structures the walkthrough as:
  - Beginner: what is inference, why optimize
  - Intermediate: 6 core components (tokenization, KV cache, flash attention, decode, sampling, tensor parallelism)
  - Advanced: Triton kernels, CUDA graphs, compilation
  - Practical: Colab notebook

**Key pedagogical insight:** nano-vLLM's API mirrors vLLM's interface (`from nanovllm import LLM, SamplingParams`). **Same API, simplified internals.** This means learners can switch between nano and production without re-learning the interface.

**Performance validation:** 1,434 tokens/sec vs vLLM's 1,362 tokens/sec on RTX 4070. The nano version is actually FASTER on a single GPU — it only loses when you need distributed features.

---

### 1.4 vLLM (production reference)

**Source:** [vllm-project/vllm](https://github.com/vllm-project/vllm), [vLLM blog](https://blog.vllm.ai/)

**Educational content around vLLM:**
- The official blog published "Inside vLLM: Anatomy of a High-Throughput LLM Inference System" (September 2025) — a comprehensive architecture walkthrough
- "Paged Attention from First Principles" by Hamza El Shafie builds up from OS virtual memory analogies
- Data Science Dojo's "Memory Is the Real Bottleneck" (January 2026) covers the systems-level motivation

**How production vLLM compares to nano-vLLM:**
- vLLM: 100,000+ LOC, C++ + Python + CUDA extensions
- nano-vLLM: 1,200 LOC, pure Python + Triton
- The gap is 99% infrastructure (scheduling, fault tolerance, model compatibility, API serving) and 1% algorithm

**The OS analogy is everywhere:** PagedAttention is explicitly inspired by virtual memory paging. Production vLLM wastes <4% KV cache memory vs 60-80% in naive approaches. This analogy is the primary teaching tool in all educational content about vLLM.

---

### 1.5 Other "nano/mini" Educational Projects

**Karpathy's llm.c:**
- ~1,000 lines of C in the root file. GPT-2 training in raw C/CUDA.
- Philosophy: rejects PRs that improve performance by 2% but add 500 lines. Readability in root folder > marginal gains.
- Structure: root = clean readable code; `dev/` = scratch space for experimental kernels
- Produces GPT-2 and GPT-3 reproductions, verified against PyTorch reference
- ~7% faster than PyTorch Nightly despite being simpler

**Karpathy's LLM101n:**
- 17-chapter course structure from bigram models to multimodal transformers
- Progressive: bigrams -> micrograd -> MLP -> attention -> transformer -> tokenization -> optimization -> distributed -> fine-tuning -> deployment -> multimodal
- Builds "everything end-to-end from basics to a functioning web app similar to ChatGPT, from scratch in Python, C and CUDA"
- Minimal prerequisites — designed for accessibility

**Agent-specific educational projects:**

| Project | Approach | Limitation |
|---------|----------|------------|
| [pguso/ai-agents-from-scratch](https://github.com/pguso/ai-agents-from-scratch) | 10 lessons + 4 framework modules, JavaScript, local LLMs | Framework recreation (LangChain/LangGraph), not production reading |
| [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | 15 lessons, multi-modal (text+video+code), Azure-based | Vendor-locked, pattern-based (not from-scratch) |
| Boot.dev "Build an AI Agent in Python" | Full course, coding agent focus | Commercial, not open |
| Various blog tutorials ("baby Claude Code") | One-off posts, basic loop | Stop at Layer 1 (the tool loop). Never reach memory, compression, coordination. |

**Critical gap in agent education:** Every "build an agent from scratch" tutorial stops at the tool loop. NONE of them go beyond to cover persistent memory, context compression, multi-agent coordination, or permission systems. nano-agent-anatomy is the only project that attempts all five layers while referencing production source code.

---

## 2. Cross-Cutting Pattern Analysis

### 2.1 How Do the Best Projects Sequence Topics?

| Project | Sequencing | Logic |
|---------|------------|-------|
| CS336 | Bottom-up: Basics -> Systems -> Scaling -> Data -> Alignment | Build the model before optimizing it |
| nanoGPT | Bottom-up: model.py first, then train.py | Architecture before training loop |
| build-nanogpt | Bottom-up with 44 incremental commits | Empty file -> working GPT-2 |
| microgpt | Onion: train0.py -> train5.py (6 progressions) | Add one concept per layer |
| minbpe | Bottom-up with 5 exercises: Basic -> Regex -> GPT-4 match -> Special tokens -> Sentencepiece | Simplest version first, verify against production at each step |
| nano-vLLM | Beginner -> Intermediate -> Advanced -> Practical | Concepts before code, code before optimization |
| nano-agent-anatomy (current) | Layer 1-4: loop -> memory -> context -> coordinator | Runtime order (which matches execution flow) |

**Pattern:** All successful projects use **bottom-up sequencing**. None use top-down ("here's the full system, now let's understand each part"). The Karpathy progression (micrograd -> minbpe -> nanoGPT -> microgpt) is the most extreme: each project is a prerequisite for the next, across years.

### 2.2 How Do They Handle "Simplification vs Accuracy"?

Three strategies observed:

1. **Simplify scale, not algorithm** (CS336, Karpathy). Implement the real FlashAttention2 kernel, but train on TinyStories instead of WebText. Implement real BPE, but on 32K names instead of trillions of tokens.

2. **Mirror the production API** (nano-vLLM). Same interface (`from nanovllm import LLM, SamplingParams`), simplified internals. Learners can switch to production without re-learning.

3. **Verify against production** (minbpe -> tiktoken, micrograd -> PyTorch, nanoGPT -> GPT-2 loss). The nano version must MATCH the production version on some observable metric. This is the most powerful anti-toy pattern.

**nano-agent-anatomy currently uses strategy 1** (simplify scale: 5 files instead of 512K lines). It should also adopt **strategy 3** — verify each layer against the production source code.

### 2.3 How Do They Reference Production Systems?

| Pattern | Example | Strength |
|---------|---------|----------|
| Docstring citations | nanoGPT: "References: 1) official GPT-2 TF implementation, 2) HuggingFace" | Low-friction, always visible |
| Side-by-side comparison | nano-vLLM HuggingFace blog: table comparing vLLM vs nano-vLLM features | Makes the gap explicit |
| Verification tests | minbpe: output matches tiktoken exactly | Proves algorithmic fidelity |
| Scaling analysis | CS336 A3: fit scaling laws at small scale, predict large-scale behavior | Bridge between toy and production |
| "Real stuff" section | microgpt blog: catalogs every difference from production | Honest about what's missing |

**nano-agent-anatomy has the citations** (inline comments like "Production equivalent: conversation.rs (584 lines)") **but not the verification.** Adding verification (e.g., "our loop handles these 5 edge cases the same way production does") would be the highest-impact improvement.

### 2.4 Format and Delivery Patterns

| Project | Format | Delivery | Duration |
|---------|--------|----------|----------|
| CS336 | Lectures + assignments + leaderboard | Cohort, 10 weeks | ~200 hours |
| nanoGPT | Code-only repo | Self-paced | ~2 hours to read |
| build-nanogpt | Git commits + 4hr YouTube video | Self-paced | ~4 hours |
| microgpt | Blog post + 6 progressive files | Self-paced | ~1 hour |
| minbpe | Code + exercise.md + lecture.md + YouTube | Self-paced | ~3 hours |
| nano-vLLM | Code + HuggingFace blog + Colab | Self-paced | ~2 hours |
| LLM101n | 17 chapters (planned, incomplete) | Self-paced | Weeks |
| nano-agent-anatomy | Code + notes + ROADMAP | Self-paced | 6 weeks planned |

**Pattern:** The most successful projects (by stars, discussion, adoption) pair CODE with NARRATIVE. Code-only repos (nanoGPT) get attention because of Karpathy's reputation, but the highest-rated educational experiences (build-nanogpt, minbpe, CS336) always have accompanying explanations.

### 2.5 What Anti-Patterns Do They Avoid?

1. **"Tutorial hell" — guided copying without understanding.** CS336 avoids this with constraint-based learning (can't use nn.Transformer). minbpe avoids it with progressive exercises that build on each other. Karpathy avoids it by insisting "close the book and try to write it down."

2. **"Toy that doesn't teach real patterns."** Avoided by verification against production (minbpe -> tiktoken). Avoided by implementing the REAL algorithm at small scale (CS336: real FlashAttention2, just on smaller data).

3. **"All theory, no practice."** CS336 flips this: implementation-first, theory supports it. Karpathy's work is 95% code, 5% explanation.

4. **"Feature creep / premature abstraction."** nanoGPT has no config system, no model factory, no plugin architecture. This is deliberate. nanochat has a single `--depth` dial that auto-configures everything else.

5. **"Incomplete coverage that misrepresents the system."** microgpt blog has a "Real stuff" section that honestly catalogs every difference from production. This prevents learners from thinking the nano version IS the production version.

---

## 3. Synthesis: Patterns for nano-agent-anatomy

### 3.1 Structural Patterns to Adopt

**From CS336: Constraint-based learning**
- Currently nano-agent-anatomy allows all of anthropic's SDK. Consider constraining: "implement the tool loop using only `requests` / raw HTTP, not the Anthropic SDK." This would force understanding of the streaming protocol, tool_use block format, etc. (Aggressive but pedagogically powerful.)
- More practically: add adapter tests like CS336. Each layer should have 3-5 tests that verify behavior matches production. E.g., "when a tool is denied, the loop sends is_error=true with the deny reason" — test this.

**From Karpathy: Onion-layer progression files**
- microgpt's train0.py -> train5.py pattern maps perfectly to nano-agent-anatomy's layers. Consider:
  - `step0_loop_basic.py` — bare tool loop, no error handling, no limits
  - `step1_loop_production.py` — add iteration limits, permission checks, deny-as-error
  - `step2_memory.py` — add persistence
  - `step3_context.py` — add compression
  - `step4_coordinator.py` — add multi-agent
  - Each step is self-contained and runnable. Each adds exactly ONE concept.

**From minbpe: Exercise file with progressive difficulty**
- minbpe's exercise.md has 5 steps from "implement BasicTokenizer" to "match sentencepiece."
- nano-agent-anatomy should have an `exercise.md` for each layer:
  - Exercise 1: "Run loop.py. Give it a task that hits the iteration limit. What happens? Why is MAX_ITERATIONS=16 instead of infinity?"
  - Exercise 2: "Remove the permission check. Give the agent a task that writes to /etc/. What happens?"
  - Exercise 3: "Read conversation.rs lines 130-217. Find the PermissionOutcome::Deny path. Compare to our implementation. What did we miss?"

**From nano-vLLM: Mirror the production API**
- nano-vLLM uses `from nanovllm import LLM, SamplingParams` — same API as vLLM.
- nano-agent-anatomy could mirror Claude Code's internal API naming. E.g., if production calls it `QueryEngine`, our loop could export `QueryEngine` as an alias. If production's memory is `MEMORY.md`, ours already is.

**From build-nanogpt: Git log as curriculum**
- The 44 clean commits in build-nanogpt each introduce one concept. The commit history IS the learning material.
- nano-agent-anatomy's .claude/CLAUDE.md already mandates "one concept per commit" with `learn:` prefix. Strengthen this: the git log should read like a textbook table of contents.

### 3.2 Cross-Validation Patterns

The best courses connect THREE things: theory (papers/lectures), production code (real systems), and student implementation (nano version).

**Current state (honest assessment):** nano-agent-anatomy is cross-validated against 4 sources: CC TS leaked source, claw-code Rust port, Anthropic Academy/CCA, and Agent SDK. The MOOC (Berkeley CS294) is referenced by lecture number throughout the notes but was NOT cross-validated — no findings from the lectures were extracted, compared against code, or verified. This was self-diagnosed here and resolved by downgrading to 4-source cross-validation. MOOC references remain as suggested reading pointers only.

The ideal triangle (theory + production + student implementation) is partially achieved: production-to-nano is solid; theory column lists MOOC lecture numbers and papers as orientation only.

**Three-column mapping (MOOC column = suggested reading, not verified):**

| Layer | Theory (suggested reading) | Production (claw-code) | Nano (our code) | Verification |
|-------|----------------------------|----------------------|-----------------|--------------|
| Loop | MOOC L1-2; ReAct paper | conversation.rs:130-217 | loop.py | Denied tool -> is_error=true |
| Memory | MOOC L6; MemGPT paper | autoDream implementation | memory.py | Consolidation merges duplicates |
| Context | MOOC L8; context distillation lit | compact.rs:1-485 | context.py | Deterministic summary preserves key files |
| Coordinator | MOOC L7, L11; multi-agent survey | coordinatorMode.ts, XML protocol | coordinator.py | Decompose-execute-synthesize flow |
| Permissions | MOOC L4, L13; sandbox escape lit | permissions.rs:1-232 | permissions.py | Unknown tool -> deny (fail-secure) |

Each cell should be a link. Each "Verification" should be a runnable test. To upgrade MOOC column from "suggested" to "validated" requires actually watching the lectures and extracting concrete claims to compare.

### 3.3 What's Different About Agents vs LLMs That Changes the Pedagogy

This is the most important section for nano-agent-anatomy's design.

**LLMs are stateless functions. Agents have runtime behavior.**

| Dimension | LLM (nanoGPT) | Agent (nano-agent-anatomy) | Pedagogical implication |
|-----------|---------------|---------------------------|------------------------|
| Core abstraction | forward(x) -> logits | loop(messages) -> action | LLMs are math; agents are state machines |
| Verification | Loss curve matches GPT-2 | Behavior matches production | Can't just measure a number; must trace execution paths |
| Simplification target | Data and compute | Environment and scale | Agents need a simplified WORLD (mock tools, test scenarios), not just smaller data |
| Runtime dynamics | Training loop is deterministic | Tool calls create branching execution | Must test multiple PATHS, not just one output |
| Failure modes | Training diverges | Agent loops infinitely, leaks data, executes wrong tool | Must test SAFETY properties, not just correctness |
| Multi-component interaction | Layers are stacked sequentially | Layers interact at runtime (memory affects loop, compression affects memory) | Must test INTEGRATION, not just units |
| Time dimension | None (batch processing) | Sessions, persistence, consolidation | Must test ACROSS TIME (does memory persist? does compression lose information?) |

**This means nano-agent-anatomy needs different pedagogical tools than nanoGPT:**

1. **Scenario-based testing, not metric-based.** nanoGPT verifies via loss curve. nano-agent-anatomy should verify via scenarios: "Given this conversation, does the agent handle tool denial correctly? Does memory consolidation merge duplicates?"

2. **Execution traces, not just code.** For LLMs, reading model.py is sufficient. For agents, you need to SEE the runtime behavior. Consider: a `--trace` flag that prints the full message sequence, including tool calls, denials, and compression events.

3. **Adversarial exercises.** LLM education rarely tests adversarial inputs. Agent education MUST: "Give the agent a prompt that tries to bypass permissions. Does the deny path work?"

4. **Integration from the start.** nanoGPT's model.py and train.py are independent. nano-agent-anatomy's layers interact at runtime. The roadmap should include integration checkpoints earlier (not just Week 6).

### 3.4 Specific Recommendations for the Project Roadmap

Based on the research, here are structural changes:

**Current weakness:** The ROADMAP is time-based (weeks) but not verification-based. Each week has "Check: Can you explain X?" but no automated verification.

**Recommended additions:**

1. **Add a `tests/` directory with scenario tests for each layer.** Each test encodes a production behavior. This is the CS336 adapter pattern applied to agents.

2. **Add an `exercises/` directory with progressive exercises per layer.** This is the minbpe exercise.md pattern. Each exercise starts with "run this" and ends with "compare to production."

3. **Add "onion" progression files.** Instead of a single loop.py that has everything, provide loop_v1.py (bare minimum) through loop_v3.py (production-grade). Learners can diff between versions.

4. **Add a "Real stuff" section to each layer's learning note.** List what production does that we don't. This is the microgpt blog pattern. Prevents "I built an agent" false confidence.

5. **Add verification targets.** For each layer, define an observable behavior that must match production:
   - Loop: denied tool returns is_error with reason text (matches conversation.rs)
   - Memory: consolidation merges entries about the same topic (matches autoDream)
   - Context: deterministic summary extracts file paths and pending work (matches compact.rs)
   - Coordinator: workers get isolated message histories (matches scratch directory pattern)
   - Permissions: unknown tools default to highest permission (matches permissions.rs)

6. **Move integration earlier.** Current plan: integration in Week 6. Research shows the best courses integrate continuously. Add "integration checkpoint" at Week 3 (loop + memory + context should work together).

### 3.5 "Learn Anything" System Design — Meta-Pattern

Extracting from all projects, the meta-pattern for "learn X by rebuilding from scratch" has 7 components:

```
1. CHOOSE A REFERENCE SYSTEM
   - Must be real, production-grade, with observable behavior
   - nanoGPT -> GPT-2, minbpe -> tiktoken, nano-vLLM -> vLLM
   - nano-agent-anatomy -> Claude Code (claw-code)

2. IDENTIFY THE ALGORITHMIC CORE
   - Strip away scale, infrastructure, deployment
   - "None of them alter the core algorithm" (Karpathy)
   - Must be able to state: "the nano version preserves X while simplifying Y"

3. BUILD BOTTOM-UP IN LAYERS
   - Each layer is self-contained and runnable
   - Each layer adds exactly one concept
   - Can diff between layers to see what changed

4. VERIFY AGAINST THE REFERENCE
   - Each layer must match the reference on some observable metric/behavior
   - minbpe output == tiktoken output
   - nanoGPT loss curve == GPT-2 loss curve
   - nano-agent denied_tool behavior == production denied_tool behavior

5. PROVIDE PROGRESSIVE EXERCISES
   - Start with "run it and observe"
   - Progress to "modify and predict"
   - End with "compare to production source"
   - Each exercise has a concrete deliverable

6. MAKE THE GAP EXPLICIT
   - Document what production does that nano doesn't
   - "Real stuff" sections prevent false confidence
   - The gap IS part of the education

7. PAIR CODE WITH NARRATIVE
   - Code alone is necessary but insufficient
   - Learning notes explain WHY, not WHAT
   - The narrative connects theory, production, and implementation
```

This pattern is domain-independent. It could be applied to:
- nano-database (reference: SQLite or PostgreSQL)
- nano-compiler (reference: GCC or LLVM)
- nano-container (reference: Docker / containerd)
- nano-browser (reference: Chromium)
- nano-agent (reference: Claude Code) <-- this project

The key insight from this research: **the best "from scratch" projects are not toys that approximate real systems. They are PROBES into real systems — minimal implementations that preserve algorithmic fidelity and verify against production behavior.**

---

## 4. Sources

### Primary Sources (Repos Read)
- [nanoGPT](https://github.com/karpathy/nanoGPT) — model.py (330 lines), train.py (336 lines), README
- [micrograd](https://github.com/karpathy/micrograd) — engine.py (94 lines), nn.py (60 lines)
- [minbpe](https://github.com/karpathy/minbpe) — base.py (165), basic.py (74), regex.py (164), exercise.md, lecture.md
- [build-nanogpt](https://github.com/karpathy/build-nanogpt) — 44 commits, README
- [nanochat](https://github.com/karpathy/nanochat) — README, ~15 modules
- [llm.c](https://github.com/karpathy/llm.c) — README, philosophy discussion
- [LLM101n](https://github.com/karpathy/LLM101n) — 17-chapter outline
- [nano-vllm](https://github.com/GeeeekExplorer/nano-vllm) — ~1,200 lines Python
- [CS336 Assignment 1](https://github.com/stanford-cs336/assignment1-basics) — scaffolding structure
- [CS336 Assignment 2](https://github.com/stanford-cs336/assignment2-systems) — systems optimization
- [ai-agents-from-scratch](https://github.com/pguso/ai-agents-from-scratch) — 10 lessons + 4 modules
- [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) — 15 lessons

### Web Sources
- [CS336 course site (Spring 2025)](https://cs336.stanford.edu/spring2025/)
- [CS336 course site (Spring 2026)](https://cs336.stanford.edu/)
- [CS336 DeepWiki overview](https://deepwiki.com/stanford-cs336/assignment1-basics/1-overview)
- [Inside CS336 and Berkeley CS294](https://luluyan.medium.com/inside-stanford-cs336-and-berkeley-cs294-194-196-a-data-scientists-journey-into-llm-fundamentals-6410d3157625) — student perspective
- [CS336 course experience blog](https://galtay.github.io/blog/course-stanford-cs336-spring-2025/)
- [microgpt blog post](http://karpathy.github.io/2026/02/12/microgpt/) — pedagogical philosophy
- [Karpathy on learning](https://x.com/karpathy/status/1756380066580455557) — anti-shortification
- [nano-vLLM HuggingFace blog](https://huggingface.co/blog/zamal/introduction-to-nano-vllm) — architecture walkthrough
- [nano-vLLM BoringBot analysis](https://boringbot.substack.com/p/nano-vllm-a-tiny-inference-engine) — pedagogical design
- [vLLM blog: Anatomy](https://blog.vllm.ai/2025/09/05/anatomy-of-vllm.html) — production architecture
- [Paged Attention from First Principles](https://hamzaelshafie.bearblog.dev/paged-attention-from-first-principles-a-view-inside-vllm/)
