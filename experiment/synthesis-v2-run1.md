# Synthesis: Claude Code Architecture (v2 SOP, Run 1)

**Date:** 2026-04-01
**Model:** Opus
**Input:** 6 Reader outputs (200 symbols, 45 patterns, 58 surprises)
**Tokens:** 22,868 | **Duration:** 204s

---

## 11 Cross-Cutting Patterns

| # | Pattern | Spans Readers | Significance |
|---|---------|--------------|--------------|
| 1 | **Feature-Flag DCE via bun:bundle** | 1,3,4,6 | High |
| 2 | **Fail-Closed Security with Layered Permission** | 1,2,4,5 | High |
| 3 | **Memoization as First-Class Architecture** | 1,3,4,5,6 | High |
| 4 | **Dual-State: Process-Global vs React-Reactive** | 1,4,5 | High |
| 5 | **Streaming-First Async Generator Pipeline** | 1,3,4 | High |
| 6 | **ToolUseContext as Ambient DI** | 1,2,3,5 | High |
| 7 | **Subagent Architecture with Cache-Hit Inheritance** | 1,3,5,6 | High |
| 8 | **Prompt Cache Preservation as System-Wide Invariant** | 1,3,4 | High |
| 9 | **Multi-Source Aggregation with Priority Cascade** | 5,6 | Medium |
| 10 | **Model-Calling-Model Recursion** | 2,3,5 | High |
| 11 | **Read-Before-Write as Universal Safety** | 2,5,6 | Medium |

### Pattern Details

**1. Feature-Flag DCE via bun:bundle** (Readers 1,3,4,6)
feature() evaluated at bundle time, not runtime. False branches physically stripped. ~94 uses across 20+ files. Internal features (BASH_CLASSIFIER, voice, Chrome MCP, internal commands) never ship to external binary.

**2. Fail-Closed Security with Layered Permission** (Readers 1,2,4,5)
buildTool → fail-closed defaults → multi-stage shell normalization → per-tool permission UI → 7 permission modes with AI classifier + circuit breaker. No single bypass compromises the system.

**3. Memoization as First-Class Architecture** (Readers 1,3,4,5,6)
Every layer memoizes for different reasons: command registry (side-effect-free imports), MCP connections (cache-invalidation reconnect), UI (module-level LRU > useMemo because fiber eviction), settings (centralized reset after N×reset profiling), plugins (cache-only startup).

**4. Dual-State** (Readers 1,4,5)
Process-global bootstrap/state (set once) vs React-reactive AppState (pub-sub store). Deliberately decoupled. Subagent isolation via no-op setAppState paths.

**5. Streaming-First Pipeline** (Readers 1,3,4)
query→queryLoop→callModel async generator chain. Always stream:true. Non-streaming fallback on 529. Double-buffered terminal rendering. Heartbeat messages during retry.

**6. ToolUseContext as Ambient DI** (Readers 1,2,3,5)
Single context bag carries all deps. Dual setAppState (real vs no-op for subagents). Flows through shell security, file TOCTOU prevention, MCP execution, memory extraction.

**7. Subagent Architecture with Cache-Hit Inheritance** (Readers 1,3,5,6)
FORK_SUBAGENT inherits parent's rendered system prompt for cache hit. Used by compact, auto-dream, memory recall, skill execution, tool search.

**8. Prompt Cache Preservation** (Readers 1,3,4)
50-70K tokens at stake. Never mutate API-bound messages. Sticky header latches. Even LogoHeader memo'd to prevent blit contamination.

**9. Multi-Source Aggregation** (Readers 5,6)
Settings: 5 layers. Commands: 5 sources. Both with deterministic priority. systemd-style drop-in directories.

**10. Model-Calling-Model Recursion** (Readers 2,3,5)
WebSearch → recursive Claude API call. BASH_CLASSIFIER → LLM as permission arbiter. Memory recall → Sonnet side-query.

**11. Read-Before-Write Safety** (Readers 2,5,6)
readFileState Map (TOCTOU). Memory path validation (anti-traversal). Bundled skill O_CREAT|O_EXCL|O_NOFOLLOW (anti-symlink).

---

## Architecture Summary

Claude Code is a 513K-line TypeScript terminal AI coding agent compiled with Bun.

**Core:** Streaming async generator pipeline (query → queryLoop → callModel). Dual state planes: process-global (session identity, costs, feature flags) vs React-reactive AppState (tasks, permissions, MCP).

**Tools:** buildTool factory with fail-closed defaults. ToolUseContext as universal dependency carrier. Shell security: multi-stage normalization, tree-sitter shadow mode, compound-command decomposition. File tools: read-before-write TOCTOU prevention.

**API:** Single factory → 4 cloud providers. Streaming-first with 529 fallback. Prompt cache preservation as architectural invariant (never mutate messages, latch headers, fork subagents with byte-identical prefix).

**UI:** Custom React reconciler → Yoga layout → double-buffered Screen → cell-level diff → ANSI output. React Compiler (Forget) applied globally. Module-level LRU caches, OffscreenFreeze, RawAnsi bypass.

**Extensibility:** 5-source command aggregation, dynamic skill discovery on file touch, path-gated skill activation, MCP skills from server prompts.

**Security:** Layered + asymmetric. 7 permission modes with AI classifier auto-approval and circuit breaker. Adversarial filesystem assumptions everywhere.

---

## Top 10 Surprises

1. **WebSearchTool = recursive API call** — delegates to Claude itself, not external search API
2. **BASH_CLASSIFIER = LLM evaluating LLM** — model calling model for security decisions, with hard-fail circuit breaker
3. **Tree-Sitter in shadow mode only** — parses but doesn't enforce, legacy regex still authoritative
4. **OffscreenFreeze exploits React reconciler internals** — element reference identity as bailout, opts out of React Compiler
5. **Memory path override blocked from projectSettings** — prevents malicious repo redirecting writes to ~/.ssh
6. **Prompt cache shapes EVERYTHING** — message immutability, header latching, subagent forking, UI memo order
7. **Commands grow mid-session** — file touches discover new skills, capability set evolves monotonically
8. **Bun-specific workarounds** — AbortSignal.timeout memory leak → use setTimeout
9. **sed -i fully intercepted** — rerouted through file-diff, _simulatedSedEdit hidden from model schema
10. **Chrome/ComputerUse MCP in-process** — saves 325MB per connection

---

## Metrics

| Metric | Value |
|--------|-------|
| Readers | 6 × Sonnet |
| Synthesizer | 1 × Opus |
| Total tokens (readers) | 540K |
| Synthesizer tokens | 23K |
| Total cost estimate | ~$4.00 |
| Wall clock (parallel readers + serial synth) | ~9.5 min |
| Cross-cutting patterns found | 11 (9 high, 2 medium) |
| Top surprises | 10 |
