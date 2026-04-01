# Reader 1: Core Runtime

## Source Reading Report: Tool.ts, QueryEngine.ts, query.ts, commands.ts, history.ts, setup.ts, bootstrap/state.ts, bridge/, remote/, tasks/, state/

---

### src/Tool.ts — 792 lines

**Core types/functions:**
- `ToolUseContext` — the god-object passed to every tool call. Carries abort controller, app state getters/setters, permission context, message log, file state cache, and a dozen optional UI callbacks. Single object unifies execution context across all tool invocations.
- `Tool<Input, Output, P>` — the complete tool interface. 30+ methods including `call`, `checkPermissions`, `validateInput`, `renderToolResultMessage`, `renderToolUseProgressMessage`, `renderGroupedToolUse`, `mapToolResultToToolResultBlockParam`, `toAutoClassifierInput`, and `backfillObservableInput`.
- `buildTool(def)` — factory that merges safe defaults (fail-closed: `isConcurrencySafe → false`, `isReadOnly → false`) with a partial tool definition.
- `ToolResult<T>` — wraps tool output with optional new messages and a `contextModifier` function for non-concurrency-safe tools that mutate context.

**Production insight:** The `Tool` interface is both the runtime contract AND the rendering contract. Every tool knows how to render itself in normal, condensed, progress, rejected, and error states. There is no separate renderer layer — the tool IS the renderer. The `maxResultSizeChars` field with `Infinity` sentinel for tools like Read is how large outputs are automatically offloaded to disk and replaced with a path reference. The `backfillObservableInput` hook (mutate-in-place, idempotent, called before any observer sees the input) solves the hard problem of adding derived fields without busting the prompt cache on the original API-bound input. The `shouldDefer` / `alwaysLoad` pair implements the ToolSearch deferred loading pattern — expensive tools are hidden from the initial prompt and only fetched on demand.

**Mapping:** Our `tool_loop.py` should use a similar interface object rather than loose functions. The `ToolResult.contextModifier` pattern (return a function that transforms context) is cleaner than mutating a shared dict. The `buildTool` factory with fail-closed defaults is directly adoptable.

---

### src/bootstrap/state.ts — 1758 lines

**Core types/functions:**
- `State` (private type, ~60 fields) — the single process-global mutable singleton. Covers session ID, cost counters, telemetry handles, model overrides, flag caches, prompt cache latches, and behavioral flags.
- `getInitialState()` — builds the singleton at module load time; calls `realpathSync(cwd())` and normalizes to NFC.
- `switchSession(sessionId, projectDir?)` — atomically switches session ID and project directory together; emits a `sessionSwitched` signal.
- Dozens of get/set accessor pairs: `getSessionId`, `addToTotalCostState`, `addToToolDuration`, `markScrollActivity` / `getIsScrollDraining`, `waitForScrollIdle`, `snapshotOutputTokensForTurn`, etc.
- `markPostCompaction` / `consumePostCompaction` — one-shot latch consumed by the next API success event.

**Production insight:** The comment "DO NOT ADD MORE STATE HERE — BE JUDICIOUS WITH GLOBAL STATE" appears three times. This is enforced discipline, not a wish. The file is explicitly a DAG leaf (nothing from `src/utils/` is imported) to avoid circular deps. Scroll-drain detection (`markScrollActivity`, `getIsScrollDraining`, `waitForScrollIdle`) prevents background intervals from competing with Ink render frames for the event loop — a subtle performance concern tutorials never mention. The `promptCache1hEligible` latch is sticky: once evaluated, it never re-evaluates mid-session, because a mid-session flip in plan eligibility would bust the server-side prompt cache at exactly the wrong moment.

**Mapping:** Our `bootstrap/state.py` should be a process-global singleton with explicit accessor functions. The one-latch pattern for expensive/cache-sensitive flags (evaluate once, freeze for session lifetime) is directly adoptable for API key caching and model selection.

---

### src/QueryEngine.ts — 1295 lines

**Core class/functions:**
- `QueryEngine` class — owns one conversation's state: `mutableMessages`, `abortController`, `permissionDenials`, `totalUsage`, `readFileState`, `discoveredSkillNames`, `loadedNestedMemoryPaths`.
- `submitMessage(prompt, options?)` — async generator. Per-turn lifecycle: build system prompt, process slash commands, persist transcript, run query loop via `query()`, translate raw messages to SDK wire format, yield `SDKMessage` events including final `result` or `error_max_turns`.
- `wrappedCanUseTool` — internal wrapper around the caller's `canUseTool` that records permission denials for SDK reporting.

