# Source Validation Audit — 2026-04-01

Session 6 audit. Every claimed cross-validation source verified against actual evidence.

## Audit Summary

| Source | Claimed | Actual | Evidence |
|--------|---------|--------|----------|
| **claw-code** | Validated | **VALIDATED** | 64 file:line references across 9 notes |
| **CC TS leaked source** | Validated | **VALIDATED** | 24 file path references across 8 notes |
| **Anthropic Docs & Eng Blog** (was "Academy") | Validated | **VALIDATED** | 7 official sources read with URLs. Academy courses too basic; eng blog is the real source. |
| **Agent SDK** | Validated | **VALIDATED** | Full architecture verified: subprocess protocol, 10 hooks, 5 permission modes, subagent mechanics. |
| **Berkeley MOOC** | Suggested reading | **PARTIALLY VALIDATED** | Fall 2024 slides read (L1,L2,L3,L11). 4/5 layers strong match. No context compression coverage. 2025/2026 PENDING. |

**Current honest count: 4 validated + 1 partially validated (MOOC F24+S25+F25, 4/5 layers)**

**Key discoveries:**
1. "9-section compaction" is NOT cross-validated by any source except our own CC TS reading. Official Anthropic docs list 5 categories.
2. Context compression is a genuine curriculum gap across ALL Berkeley MOOC iterations (F24, S25, F25). No lecture covers it.
3. "Anthropic Academy" (Skilljar) is too introductory. Rename source to "Anthropic Docs & Engineering Blog."
4. Berkeley has 3 course iterations: F24 foundational, S25 advanced, F25 renamed "Agentic AI" with MCP/A2A/AgentBeats.
5. Game theory perspective (Noam Brown, S25 L7) provides formal basis for CC's consequence framing pattern.

---

## Source 1: claw-code (Rust port) — VALIDATED

64 specific references with file:line citations across 9 note files. Examples:
- `conversation.rs:130-217` — tool loop with permission check
- `compact.rs:1-485` — deterministic compaction
- `permissions.rs:1-232` — permission hierarchy
- `usage.rs` — token tracking, session cost

**Verdict:** Real cross-validation. Deeply read.

---

## Source 2: CC TS leaked source (513K lines) — VALIDATED

24 specific references with file paths across 8 notes. Examples:
- `src/services/compact/prompt.ts` — LLM-based compaction with 9 sections
- `src/tools/AgentTool/built-in/verificationAgent.ts` — "try to break it" verifier
- `coordinatorMode.ts` — coordinator as mode flag
- `swarmWorkerHandler.ts` — worker permission restrictions
- `FileEditTool`, `FileWriteTool`, `FileReadTool` — readFileState Map

**Verdict:** Real cross-validation. Deeply read.

---

## Source 3: Berkeley MOOC (CS294/194-196) — PARTIALLY VALIDATED

### Fall 2024 (llmagents-learning.org/f24)

Course page: https://rdi.berkeley.edu/llm-agents/f24
Slides: http://llmagents-learning.org/slides/
Student notes: https://github.com/rajdeepmondaldotcom/CS294_LLM_Agents_Notes_Fall2024

12 lectures. Slides actually read for L1, L2, L3, L11.

#### Lecture 2: LLM Agents History & Overview (Shunyu Yao, OpenAI)
Slides: http://llmagents-learning.org/slides/llm_agent_history.pdf (60 slides)

Key findings:
- **ReAct formal definition:** Â = A ∪ L where L = language sequences. Reasoning is a first-class internal action (â_t ∈ L updates context only, not environment)
- **Short-term/long-term memory split (slides 37, 44-45):**
  - Short-term = context window (append-only, limited, does NOT persist)
  - Long-term = external storage (read/write, DOES persist)
  - Controller mediating = "code-based controller"
- **CoALA framework (slide 45):** Memory + Action Space + Decision Making
- **Retrieval scoring from Generative Agents (slides 41-43):** score = recency × importance × relevance
- **Reflexion (slides 38-39):** GPT-4 + Reflexion = 91% HumanEval pass@1 vs 67% zero-shot. "Verbal RL" — text feedback updates long-term memory.
- **ReAct performance (slide 31):** PaLM-540B: ReAct 35.1 HotpotQA / 64.6 FEVER / 71 ALFWorld, beats both reasoning-only and acting-only.

