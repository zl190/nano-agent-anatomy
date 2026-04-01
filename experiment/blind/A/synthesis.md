# Synthesis v1: Claude Code Source Reading (513K LOC TypeScript)

6 reader reports, ~35K words of analysis. This synthesis extracts the cross-cutting patterns, architectural summary, and surprising findings.

---

## 1. Cross-Cutting Patterns

Patterns that appear in 2+ reader reports, ordered by how many reports surface them.

### 1.1 Layered Permission Model (R1, R2, R3, R4, R5)

Every tool call passes through a multi-layer permission cascade before execution:

```
Tool-level checkPermissions() → Permission rules (session/project/user)
  → Agent-level allowedTools override → Async flag (auto-deny if no UI)
    → YOLO classifier (AI decides safety) → Interactive prompt → Mode default
```

The permission result is a **three-way enum** (`allow | ask | passthrough`), not a boolean. `passthrough` means "this layer has no opinion; try the next." This enables composable permission chains where no layer needs knowledge of the others. The `claim()` atomic check-and-mark pattern resolves races when 4+ concurrent sources (local UI, CCR bridge, Telegram channel, hooks+classifier) compete to answer a single permission request.

**Why it matters:** Tutorials teach `if (allowed) execute()`. Production requires a chain-of-responsibility where each layer can short-circuit, defer, or abstain — and where the first responder among multiple concurrent sources wins atomically.

### 1.2 Fail-Closed Defaults + Security at Every Boundary (R1, R2, R3, R5, R6)

`buildTool` defaults: `isConcurrencySafe: false`, `isReadOnly: false`. Every tool that touches the filesystem guards against:

- **UNC paths** — `\\server\share` triggers SMB auth, leaking NTLM credentials. All filesystem tools short-circuit before any I/O.
- **Symlink traversal** — Team memory paths use two-pass validation: `path.resolve()` (fast, string-only) then `realpathDeepestExisting()` (resolves symlinks). `realpath` alone misses dangling symlinks; `lstat` distinguishes.
- **Bare-repo attacks** — BashTool/PowerShellTool detect writes to git-internal paths (HEAD, objects/, refs/, hooks/) including via NTFS 8.3 short names (`git~1`).
- **POSIX `--` delimiter** — Path extractors are aware of end-of-options, so `rm -- -/../secret` doesn't bypass validation.
- **MCP skill trust boundary** — MCP skills cannot execute inline shell commands. `loadedFrom !== 'mcp'` is the gate.

Bundled skill file extraction uses `O_NOFOLLOW|O_CREAT|O_EXCL` flags, `0o600` mode, and a per-process nonce directory to prevent pre-created symlink attacks.

### 1.3 Memoize-Expensive, Re-evaluate-Cheap (R1, R2, R3, R6)

A consistent two-tier caching pattern throughout:

| Expensive (memoized) | Cheap (re-evaluated every call) |
|---|---|
| `loadAllCommands(cwd)` | `meetsAvailabilityRequirement(cmd)`, `isEnabled()` |
| `connectToServer(name, config)` | Connection health checks |
| `getAutoMemPath()` (by project root) | Memory file relevance selection |
| Zod schemas via `lazySchema()` | Tool availability based on auth state |
| Skill content at load time (name+description only) | Full content loaded on invocation |
| Prompt cache TTL (latched at session start) | Never re-evaluated mid-session |

The principle: I/O-bound or parse-heavy work is memoized. Runtime-state-dependent checks (auth, feature flags, capability) run fresh because they can change mid-session. Memoization caches are explicitly clearable (e.g., MCP connection drops clear the memo cache, next call reconnects fresh).

### 1.4 Discriminated Unions as Architectural Contracts (R1, R2, R3, R5, R6)

Used pervasively for type-safe dispatch:

- **Tool output**: `text | image | notebook | pdf | parts | file_unchanged` (FileReadTool)
- **Connection state**: `connected | failed | needs-auth | pending | disabled` (MCP)
- **Task state**: `LocalShell | LocalAgent | RemoteAgent | InProcessTeammate | LocalWorkflow | MonitorMcp | Dream`
- **Command type**: `LocalJSXCommand | LocalCommand | PromptCommand`
- **Selector return**: `{ type: 'leader' } | { type: 'viewed', task } | { type: 'named_agent', task }`
- **File write output**: `create | update`