**Production insight:** `submitMessage` rebuilds `processUserInputContext` twice per turn: once before slash-command processing (where `setMessages` is live) and once after (where `setMessages` is a no-op). This is intentional: slash commands like `/force-snip` mutate the message array during processing, so the second context snapshot freezes the post-mutation state for the query loop. The user message is written to transcript BEFORE the API call — not after — so interrupted sessions remain resumable even if the process is killed before any response arrives. In bare/scripted mode, this write is fire-and-forget (`void transcriptPromise`) to avoid the ~4ms disk I/O on the critical path. The `discoveredSkillNames` set is cleared at the start of each `submitMessage` (not each session) to prevent unbounded growth across many SDK turns.

**Mapping:** Our `QueryEngine` equivalent should be a class (not a function) so state persists across turns. The pre-turn transcript write pattern (write user message immediately, even if AI never responds) should be adopted for any agent that supports resume.

---

### src/query.ts — 1729 lines

**Core functions:**
- `query(params)` — thin wrapper: delegates to `queryLoop`, then notifies command lifecycle for all consumed slash commands on clean exit.
- `queryLoop(params, consumedCommandUuids)` — the main `while (true)` tool loop. Per-iteration: apply tool-result budget, run snip compaction, run microcompact, run context collapse, run autocompact, call the API via `deps.claude()`, stream tool executions via `StreamingToolExecutor` / `runTools`, handle stop hooks, manage `maxOutputTokens` recovery, detect and handle interrupt.
- `State` (loop-local type) — `messages`, `toolUseContext`, `autoCompactTracking`, `maxOutputTokensRecoveryCount`, `hasAttemptedReactiveCompact`, `turnCount`, `transition`.
- `yieldMissingToolResultBlocks` — synthesizes `tool_result` error messages for any tool_use blocks left pending when the model is interrupted.