Cross-validation with CC:
- Short-term/long-term = `mutable_messages` vs `TranscriptStore` (never truncated)
- "Code-based controller" = `conversation.rs` runtime
- Retrieval scoring explains CC's 256-token relevance side call (notes/02 gap)
- "Reasoning is internal action" validates extended thinking tokens

#### Lecture 3: Agentic AI Frameworks & AutoGen (Chi Wang + Jerry Liu)
Slides: http://llmagents-learning.org/slides/autogen.pdf (37 slides)

Key findings:
- **6 multi-agent orchestration axes (slide 14):**
  1. Static vs dynamic topology
  2. NL vs PL communication
  3. Context sharing vs isolation
  4. Cooperation vs competition
  5. Centralized vs decentralized
  6. Intervention vs automation
- **Commander/Writer/Safeguard pattern (slides 7-9):** nested chat with safety validation
- **Reflection pattern (slides 21-22):** Writer + Critic with termination condition
- **StateFlow (slide 25):** Agents as state machine with `speaker_selection_method=state_transition`
- **AutoBuild (slides 33-35):** Meta-agent builds agent teams from task description. Captain Agent = 84.25 avg vs 40.98 vanilla LLM.

Cross-validation with CC:
- CC coordinator = dynamic, NL, isolation, cooperation, centralized, automation (6-axis classification)
- Commander/Writer/Safeguard ≈ coordinator + worker + verificationAgent
- `is_termination_msg` pattern = CC's `stop_reason` field on TurnResult
- `summary_method` on chat queues = CC's `agentMemorySnapshot.ts`
- StateFlow = CC's permission system as state transitions (unknown tool → DENY)

#### Lecture 11: Measuring Agent Capabilities & Anthropic RSP (Ben Mann, Anthropic)
Slides: http://llmagents-learning.org/slides/antrsp.pdf (29 slides)

Key findings:
- **ASL system (slides 14-15):** ASL-1 through ASL-4, progressively higher capability + safeguards
- **ASL-3 triggers:** biological weapons, cyberattack, autonomous replication/AI R&D
- **ASL-3 standard (slide 16):** Security Standards (prevent theft) + Deployment Standards (prevent misuse despite hundreds of hours of jailbreaking)
- **Capability measurement:** Task completion time relative to humans. Claude 3.5 Sonnet handles 30-minute human tasks in seconds.

Cross-validation with CC:
- ASL framework = origin story for CC permission tiers (WorkspaceWrite → DangerFullAccess)
- DangerFullAccess gates ASL-3-adjacent capabilities (autonomous agent spawning)
- "Resist hundreds of hours of jailbreaking" = why deny-as-error returns reason to LLM (model must reason about denial, not find workarounds)
- Deployment Standard distinction (security vs misuse prevention) = two CC layers: model weights not exposed (security) + permission system (deployment)

#### Layer coverage:

| Layer | Closest Lecture | Match Quality |
|-------|----------------|---------------|
| Loop (tool use) | L2 (Yao) | **Strong** — ReAct formalization |
| Memory | L2 (Yao, slides 35-45) | **Strong** — short/long-term split, retrieval scoring |
| Context compression | **None** | **No match** — not covered in Fall 2024 |
| Coordinator | L3 (Wang/AutoGen) | **Strong** — 6 orchestration axes, patterns |
| Permissions/Safety | L11 (Mann/Anthropic) | **Strong** — ASL framework, deployment standards |

### Spring 2025: CS294/194-280 Advanced LLM Agents

URL: https://llmagents-learning.org/s25