Every discriminated union forces callers to handle all cases. No stringly-typed dispatch.

### 1.5 Two State Systems (R1, R4, R5)

| System | File | Purpose | Immutability |
|---|---|---|---|
| Process-global singleton | `bootstrap/state.ts` (~60 fields) | Session ID, cost counters, telemetry, model overrides, prompt cache latches | Module-level, no React, DAG leaf |
| React-bound UI state | `state/AppStateStore.ts` (~60 fields) | Tools, permissions, tasks, MCP, plugins, settings, bridge, speculation | `DeepImmutable<>` (except tasks/agentNameRegistry which contain functions) |

The reactive substrate is a **34-line hand-rolled store** (`createStore`): `getState`, `setState(updater)`, `subscribe(listener)`. No Redux, Zustand, or Jotai. `Object.is` reference equality skips no-op updates. All side effects flow through one `onChangeAppState` diff-watcher — before this pattern, 8+ mutation sites forgot to notify CCR of permission mode changes.

`AsyncLocalStorage` provides per-agent context isolation when multiple backgrounded agents share the same process (R5).

### 1.6 Prompt Cache as Active Engineering Concern (R1, R3)

Prompt cache is not a side effect — it's an actively managed budget:

- **TTL latched at session start** — `promptCache1hEligible` evaluates once and freezes for the session. A mid-session flip would bust the server-side cache.
- **MCP tools downgrade scope** — MCP tools are per-user (dynamic tool section), so `global` cache scope downgrades to `ephemeral` when MCP is present.
- **Tool schema order is deterministic** — Non-deterministic ordering would bust the cache prefix.
- **Fork children share byte-identical prefixes** — `buildForkedMessages()` replaces all tool_result blocks with an identical placeholder. Only the per-child directive text block differs.
- **`omitClaudeMd` for read-only agents** — Explore/Plan agents skip CLAUDE.md and git status, saving ~5-15 Gtok/week.

### 1.7 Fire-and-Forget with Guaranteed Cleanup (R1, R2, R5)

Async operations that must not block the critical path:

| Operation | Where |
|---|---|
| Transcript write (bare mode) | `void transcriptPromise` in `submitMessage` |
| Paste store write | `storePastedText` — hash-referenced, fire-and-forget |
| Skill discovery on file read/write | `addSkillDirectories(newSkillDirs).catch(() => {})` |
| Memory prefetch | `pendingMemoryPrefetch` with `using` disposal pattern |
| Plugin installation progress | Background work streams status into AppState |

All fire-and-forget operations register with `registerCleanup()` (a 25-line global cleanup registry) so they complete before process exit. `Promise.all` runs all cleanups concurrently.

### 1.8 Skills Are Agents (R3, R6)

`SkillTool.executeForkedSkill()` calls `runAgent()` directly. A skill is an agent whose definition comes from a markdown file with frontmatter, loaded via `getCommands()` rather than `loadAgentsDir()`. The differences:

| | Skills | Agents |
|---|---|---|
| Discovery | Slash commands, auto-invocation via `whenToUse` | Agent tool, `subagent_type` parameter |
| Lifecycle | Sync in-session (usually) | Sync or async/background |
| Definition | Markdown frontmatter | Markdown frontmatter (same parser) |
| Source | File, bundled, MCP, plugin | File, bundled |
| Trust | MCP skills restricted (no shell exec) | All agents trusted equally |

MCP servers can dynamically inject skills into the skill list. Bundled skills (always-on, invisible) are distinct from builtin plugins (user-toggleable in `/plugin` UI).

### 1.9 Async Generator as the Tool Loop Contract (R1, R3)

`query()` and `submitMessage()` are async generators. Callers iterate via `for await`. This makes backpressure, early exit, and error propagation natural — no callback hell, no event emitter. The `StreamingToolExecutor` yields tool executions as they stream from the API.