**Production insight:** The loop applies five successive message-array transformations before every API call: tool-result budget, snip, microcompact, context collapse, autocompact. Each returns a new `messagesForQuery` array; the original `messages` is never mutated (it's the source of truth for transcript and UI). The `pendingMemoryPrefetch` uses the `using` disposal pattern (TS 5.2 explicit resource management) to guarantee cleanup on all generator exit paths including throw and `.return()`. Skill discovery prefetch is fired per-iteration and awaited post-tools to hide latency under model streaming. The `taskBudgetRemaining` variable is loop-local (not on `State`) expressly to avoid touching the 7 continue sites in the loop — a precision scoping decision to minimize the risk of forget-to-update bugs.

**Mapping:** Our `tool_loop.py` should apply message preprocessing before each API call as a pipeline of pure functions (not mutations). The `continue` pattern (replace `state = {...}` at loop bottom) is cleaner than scattered mutations. The `while (true)` with explicit `Terminal` return type and `Continue` transition type is directly adoptable for making loop exits typed and auditable.

---

### src/commands.ts — 754 lines

**Core functions:**
- `COMMANDS()` — memoized factory returning ~70 built-in commands. Evaluated lazily (not at module load) because some commands read config.
- `getCommands(cwd)` — main entry point: loads from `loadAllCommands(cwd)` (memoized by cwd), merges dynamic skills, filters by availability and `isEnabled()`. Availability and enable checks are NOT memoized — auth can change mid-session.
- `loadAllCommands(cwd)` — parallel loads: skill dir commands, plugin skills, bundled skills, builtin plugin skills, plugin commands, workflow commands. Returns all merged.
- `getSkillToolCommands(cwd)` / `getSlashCommandToolSkills(cwd)` — memoized filters over `getCommands()` for model-invocable skills vs. slash-only skills.
- `meetsAvailabilityRequirement(cmd)` — checks `claude-ai` vs `console` subscription gates.
- `BRIDGE_SAFE_COMMANDS`, `REMOTE_SAFE_COMMANDS` — explicit allowlists for commands safe to execute over the remote bridge or in remote mode.
- `isBridgeSafeCommand(cmd)` — `prompt`-type commands are always safe (they expand to text); `local-jsx` always blocked; `local` requires opt-in via `BRIDGE_SAFE_COMMANDS`.

**Production insight:** The `clearCommandMemoizationCaches()` function must also clear `getSkillIndex` in `skillSearch/localSearch.ts` because it's an outer memoization built on top of the inner caches — clearing only the inners is a no-op for the outer. The comment "lodash memoize returns the cached result without ever reaching the cleared inners" is a subtle trap. Dynamic skills (discovered during file operations) are inserted at a specific position in the command list (after plugin skills, before builtins) and deduplicated against existing names — not prepended or appended blindly.

**Mapping:** Our commands registry should use the same two-tier model: a memoized load (expensive I/O) plus per-call availability/enabled filtering (can't cache, depends on runtime state). The `BRIDGE_SAFE_COMMANDS` allowlist pattern is directly adoptable for any environment where a subset of commands should be callable from a remote client.

---

### src/history.ts — 464 lines

**Core functions:**
- `addToHistory(command)` — public entry point. Skips if `CLAUDE_CODE_SKIP_PROMPT_HISTORY` env var is set (prevents tmux verification sessions from polluting user history). Fires `addToPromptHistory` async.
- `getHistory()` — async generator. Yields current-session entries first (in order), then other sessions, up to `MAX_HISTORY_ITEMS = 100`. Ensures concurrent sessions don't interleave up-arrow navigation.
- `getTimestampedHistory()` — for ctrl+r picker: deduped by display text, lazy-resolved paste content via `resolve()` callback.
- `removeLastFromHistory()` — one-shot undo. Fast path: pop from `pendingEntries`. Slow path: add timestamp to `skippedTimestamps` set (for entries already flushed to disk).
- `expandPastedTextRefs(input, pastedContents)` — replaces `[Pasted text #N]` placeholders with actual content. Processes in reverse order so earlier offsets stay valid after later replacements.
- `flushPromptHistory(retries)` — async, retries up to 5 times with 500ms sleep between. Uses a file lock for multi-process safety.

**Production insight:** Large pasted content (>1024 bytes) is stored by hash in a separate paste store (`storePastedText`) with a fire-and-forget disk write — the history entry records only the hash, not the content. This makes history entries cheap to write and read. The `skippedTimestamps` set (for undo after flush) and `pendingEntries` array (for undo before flush) together handle the race between undo and the async flush without any synchronization primitives — just set-membership checks at read time.

**Mapping:** Our REPL history (if any) should store large pastes externally and reference by hash. The current-session-first ordering (not pure chronological) for up-arrow navigation is a UX insight worth carrying forward.

---

### src/setup.ts — 477 lines

**Core function:**
- `setup(cwd, permissionMode, allowDangerouslySkipPermissions, worktreeEnabled, ...)` — called once at process start. Sequentially: start UDS messaging server, capture teammate snapshot, restore interrupted terminal settings, `setCwd`, capture hooks config snapshot, optionally create git worktree and tmux session, register background services (session memory, context collapse, lock version, attribution hooks, file access hooks, team memory watcher), drain analytics sinks, emit `tengu_started` beacon, prefetch API key, check for release notes.

**Production insight:** The `tengu_started` analytics event is emitted as the EARLIEST POSSIBLE reliable signal after the analytics sink is attached, before any parsing or I/O that could throw. The comment references a P0 crash (inc-3694) where a CHANGELOG parse error after startup killed the beacon. The ordering is load-bearing for release health monitoring. The hooks config snapshot is captured AFTER `setCwd` (so hooks load from the correct directory) but before any user interaction. The `--bare` mode (scripted/non-interactive) skips the attribution hook, repo classification, session file access analytics, and team memory watcher because none of these produce value for scripted calls — and the ~49ms attribution hook stat check is pure overhead.

**Mapping:** Our `setup.py` should emit a session-started telemetry event as close to process entry as possible, before any logic that could throw. The ordered startup sequence (UDS → snapshot → cwd → hooks → background jobs → analytics → prefetch) is a template worth following.

---

### src/state/ (5 files, ~950 lines total)

**Core types/functions:**
- `store.ts` (34 lines): `createStore<T>(initialState, onChange?)` — minimal React-external state store. Three methods: `getState`, `setState(updater)`, `subscribe(listener)`. `setState` uses `Object.is` to skip no-op updates.
- `AppState` (in AppStateStore.ts) — the React-bound UI state (distinct from `bootstrap/state.ts`'s process-global). Contains `toolPermissionContext`, `tasks`, `mcp`, `plugins`, `settings`, `remoteConnectionStatus`, bridge fields, speculation state, teammate state, and optional feature-gated fields (computer use MCP, REPL VM context, team context).
- `AppStateProvider` (AppState.tsx, React-compiled) — wraps the REPL tree. Creates the store, registers settings change listener, provides context. Prevents nested providers.
- `selectors.ts` — computed views over `AppState` (e.g. `getActiveTasks`).
- `onChangeAppState.ts` — side-effect handler called on every state transition.

**Production insight:** `AppState` uses `DeepImmutable<{...}>` on most fields, but `tasks` and `agentNameRegistry` are explicitly excluded from `DeepImmutable` because they contain function types (abort controllers, callbacks) that don't survive deep freezing. The `store.ts` is 34 lines — it's not Redux, Zustand, or Jotai. It's a hand-written minimal store with exactly the surface area needed: no selectors, no middleware, no devtools. The `AppStateStore` (process-bound) is entirely separate from `bootstrap/state.ts` (module-global singleton) — there are two state systems, one for React rendering and one for everything else.

**Mapping:** The `createStore` pattern (34 lines, typed updater function, reference equality bail-out, subscriber notification) is directly implementable in Python for any UI or async state management. The explicit split between "React app state" and "process-global singleton state" is the right architecture for any agent with both a REPL and background threads.

---

### src/bridge/ (29 files, 12,613 lines total)

**Core files and functions:**
- `bridgeMain.ts` (2999 lines): `runBridgeLoop(config, environmentId, ...)` — the CCR (Claude Code Remote) daemon. Poll loop: fetch work items from backend, spawn child `claude` processes for each session, manage process lifecycle, handle capacity wake signals, exponential backoff with give-up timers, sleep detection via elapsed-time comparison against `2 × connCapMs`.
- `replBridge.ts` (2406 lines): `ReplBridgeHandle` interface and `initBridgeCore(params)` — the always-on bridge that runs inside an interactive REPL session. Opens a WebSocket to claude.ai, polls for inbound messages, routes control requests (permission, cancel), funnels session events back to the web client.
- `bridgeMessaging.ts` (461 lines): `handleIngressMessage`, `handleServerControlRequest`, `BoundedUUIDSet` — message dedup and routing layer. `BoundedUUIDSet` is a fixed-size ring buffer that prevents unbounded memory growth for seen message IDs.
- `sessionRunner.ts` (550 lines): `createSessionSpawner` — manages child process spawning with worktree isolation, tmux session creation, output redirection.
- `types.ts` (262 lines): `BridgeConfig`, `WorkSecret`, `WorkData`, `SpawnMode`, `BridgeWorkerType`, `SessionDoneStatus`.

**Production insight:** The bridge operates as a completely separate process (daemon mode via `runBridgeLoop`) OR as an in-process bridge running inside the REPL (`replBridge`). The two share `remoteBridgeCore.ts` but have different lifecycles. `WorkSecret` is a base64url-encoded JSON blob delivered with each work item — it carries the session ingress token, API base URL, auth tokens, and optional claude_code_args. This is how the backend injects per-session config into ephemeral child processes without environment variable pollution. The `FlushGate` (bridge/flushGate.ts) is a one-shot barrier that holds the first POST until the REPL has had time to mount — without it, the web client receives the session init message before the REPL is ready to process it.

**Mapping:** The `WorkSecret` pattern (encode session-specific config in a signed blob, not env vars) is applicable when spawning child agent processes from a coordinator. The two-mode architecture (daemon bridge vs. in-process bridge sharing core logic) is a template for building remote-control infrastructure that works both ways.

---

### src/remote/ (4 files, ~1020 lines total)

**Core classes/functions:**
- `RemoteSessionManager` (343 lines): manages one CCR remote session from the viewer side. Wraps `SessionsWebSocket`, routes `SDKMessage` vs. `SDKControlRequest` vs. `SDKControlResponse`, handles permission request/response flow with a `pendingPermissionRequests` Map. `sendUserMessage(text)` posts via HTTP.
- `SessionsWebSocket` (404 lines): WebSocket client with exponential backoff reconnect, 60s disconnect timeout (disabled in viewer-only mode), message parsing with type narrowing.
- `sdkMessageAdapter.ts` (302 lines): pure conversion functions from `SDKMessage` (wire format) to internal `Message` types for REPL rendering. No state.
- `remotePermissionBridge.ts` (78 lines): bridges CCR permission requests to the local REPL's permission dialog.

**Production insight:** `RemoteSessionManager` distinguishes `viewerOnly` mode where Ctrl+C/Escape do NOT send interrupt to the remote agent and the 60s reconnect timeout is disabled. This is the `claude assistant` viewer: you watch a remote agent run but cannot control it. The distinction is encoded in `RemoteSessionConfig.viewerOnly` and enforced throughout the manager — separate from the connection logic, not scattered through conditionals. `sdkMessageAdapter.ts` is entirely pure functions — no state, no side effects. Adapter layer is isolated so it can be tested without any runtime context.

**Mapping:** The `viewerOnly` mode (read-only observer without control rights) is directly applicable to any multi-agent system where some agents monitor others. The pure adapter pattern (separate file, no imports of business logic) for protocol translation is directly adoptable.

---

### src/tasks/ (9 files + subdirs, ~1500 lines total)

**Core types/functions:**
- `TaskState` union (types.ts): `LocalShellTaskState | LocalAgentTaskState | RemoteAgentTaskState | InProcessTeammateTaskState | LocalWorkflowTaskState | MonitorMcpTaskState | DreamTaskState`. All task types have a common `TaskStateBase` with `id`, `type`, `status`, `description`, `createdAt`.
- `LocalAgentTaskState` (LocalAgentTask.tsx): adds `agentId`, `prompt`, `selectedAgent`, `abortController`, `progress: AgentProgress`, `isBackgrounded`, `pendingMessages[]`, `retain` (UI holding the task), `diskLoaded` (bootstrap has merged sidechain JSONL), `evictAfter` (panel GC deadline).
- `ProgressTracker` / `updateProgressFromMessage` / `getProgressUpdate` — track tool call count and token count from assistant messages. Input tokens are kept as latest (cumulative in API), output tokens are summed per-turn.
- `LocalMainSessionTask.ts`: `registerMainSessionTask` — when user backgrounds the main session (Ctrl+B), creates a `LocalAgentTaskState` with `agentType: 'main-session'` and routes the in-progress query to a task-specific transcript file (never the main session file).
- `DreamTask.ts`: `registerDreamTask`, `addDreamTurn` — surfaces the auto-dream (memory consolidation) subagent in the UI task registry. The dream agent runs 4 phases (orient/gather/consolidate/prune) but the task state doesn't parse them — it just flips `phase` from `'starting'` to `'updating'` when the first Edit/Write tool call lands.

**Production insight:** The `retain` flag on `LocalAgentTaskState` is separate from `viewingAgentTaskId` in `AppState`. `retain` means "the UI is holding this task (stream-append mode, disk bootstrap)"; `viewingAgentTaskId` means "what the user is LOOKING AT." A task can be retained without being viewed, and vice versa. The `evictAfter` timestamp (panel GC deadline) is set at terminal transitions and on unselect, cleared on retain — a fine-grained panel lifecycle separate from task status. `pendingMessages[]` on `LocalAgentTaskState` queues `SendMessage` payloads that arrive mid-turn and are drained at tool-round boundaries — this is how inter-agent messaging is implemented without interrupting the current tool execution.

**Mapping:** The `ProgressTracker` (input-token-latest, output-token-cumulative) is directly adoptable for our subagent progress display. The `pendingMessages` drain-at-boundary pattern is the right model for inter-agent message passing: buffer, don't interrupt. The `retain` / `evictAfter` panel lifecycle is worth implementing if we build a multi-agent UI.

---

## Cross-Cutting Patterns Summary

1. **Two state systems:** `bootstrap/state.ts` is the process-global singleton (module-level, no React, DAG leaf). `state/AppStateStore.ts` is the React-bound UI state. They are separate and serve different masters.

2. **Fail-closed defaults:** `buildTool` defaults `isConcurrencySafe → false`, `isReadOnly → false`. Permissive is never the default.

3. **Memoize-expensive, re-evaluate-cheap:** `loadAllCommands` is memoized by cwd. `meetsAvailabilityRequirement` and `isEnabled` run fresh every call. The pattern is explicit and consistent.

4. **Feature-flag dead code elimination:** `feature('FEATURE_NAME') ? require(...)  : null` is how optional subsystems (VOICE_MODE, CONTEXT_COLLAPSE, KAIROS, etc.) are excluded from external builds without tree-shaking failures.

5. **Fire-and-forget with cleanup registration:** async operations that must not block the critical path (transcript write in bare mode, paste store write) are fire-and-forget but always registered with `registerCleanup` so they complete before process exit.

6. **Generator protocol as the tool-loop contract:** `query()` and `submitMessage()` are async generators. Callers iterate via `for await`. This makes backpressure, early exit, and error propagation natural — no callback hell, no event emitter.