12 lectures. Key additions beyond F24:
- **L5 (Yu Su):** Memory, Reasoning, Planning — HippoRAG (long-term RAG-based memory, NOT context compression), WebDreamer (world models for web planning), Grokked Transformers
- **L7 (Noam Brown, OpenAI):** Multi-agent game theory
- **L8 (Oriol Vinyals, DeepMind):** Multi-agent coordination & competition
- **L3-4:** Post-training for reasoning, AlphaProof (formal math)
- **L10:** Safety and security
- **L11:** Agent evaluation and benchmarks

Cross-validation with CC:
- HippoRAG (L5) = external long-term memory via retrieval, complements CC's autoDream (which is in-context consolidation). Different mechanisms, same goal: persist knowledge across sessions.
- Game theory (L7) gives formal basis for CC's consequence framing ("you will fail" = altering payoff matrix to make compliance dominant strategy)
- **Context compression: NOT COVERED** — Yu Su's "memory" is RAG-based retrieval, not context window management

### Fall 2025: CS294/194-196 Agentic AI (renamed)

URL: https://agenticai-learning.org/f25

21 lectures (Sep 8 – Dec 8). Significantly expanded from F24's 12 lectures.

New topics NOT in F24:
- **MCP + A2A** — open standards for agent communication (explicitly named in intro)
- **AgentBeats** — live evaluation platform with Green Agent (external benchmarks) + White Agent (build your own benchmark)
- **Agent economics** (Nov 5) — dedicated lecture
- **Multimodal agents** (Oct 22)
- **Embodied agents** (Oct 29)
- **Human-agent interaction** (Nov 17)
- **Post-training for verifiable agents** (Oct 15, RLVR style)