The query loop applies **five successive message-array transformations** before every API call: tool-result budget → snip → microcompact → context collapse → autocompact. Each returns a new array; the original is never mutated (it's the source of truth for transcript and UI).

### 1.10 Model-Facing vs Human-Facing Divergence (R4, R6)

"What the user sees" and "what the model processes" are intentionally different:

- The REPL keeps snipped messages for scrollback. The compact command strips them before summarization.
- `/context` mirrors the exact pre-API transforms so the token count the user sees matches what the model receives.
- `backfillObservableInput` mutates tool input in-place (idempotent) before any observer sees it, adding derived fields without busting the prompt cache on the original API-bound input.
- `_simulatedSedEdit` is stripped from the model-facing schema — "exposing it would let the model bypass permission checks."

---

## 2. Architecture Summary

### The Runtime Core

Claude Code is a **single-process terminal application** built on three pillars: a custom React renderer for terminals (Ink, ~13K LOC), a React component tree (24K+ LOC), and a CLI/remote integration layer (~7K LOC). The main loop is an async generator (`queryLoop`) that runs inside a `while (true)` with typed `Continue` and `Terminal` transitions. Each iteration: preprocess messages through a 5-stage pipeline of pure functions, call the Anthropic API via streaming, execute tool calls via `StreamingToolExecutor`, handle interrupts, and manage `maxOutputTokens` recovery. The tool loop is not a simple request-response cycle — it's a stateful generator that yields events, supports backpressure, and can be cleanly interrupted at any point via abort controllers.

### State and Reactivity

State is split into two systems that never reference each other. The process-global singleton (`bootstrap/state.ts`) is a DAG leaf — it imports nothing from `src/utils/` to prevent circular dependencies — and holds session identity, cost counters, telemetry handles, and prompt cache latches. The React-bound state (`AppStateStore`) is a 34-line hand-rolled pub/sub store with `DeepImmutable` typing on most fields. Side effects are centralized in a single `onChangeAppState` diff-watcher that fires after every `setState`, replacing the prior pattern of scattering persistence/notification calls across 8+ mutation sites. When multiple agents run concurrently in the same process (via Ctrl+B backgrounding), `AsyncLocalStorage` provides implicit context propagation per async execution chain, preventing agent A's events from using agent B's context.

### The Tool System

Every tool is a plain object satisfying a ~15-method interface: `validateInput`, `checkPermissions`, `call`, rendering hooks for 5 display states (normal, condensed, progress, rejected, error), API mapping, concurrency safety declaration, and permission matcher. The `buildTool` factory applies fail-closed defaults. Tools know how to render themselves — there is no separate renderer layer. Large outputs are automatically offloaded to disk via a `maxResultSizeChars` field. Deferred tools (`shouldDefer` / `alwaysLoad` pair) are hidden from the initial prompt and fetched on demand via `ToolSearch`, keeping the initial tool list token-efficient. The BashTool alone is 12,400 lines, with its security subsystems (permission engine, AST-based compound command decomposition, read-only validation, path extraction with POSIX `--` awareness) dwarfing the execution logic. Command-specific exit code semantics (grep exit 1 = "no matches", not error) are a first-class layer.

### Agent Hierarchy and MCP

Agents spawn through four paths: multi-agent swarm (tmux), fork (clone parent context with cache-optimized identical prefixes), normal sync/async (via `runAgent()`), and remote (CCR teleport). Background agents get a restricted tool allowlist, auto-deny permission prompts (except `bubble` mode which forwards to parent), and an unlinked AbortController. Skills are agents in disguise — `SkillTool` calls `runAgent()` directly. MCP connections use a discriminated union for state (`connected | failed | needs-auth | pending | disabled`), memoized connections with clear-on-close for auto-reconnect, and a 27.8-hour tool call timeout. The bridge operates as either a daemon (CCR `runBridgeLoop`) or an in-process bridge (REPL `replBridge`), sharing core logic. `WorkSecret` (base64url-encoded JSON blob) injects per-session config into ephemeral child processes without environment variable pollution.

### Persistence and Memory

The memory system (~1,736 lines) implements a 4-type taxonomy (user/feedback/project/reference) with eval-validated prompt instructions — section headers are chosen based on A/B test success rates ("Before recommending from memory" → 3/3; "Trusting what you recall" → 0/3, same body text). Memory selection is a per-turn side-query: a 256-token Sonnet call selects 5 relevant files from a manifest, filtered by `alreadySurfaced` to prevent re-injection. Human-readable relative ages ("47 days ago") trigger staleness reasoning more reliably than ISO timestamps. The harness creates the memory directory, then tells the model it already exists — a prompt-engineering fix that saves one `ls` turn per session. Team memory writes use two-pass symlink validation with referenced security reviews (PSR M22186, M22187).

---

## 3. Most Surprising Findings

### 3.1 The security subsystems dwarf the tools they protect

BashTool's security (bashPermissions.ts 2,621 lines + bashSecurity.ts 2,592 lines + readOnlyValidation.ts 1,990 lines + pathValidation.ts 1,303 lines) totals ~8,500 lines. The actual execution logic is ~1,100 lines. PowerShellTool is similar: 8,800 total, with ~4,700 in security. The ratio is roughly **4:1 security-to-execution**. This is not visible in any tutorial or architectural overview.

### 3.2 Prompt cache stability is an obsession, not an optimization

Cache TTL is latched at session start and never re-evaluated. Fork children have byte-identical prefixes by design. MCP tool presence downgrades cache scope. Tool schema building order is deterministic. The `promptCache1hEligible` flag is sticky — once evaluated, it never re-evaluates, because "a mid-session flip in plan eligibility would bust the server-side prompt cache at exactly the wrong moment." This is treated as a correctness concern, not a performance optimization.

### 3.3 Memory instructions are A/B tested against evals

The prompt text in `memoryTypes.ts` has inline comments citing success rates. "Before recommending from memory" (action cue at decision point) went 3/3. "Trusting what you recall" (abstract) went 0/3 — same body text, different header. The "what NOT to save" section was validated to override even explicit user requests. Position in the prompt matters: content "buried as a bullet under 'When to access'" dropped to 0/3.

### 3.4 `sed -i` is intercepted and simulated, not executed

When BashTool recognizes a `sed -i` pattern, it parses the edit, shows the user a diff preview, and applies the verified diff directly without spawning a shell process. The `_simulatedSedEdit` field is deliberately stripped from the model-facing schema — the comment: "exposing it would let the model bypass permission checks." The model thinks it's running sed. It isn't.

### 3.5 The terminal renderer is a game engine in disguise

Ink implements double buffering with Uint32Array cell comparison, bit-packed style pools (visibility encoded in bit 0 for branchless skip of invisible spaces), hardware scroll via DECSTBM escape sequences (90% output reduction on pure-scroll frames), dirty-flag cascading (mark upward in O(depth) to prevent one dirty node from forcing 2,800 message re-renders), Yoga WASM node pooling with 5-minute GC cycles, and adaptive scroll drain (proportional for native terminals, constant velocity for xterm.js). The React reconciler is 512 lines — layout, scheduling, and batching come from upstream React.

### 3.6 WebFetch uses a two-model pipeline

WebFetch doesn't return raw content to the main model. It runs a Haiku query over the fetched content with the user-supplied prompt, then returns Haiku's summary. The main model never sees the raw HTML or Markdown. WebSearch is even more surprising — it's a server-side capability, not HTTP. The client triggers `web_search_20250305` as an API tool; the server executes the search and returns results in the streaming response.

### 3.7 The 34-line store is the entire reactive substrate

No Redux, no Zustand, no Jotai. `createStore<T>(initialState, onChange?)` with three methods: `getState`, `setState(updater)`, `subscribe(listener)`. `Object.is` for no-op detection. `onChange` fires the single diff-watcher that owns all side effects. React hooks use `useSyncExternalStore` against the store's `subscribe`. The entire state management philosophy fits on a whiteboard.

### 3.8 `useLayoutEffect` vs `useEffect` for raw mode is a subtle production bug

`useInput` enables terminal raw mode via `useLayoutEffect` (synchronous, during React's commit phase). Using `useEffect` would defer to the next event loop tick — leaving the terminal in cooked mode briefly, causing keystrokes to echo to screen before the handler activates. This is a timing bug that no tutorial mentions and that would be extremely difficult to diagnose in production.

### 3.9 The `/batch` skill enforces a machine-readable output contract

Background workers spawned by `/batch` must emit `PR: <url>` as their final output. The coordinator parses this as structured data to populate a progress table. Background agent output is treated as a protocol, not prose. Each worker's prompt includes verbatim worker instructions (simplify → tests → e2e → commit+push → PR → report) that cannot be deviated from.

### 3.10 Read deduplication saves 2.64% of fleet cache_creation tokens

FileReadTool tracks `(path, offset, limit, mtime)` and returns a ~100-byte `file_unchanged` stub when the model re-reads the same file at the same offset with unchanged mtime. The comment documents: "~18% of Read calls are same-file collisions." The dedup only applies when `offset !== undefined` — a subtle invariant distinguishing post-Read entries from post-Edit/Write entries (which set mtime but leave offset undefined).

---

## 4. Pattern Density Map

Where patterns concentrate, ranked by cross-report frequency:

| Pattern | R1 | R2 | R3 | R4 | R5 | R6 | Count |
|---|---|---|---|---|---|---|---|
| Permission cascade (3-way enum) | x | x | x | x | x | | 5 |
| Security at boundaries | | x | x | | x | x | 4 |
| Memoize-expensive / re-evaluate-cheap | x | x | x | | | x | 4 |
| Discriminated unions | x | x | x | | x | x | 5 |
| Fire-and-forget + cleanup | x | x | | | x | | 3 |
| Two state systems | x | | | x | x | | 3 |
| Fail-closed defaults | x | x | | | | | 2 |
| Prompt cache engineering | x | | x | | | | 2 |
| Skills = agents | | | x | | | x | 2 |
| Async generator protocol | x | | x | | | | 2 |
| Feature-flag dead code elimination | x | | | | | x | 2 |
| Model vs human context divergence | | | | x | | x | 2 |
| Singleton with subscriber counting | | | | x | x | | 2 |
| Read-before-write enforcement | | x | | | x | | 2 |
| Side-query for context selection | | | | | x | x | 2 |

---

## 5. What Tutorials Will Never Teach

1. **The security/execution ratio is 4:1.** The interesting part of a shell tool isn't executing commands — it's deciding whether to execute them.

2. **Prompt cache is a correctness concern.** A mid-session cache bust doesn't just cost money — it changes model behavior because the cached prefix's attention patterns differ from a fresh computation.

3. **Exit codes are command-specific vocabulary.** `grep` exit 1 means "no matches found." `diff` exit 1 means "files differ." `find` exit 1 means "partial success." A universal nonzero-is-error handler is wrong.

4. **Deferred tool loading is the tool-count scaling strategy.** You can't put 70+ tools in the initial prompt. `shouldDefer` / `alwaysLoad` + `ToolSearch` keeps the initial prompt lean while making all tools discoverable.

5. **Memory selection is itself an LLM call.** A 256-token Sonnet call per turn to select 5 relevant memory files is cheaper than injecting all memory and hoping the model ignores the irrelevant parts.

6. **The `onChangeAppState` pattern replaces 8+ scattered notification sites.** One diff-watcher that owns all persistence/sync side effects. Any future `setState` call automatically gets CCR notification, settings persistence, and env var re-application for free.

7. **Background agents have a fundamentally different permission model.** They can't show UI prompts. They get a restricted tool allowlist. They auto-deny anything requiring approval — unless `bubble` mode explicitly forwards to the parent.

8. **Read-before-write is enforced, not advisory.** The `readFileState` map gates every edit and write. The model cannot overwrite a file it hasn't read, and it cannot overwrite a file that was modified externally since the last read.

9. **The store is 34 lines because it doesn't need to be more.** The entire React ecosystem's state management discourse collapses when you have a typed updater function, reference equality bail-out, and a subscriber list.

10. **`useLayoutEffect` matters for I/O.** Raw mode, cursor positioning, and any synchronous TTY interaction needs commit-phase timing. `useEffect`'s next-tick deferral creates invisible race conditions.