Key lectures for our project:
- Sep 15: Tool Use in Agents
- Oct 1: Memory and Knowledge Management (closest to context mgmt, but title doesn't confirm compression)
- Oct 6-8: Multi-Agent Systems I & II
- Oct 13: Safety and Security
- Sep 24: Agents Stack and Infrastructure (may touch on context)

**Context compression: NOT CONFIRMED in any lecture title.** Oct 1 "Memory and Knowledge Management" is the only candidate but no slide content verified.

### Spring 2026 — DOES NOT EXIST

No Spring 2026 course found. Pattern: F24 (foundational) → S25 (advanced) → F25 (foundational, renamed). If pattern holds, S26 might be advanced round 2, but no announcement found.

### Context Compression Coverage Across ALL Iterations

| Term | Context Compression? | What's covered instead |
|------|---------------------|----------------------|
| Fall 2024 | **No** | — |
| Spring 2025 | **No** | HippoRAG (external retrieval) |
| Fall 2025 | **No** (unconfirmed for Oct 1 lecture) | Memory = knowledge management, not window management |

**Conclusion:** Context compression is a genuine curriculum gap across ALL Berkeley LLM agent courses. Our Unit 3 (context compression) has NO MOOC cross-validation and must rely on CC source code + Anthropic eng blog ("context rot," Tool Result Clearing) as primary sources.

### Fall 2025: Slide Content Actually Read

5 slide decks extracted from rdi.berkeley.edu/agentic-ai/slides/:

#### Oct 20 — Multi-Agent AI (Noam Brown, OpenAI)
- Game-theoretic foundations: minimax vs population best response, self-play convergence
- **Cheap-talk theorem:** In zero-sum minimax equilibrium, language communication is provably useless. Agents must be evaluated by outcomes, not assertions.
- CICERO (Diplomacy): imitation → scale inference → RL. Top 10% in online league.
- Routing-as-multi-agent: routing to best model per query is already multi-agent
- Cross-validation: cheap-talk theorem reinforces why outcome-based contracts are needed for agent markets

#### Nov 10 — Practical Lessons from Deploying AI Agents (Clay Bavor, Sierra)
- **"Agent Iceberg":** visible = LLM+RAG+tools; submerged = ~30 production concerns (prompt injection, compliance, RBAC, regression testing, PII detection, etc.)
- **"Pay for a job well done"** — outcome-based pricing as emerging model
- **τ-bench:** Sierra-developed eval benchmark, adopted by Anthropic and OpenAI. Uses `pass^k` (ALL k trials succeed) not `pass@k`
- Fast brain/slow brain architecture
- Cross-validation with CC: Agent Iceberg ≈ CC's 513K lines of submerged infrastructure; fast/slow brain ≈ trivial→do-directly vs spawn-agent routing

#### Oct 27 — Predictable Noise in LLM Benchmarks (Sida Wang, Meta)
- Benchmark SNR is dangerously low: HumanEval SNR=1.1, HumanEval+ SNR=0.50
- "Models are bigger sources of inconsistency than benchmarks"
- Paired comparison reduces variance vs unpaired
- Cross-validation: statistical unreliability of benchmarks = information asymmetry = credence good verification problem

#### Sep 8 — Introduction (Dawn Song)
- **MCP vs A2A positioning:** MCP = vertical (agent↔tool/environment), A2A = horizontal (agent↔agent task handoff)
- **AgentBeats platform:** uses both MCP and A2A. Green agents (evaluators) communicate with white agents (solvers) via A2A.
- This is the ONLY lecture that directly discusses MCP/A2A

#### Sep 29 — Post-Training Verifiable Agents (Jiantao Jiao, NVIDIA)
- Agentic models = "Environment Feedback Aligned Models" (verifiable rewards)
- Three training requirements: diverse environments, diverse tools, verifiable rewards
- Verifier quality critical: false positives/negatives degrade training
- Cross-validation: verifiable rewards = technical path to making agent quality observable = reducing credence good problem

### Agent-Economy Paper Cross-Validation (Unexpected Finding)

The submitted agent-economy paper argues software quality is a credence good. Four F25 lectures provide interlocking empirical support WITHOUT naming the thesis:

| Lecture | Finding | Credence Good Connection |
|---------|---------|------------------------|
| Bavor (Sierra) | Outcome-based pricing ("pay for a job well done") | = credence good market's natural equilibrium |
| Bavor (Sierra) | 30-item Agent Iceberg of non-verifiable quality | = credence good characteristics catalog |
| Wang (Meta) | Benchmark SNR too low to verify quality differences | = information asymmetry is real and severe |
| Jiao (NVIDIA) | Verifiable reward training | = reducing credence good problem from supply side |
| Brown (OpenAI) | Cheap-talk theorem: language claims untrustworthy | = outcomes, not assertions, needed for evaluation |
| Song (Berkeley) | τ-bench adopted by Anthropic/OpenAI as independent eval | = beginning of third-party credence good certification |

**No lecture directly addresses agent economics as academic topic.** The paper fills a genuine gap.

### Correction: Lecture numbering mismatch

Project notes previously referenced wrong lecture numbers and speakers:
- "L6: Training Agentic Models (Weizhu Chen, Microsoft)" — NOT in any found course
- "L2: System Design (Yangqing Jia, NVIDIA)" — NOT in any found course
These may reference an entirely different course or an early draft syllabus that changed.

---

## Source 4: Anthropic Academy + Engineering Blog — VALIDATED (with correction)

**Correction:** "Anthropic Academy" (Skilljar courses at anthropic.skilljar.com) is too introductory for production cross-validation. The REAL cross-validation sources are the **Anthropic Engineering Blog** posts and **official docs**. Rename this source to "Anthropic Docs & Engineering Blog."

### Official Sources Read (with URLs):

#### "Building Effective Agents" (Dec 2024)
URL: https://www.anthropic.com/research/building-effective-agents
- Named pattern taxonomy: Prompt Chaining, Routing, Parallelization, Orchestrator-Workers, Evaluator-Optimizer, Autonomous Agents
- Workflow vs Agent distinction: workflows = predefined code paths; agents = LLMs dynamically directing tool use
- "Poka-yoke" principle for tool design — error prevention at definition time
- Cross-validation: Evaluator-Optimizer = verification agent; Orchestrator-Workers = coordinator mode

#### "Effective Context Engineering for AI Agents" (Sep 2025)
URL: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- "Context rot" — recall accuracy decreases as token count increases
- Just-in-time tool loading: maintain lightweight identifiers, load dynamically
- Compaction = "distills contents in a high-fidelity manner"; preserve architectural decisions, unresolved bugs
- "Tool Result Clearing" as lightest compaction form
- Structured Note-Taking = agentic memory pattern
- Sub-agents return condensed summaries (1,000-2,000 tokens)
- Cross-validation: validates compaction concept, note-taking ≈ autoDream. **Does NOT confirm 9-section structure.**

#### "Claude Code Auto Mode" (Mar 2026)
URL: https://www.anthropic.com/engineering/claude-code-auto-mode
- **Three-Tier Permission Structure:**
  - Tier 1: Safe tools (reads, navigation) → auto-permitted
  - Tier 2: In-project file edits → auto-allowed
  - Tier 3: Shell, external, out-of-project → classifier
- Two-stage classifier: Stage 1 fast filter (single token), Stage 2 chain-of-thought
- False positive reduction: 8.5% → 0.4%
- Blocked categories: "scope escalation," "credential exploration," "safety-check bypass"
- Cross-validation: **Confirms three-layer enforcement as three-tier permission model**

#### "Claude Code Sandboxing" (Oct 2025)
URL: https://www.anthropic.com/engineering/claude-code-sandboxing
- OS-level: Linux bubblewrap + macOS seatbelt
- Filesystem boundary: read/write only to CWD
- Network boundary: unix domain socket proxy
- Sandboxing reduces permission prompts by 84%
- Cross-validation: **This IS the code-level enforcement layer (Layer 3)**

#### "Advanced Tool Use" (Nov 2025)
URL: https://www.anthropic.com/engineering/advanced-tool-use
- Tool Search Tool: `defer_loading: true` reduces context ~72K → ~500 tokens
- `allowed_callers` field restricts tool access by execution environment
- Programmatic tool calling with `asyncio.gather()` for parallelism
- Cross-validation: validates permission mechanism at tool definition level

#### Sub-agents Documentation
URL: https://code.claude.com/docs/en/sub-agents
- `maxTurns` field confirmed as production mechanism
- `permissionMode`: default/acceptEdits/dontAsk/bypassPermissions/plan
- Built-in subagents: Explore (Haiku), Plan (read-only), general-purpose (all tools)
- "Subagents cannot spawn other subagents" — prevents recursive nesting
- Auto-compaction at ~95% capacity; `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` env var
- Cross-validation: confirms maxTurns, permission modes, compaction threshold

#### Tool Use API Docs
URL: https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works
- Canonical agentic loop with `stop_reason == "tool_use"` check
- `pause_turn` stop reason = server-side iteration limit hit
- Three execution buckets: user-defined, Anthropic-schema, server-executed
- Cross-validation: confirms tool loop structure and stop conditions

### Community Sources (high-confidence corroboration, not primary):
- autoDream reverse engineering (gist): full gate sequence (24h + 5 sessions + lock), microcompact paths
- Claude Code architecture analysis (GitHub): confirms fileStateCache.ts, three-file compaction (compact.ts + autoCompact.ts + microCompact.ts), COORDINATOR_MODE feature flag

### Key gap discovered:
**"9 sections" in compaction output is NOT cross-validated.** Official sources list 5 categories (accomplished, WIP, files, next steps, constraints). The "9 sections" claim comes from our own CC TS source reading only.

### Verdict: VALIDATED as cross-validation source (renamed to "Anthropic Docs & Engineering Blog")

---

## Source 5: Agent SDK — VALIDATED

**Confirmed:** The Agent SDK is literally a control protocol wrapper over the Claude Code CLI binary.

### Architecture (verified from SDK source + docs):
- `pip install claude-agent-sdk` bundles the CC CLI binary inside the package
- On `query()`, spawns CLI as subprocess via `anyio.open_process()`
- All communication: bidirectional JSON-lines over stdin/stdout
- SDK version: 0.1.53 (March 31, 2026); bundled CLI version: 2.1.79
- **The SDK does NOT have its own LLM runtime.** Delegates all model calls to CC CLI → Anthropic API.

### Control Protocol (verified):

| Request Type | Direction | Purpose |
|---|---|---|
| `initialize` | SDK → CLI | Registers hooks and agent definitions |
| `can_use_tool` | CLI → SDK | Permission request before tool execution |
| `hook_callback` | CLI → SDK | Lifecycle hook (PreToolUse, PostToolUse, etc.) |
| `mcp_message` | CLI → SDK | Routes JSONRPC to in-process MCP servers |
| `interrupt` | SDK → CLI | Terminate task |
| `set_permission_mode` | SDK → CLI | Change permission mode mid-session |
| `rewind_files` | SDK → CLI | Restore file state to checkpoint |

### Hook Events (10 Python SDK, 25+ CC shell):
Python: PreToolUse, PostToolUse, PostToolUseFailure, UserPromptSubmit, Stop, SubagentStop, PreCompact, Notification, SubagentStart, PermissionRequest

### Permission Model (5 modes):
default, acceptEdits, plan, bypassPermissions, dontAsk
- Evaluation order: allowed_tools → can_use_tool callback → disallowed_tools → permission_mode
- Fine-grained: `"Bash(npm:*)"` pattern syntax
- Dynamic updates via PermissionUpdate in hook outputs

### Subagent Mechanics:
- Invoked via `Agent` tool (tool_use block)
- Fresh context window (no parent message history)
- Inherits permission context from parent
- Transcripts: `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`
- Cannot spawn further subagents (no nesting)

### Sources:
- https://platform.claude.com/docs/en/agent-sdk/overview
- https://platform.claude.com/docs/en/agent-sdk/agent-loop
- https://platform.claude.com/docs/en/agent-sdk/hooks
- https://github.com/anthropics/claude-agent-sdk-python
- https://pypi.org/project/claude-agent-sdk/

### Verdict: VALIDATED — deep cross-validation with specific architecture details

---

## What This Audit Changes

### Source naming correction:
- "Anthropic Academy" → "Anthropic Docs & Engineering Blog" (Academy is too basic; eng blog is the real source)
- "Agent SDK/CCA" → "Agent SDK" (CCA is not a real thing; SDK is verified independently)

### Note header updates needed:
All notes currently say "Cross-validation: Anthropic Academy, CCA Domain 3, Agent SDK" — update to:
"Cross-validation: CC TS source, claw-code, Anthropic Eng Blog, Agent SDK, Berkeley MOOC (4/5 layers)"

### Specific findings to incorporate into each note:
1. **notes/01 (tool loop):** Add ReAct formal definition (Â = A ∪ L) from MOOC L2. Add `pause_turn` stop reason from API docs.
2. **notes/02 (memory):** Add retrieval scoring (recency × importance × relevance) from MOOC L2. Add autoDream gate sequence (24h + 5 sessions) from community reverse engineering. Add "Structured Note-Taking" as official Anthropic term.
3. **notes/03 (context):** Mark "9-section compaction" as CC TS source ONLY — not officially cross-validated. Add "context rot" terminology from Anthropic eng blog. Add Tool Result Clearing as lightest compaction form.
4. **notes/04 (coordinator):** Add 6 orchestration axes from MOOC L3. Add Orchestrator-Workers as official Anthropic pattern name. Classify CC: dynamic, NL, isolation, cooperation, centralized, automation.
5. **notes/05 (prompt engineering):** Add three-tier auto mode permission structure from eng blog. Add poka-yoke principle for tool design.
6. **notes/06 (reliability triad):** Add ASL framework as origin story for permission tiers from MOOC L11.
7. **notes/07 (integration):** Update source count to reflect audit results.

### Corrections to propagate:
- "9-section compaction" — only our CC TS reading supports this. Official docs say 5 categories. Flag as "internal implementation detail, not officially documented."
- "Three-layer enforcement" — our naming. Anthropic calls it "three-tier permission." The concept is confirmed; the name is ours.
- "autoDream" — internal name from minified JS bundle. Official term: "memory consolidation" or "structured note-taking."

### MOOC 2025/2026 — PENDING
S25 and F25 slide decks partially audited (see § Source 5 above). Full lecture-by-lecture audit not yet completed.
