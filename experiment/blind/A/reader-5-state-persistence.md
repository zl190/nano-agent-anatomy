# Reader 5 — State, Persistence, Memory, Permissions
**Assigned directories:** `src/state/`, `src/memdir/`, `src/services/plugins/`, `src/hooks/` (key files), `src/utils/` (key files)

---

## 1. `src/state/` — Application State

### Line counts
| File | Lines |
|---|---|
| AppStateStore.ts | 569 |
| onChangeAppState.ts | 171 |
| teammateViewHelpers.ts | 141 |
| selectors.ts | 76 |
| store.ts | 34 |

---

### `store.ts` (34 lines)

**The entire reactive state layer is 34 lines.** No Redux, no Zustand, no React context.

```typescript
export type Store<T> = {
  getState: () => T
  setState: (updater: (prev: T) => T) => void
  subscribe: (listener: Listener) => () => void
}

export function createStore<T>(initialState: T, onChange?: OnChange<T>): Store<T>
```

- `setState` takes an updater function (not a value), runs `Object.is` diff check, then notifies all listeners.
- The `onChange` callback is the only side-effect hook — it receives `{ newState, oldState }`. This is where `onChangeAppState.ts` plugs in.

**Production insight:** A hand-rolled pub/sub is the entire state substrate. The `onChange` callback fires after every mutation — it's the central "effect layer" without being React-specific.

---

### `AppStateStore.ts` (569 lines) — the God Object

`AppState` is a single massive type with ~60 top-level fields:

```typescript
export type AppState = DeepImmutable<{
  settings, verbose, mainLoopModel, statusLineText, expandedView,
  toolPermissionContext, kairosEnabled, replBridge*, mcp, plugins,
  agentDefinitions, fileHistory, attribution, todos, notifications,
  speculation, promptSuggestion, sessionHooks, computerUseMcpState,
  replContext, teamContext, inbox, workerSandboxPermissions, ...
}> & {
  // Excluded from DeepImmutable because they contain function types:
  tasks: { [taskId: string]: TaskState }
  agentNameRegistry: Map<string, AgentId>
  ...
}
```

Key design decisions embedded in comments:
- **Why God Object**: "PromptInputFooter → CompanionSprite can read their own focused state" — footerSelection lives in AppState not local state so pill components rendered outside PromptInput can read it without prop drilling.
- **DeepImmutable gap**: `tasks` and `agentNameRegistry` are excluded because `DeepImmutable` can't handle function types (tasks contain `AbortController`, callbacks). Runtime mutability is tolerated there.
- **`getDefaultAppState()`** uses lazy `require()` for `teammate.ts` to avoid circular dependencies — TypeScript static imports would create a cycle.

**Production insight:** In a large multi-surface app, the single God Object is a deliberate tradeoff. Prop drilling across 6+ components is worse than one big shared type. TypeScript-only immutability (`DeepImmutable`) is enforced at the type level, not runtime.

---

### `onChangeAppState.ts` (171 lines) — the reactive side-effect layer

This function is the `onChange` callback registered with `createStore`. It runs after every `setState`. It watches diffs:

```typescript
export function onChangeAppState({ newState, oldState }: { ... }) {
  // toolPermissionContext.mode → CCR sync + SDK notification
  if (prevMode !== newMode) {
    notifySessionMetadataChanged({ permission_mode: newExternal, ... })
    notifyPermissionModeChanged(newMode)
  }
  // mainLoopModel → settings persistence
  // expandedView → globalConfig persistence
  // verbose → globalConfig persistence
  // settings → clear auth caches, re-apply env vars
}
```

The comment on the permission mode block is revealing:
> "Prior to this block, mode changes were relayed to CCR by only 2 of 8+ mutation paths [...] Every other path — Shift+Tab cycling, ExitPlanModePermissionRequest, /plan slash command, rewind, REPL bridge's onSetPermissionMode — mutated AppState without telling CCR."

**Production insight:** Scattering "save to disk / notify external service" across 8+ callsites leads to missed notifications. The fix: one diff-watcher that owns all side effects. Any future callsite automatically gets sync for free.

---

### `selectors.ts` (76 lines) — derived state

Pure functions over AppState:

```typescript
function getViewedTeammateTask(appState): InProcessTeammateTaskState | undefined
// Returns currently-viewed teammate task, or undefined if not viewing

function getActiveAgentForInput(appState): ActiveAgentForInput
// Discriminated union: { type: 'leader' } | { type: 'viewed', task } | { type: 'named_agent', task }
// Routes user input to the correct agent
```

**Production insight:** Selectors are extracted to avoid re-deriving the same logic in multiple components. The discriminated union return type forces callers to handle all routing cases.

---

### `teammateViewHelpers.ts` (141 lines) — UI state transitions

Manages `retain` and `evictAfter` patterns for agent transcript viewing:

```typescript
function enterTeammateView(taskId, setAppState): void
// Sets retain: true → blocks eviction, enables stream-append, triggers disk bootstrap

function exitTeammateView(setAppState): void
// Clears retain, releases messages back to stub form

function stopOrDismissAgent(taskId, setAppState): void
// Running → abort; terminal → evictAfter: 0 (immediate evict)
```

The `release(task)` helper:
```typescript
function release(task): LocalAgentTaskState {
  return { ...task, retain: false, messages: undefined, diskLoaded: false,
    evictAfter: isTerminalTaskStatus(task.status) ? Date.now() + 30_000 : undefined }
}
```

**Production insight:** "retain" is a lifecycle flag, not a UI flag. It controls whether a task loads from disk, whether stream-append is enabled, and whether the GC timer fires. Decoupling memory management from visibility gives fine-grained control.

---

## 2. `src/memdir/` — Persistent Memory System

### Line counts
| File | Lines |
|---|---|
| paths.ts | 278 |
| memdir.ts | 507 |
| teamMemPaths.ts | 292 |
| memoryTypes.ts | 271 |
| findRelevantMemories.ts | 141 |
| teamMemPrompts.ts | 100 |
| memoryScan.ts | 94 |
| memoryAge.ts | 53 |

Total: ~1,736 lines just for the memory system.

---

### `paths.ts` (278 lines) — path resolution + security

```typescript
export const getAutoMemPath = memoize(
  (): string => { /* resolution order below */ },
  () => getProjectRoot()  // cache key
)
```

Resolution order:
1. `CLAUDE_COWORK_MEMORY_PATH_OVERRIDE` env var (for Cowork — VM sessions have non-stable CWDs)
2. `autoMemoryDirectory` in settings.json (trusted sources only: policy/local/user — NOT projectSettings)
3. `~/.claude/projects/<sanitized-canonical-git-root>/memory/`

Security design in `validateMemoryPath()`:
- Rejects relative paths, root/near-root paths, Windows drive roots, UNC paths, null bytes
- Supports `~/` expansion only for user-trusted settings sources

Why canonical git root? "All worktrees of the same repo share one auto-memory directory." Without this, `git worktree add` would give each worktree its own memory.

Why memoized by project root? The function is called on every tool-use message re-render. Each cache miss triggers `getSettingsForSource × 4` → `readFileSync`.

**Production insight:** Memory path security has multiple layers: validation at setting-parse time, memoization for performance, canonical git root for worktree sharing. The security model matches trust levels: committed project settings cannot set memory path (prevents malicious repos gaining write access to `~/.ssh`).

---

### `memdir.ts` (507 lines) — the prompt builder

`buildMemoryLines()` generates the full memory instructions injected into the system prompt. The actual rules Claude follows for memory are TypeScript string arrays here.

`loadMemoryPrompt()` dispatches across three modes:
```
KAIROS + active → buildAssistantDailyLogPrompt()  // append-only log, nightly distill
TEAMMEM enabled → buildCombinedMemoryPrompt()      // private + team directories
otherwise       → buildMemoryLines() solo
```

Key design in `buildAssistantDailyLogPrompt()`:
```
Prompt tells model to append to: <memdir>/logs/YYYY/MM/YYYY-MM-DD.md
```
This prompt is cached (systemPromptSection cache). The cache is NOT invalidated on midnight rollover — the date is injected separately via a `date_change` attachment. This preserves the prompt cache prefix across midnight.

`DIR_EXISTS_GUIDANCE` shipped string:
> "This directory already exists — write to it directly with the Write tool (do not run mkdir or check for its existence)."

**Production insight:** The harness creates the directory, then tells the model it already exists. Without this, models burned turns on `ls`/`mkdir`. The solution isn't technical — it's prompt-engineering the expected precondition.

---

### `findRelevantMemories.ts` (141 lines) — turn-level injection via side-query

```typescript
export async function findRelevantMemories(
  query: string,
  memoryDir: string,
  signal: AbortSignal,
  recentTools: readonly string[] = [],
  alreadySurfaced: ReadonlySet<string> = new Set(),
): Promise<RelevantMemory[]>
```

The flow:
1. `scanMemoryFiles()` → reads frontmatter of all `.md` files
2. Filter out `alreadySurfaced` (files shown in prior turns)
3. `selectRelevantMemories()` → 256-token Sonnet call with structured output
4. Returns up to 5 paths + mtimeMs

The `recentTools` signal is subtle:
```typescript
// When actively using a tool, don't surface that tool's reference docs
// (the conversation already contains working usage — false positive on keyword overlap)
```

**Production insight:** Memory selection is itself an LLM call. A 256-token Sonnet call at each turn is cheap enough to be worth the context quality improvement. The `alreadySurfaced` filter prevents re-suggesting files already in context.

---

### `memoryScan.ts` (94 lines)

```typescript
export async function scanMemoryFiles(memoryDir, signal): Promise<MemoryHeader[]>
```

Single-pass: `readFileInRange()` returns both content AND `mtimeMs`, so stat + read happen together. Sorts newest-first, caps at 200 files.

```typescript
export function formatMemoryManifest(memories: MemoryHeader[]): string
// Output: "- [type] filename.md (2025-03-01T10:00:00Z): one-line description"
```

**Production insight:** The manifest format is critical — it's what the Sonnet selector sees. Type + filename + timestamp + description in one line gives the selector enough signal without burning context.

---

### `memoryAge.ts` (53 lines)

```typescript
export function memoryAge(mtimeMs: number): string
// Returns: "today" | "yesterday" | "N days ago"

export function memoryFreshnessText(mtimeMs: number): string
// Returns "" for ≤1 day; returns staleness caveat string for older memories
```

The comment: "Models are poor at date arithmetic — a raw ISO timestamp doesn't trigger staleness reasoning the way '47 days ago' does."

For memories >1 day old, the injected text:
> "This memory is 47 days old. Memories are point-in-time observations, not live state — claims about code behavior or file:line citations may be outdated. Verify against current code before asserting as fact."

**Production insight:** Human-readable relative age is a deliberate UX decision for the model. The staleness caveat names the specific failure mode (file:line citations going stale) to make verification behavior concrete.

---

### `memoryTypes.ts` (271 lines) — the source of truth for memory rules

The 4-type taxonomy:
- `user` — role, goals, knowledge
- `feedback` — corrections + validations ("record from failure AND success")
- `project` — ongoing work, context not derivable from git
- `reference` — pointers to external systems

The `WHAT_NOT_TO_SAVE_SECTION` (eval-validated):
```
"These exclusions apply even when the user explicitly asks you to save.
If they ask you to save a PR list or activity summary, ask what was
surprising or non-obvious about it — that is the part worth keeping."
```

Comment on `TRUSTING_RECALL_SECTION`:
```
H1 (verify function/file claims): 0/2 → 3/3 via appendSystemPrompt.
When buried as a bullet under "When to access", dropped to 0/3 —
position matters.
```

**Production insight:** The memory instructions are A/B tested against evals. Section headers are measured against success rates. "Before recommending from memory" (action cue at decision point) went 3/3. "Trusting what you recall" (abstract) went 0/3. Same body text, different header.

---

### `teamMemPaths.ts` (292 lines) — production-grade path security

Two-pass symlink validation for team memory writes:

**Pass 1 (fast):** `path.resolve()` normalizes `..` segments and checks string containment.

**Pass 2 (symlink-safe):** `realpathDeepestExisting()` walks up the tree until it finds an existing ancestor, resolves symlinks via `realpath()`, re-joins the non-existing tail, then checks containment against the real team dir.

```typescript
// Dangling symlinks detected via lstat-vs-ENOENT logic:
// - realpath ENOENT: could be truly non-existent (safe) OR dangling symlink (unsafe)
// - lstat distinguishes: succeeds for dangling symlinks
```

Referenced security review: PSR M22186, PSR M22187.

**Production insight:** `path.resolve()` alone is insufficient for write-path validation in a system where the model can write to user-configured directories. An attacker who places a symlink inside teamDir pointing to `~/.ssh/authorized_keys` would pass `resolve()`-based checks. The realpath layer closes this.

---

## 3. `src/services/plugins/` — Plugin Management

### Line counts
| File | Lines |
|---|---|
| pluginCliCommands.ts | 344 |
| PluginInstallationManager.ts | 184 |
| pluginOperations.ts | ~300+ |

---

### `PluginInstallationManager.ts` (184 lines)

```typescript
export async function performBackgroundPluginInstallations(setAppState): Promise<void>
```

Pattern: background work that streams status into AppState:
1. Compute diff upfront → initialize `installationStatus.marketplaces` with `pending` entries
2. Call `reconcileMarketplaces({ onProgress })`
3. `onProgress` maps events → `setAppState` mutations (`installing` → `installed` | `failed`)
4. After completion: new installs → `refreshActivePlugins()`; updates only → `needsRefresh: true`

The auto-refresh path:
```typescript
// New marketplaces → auto-refresh. Fixes "plugin not found" errors from cache-only
// load on fresh homespace where marketplace cache was empty.
```

**Production insight:** The UI sees only AppState status fields — it never awaits the background work. The status streaming pattern decouples background I/O from UI rendering. `needsRefresh: true` is a deferred action: show notification, let user choose when.

---

### `pluginCliCommands.ts` (344 lines)

Thin CLI layer over `pluginOperations.ts`:
- Console output + `process.exit()`
- Analytics events on both success and failure (failure events enable dashboard success-rate computation)
- PII routing via `_PROTO_*` prefix → privileged BigQuery columns

```typescript
// _PROTO_plugin_name routes to PII-tagged plugin_name/marketplace_name BQ columns.
// Unredacted plugin_id was previously logged to general-access additional_metadata
// for all users — dropped in favor of the privileged column route.
```

**Production insight:** Separating CLI wrapper from pure operations (`pluginOperations.ts`) makes the operations testable without CLI side effects. Failure analytics events are as important as success events for monitoring command reliability.

---

## 4. `src/hooks/` — Key Architectural Hooks

### `toolPermission/PermissionContext.ts` (388 lines)

The permission system abstraction. `createPermissionContext()` returns a frozen object with all permission operations:

```typescript
const ctx = createPermissionContext(tool, input, toolUseContext, assistantMessage, toolUseID, ...)
// Contains: logDecision, logCancelled, persistPermissions, cancelAndAbort,
//           tryClassifier, runHooks, buildAllow, buildDeny,
//           handleUserAllow, handleHookAllow, pushToQueue, removeFromQueue
```

`createResolveOnce()` — the atomic race guard:
```typescript
function createResolveOnce(resolve): ResolveOnce<T> {
  let claimed = false, delivered = false
  return {
    resolve(value) { if (delivered) return; delivered = true; claimed = true; resolve(value) },
    isResolved() { return claimed },
    claim() { if (claimed) return false; claimed = true; return true }  // atomic check-and-mark
  }
}
```

`claim()` vs `isResolved()`: `claim()` is used when you have async work *between* the check and the resolve. `isResolved()` is used for early-exit guards where no async work follows.

**Production insight:** The permission context encapsulates all operations into one object passed to three different handlers (coordinator, interactive, swarm worker). The factory pattern keeps handler code clean. `createResolveOnce` solves the multi-source async race without locks.

---

### `handlers/interactiveHandler.ts` (536 lines)

The main agent permission flow races 4 sources:

```
1. Local UI dialog (onAllow/onReject callbacks on the queue item)
2. CCR bridge (claude.ai web UI) — bridgeCallbacks.onResponse
3. Channel (Telegram/iMessage) — channelCallbacks.onResponse
4. Hooks + bash classifier (async, background)
```

Each racer calls `claim()` before proceeding. First one wins.

```typescript
// Grace period: ignore user interactions in the first 200ms to prevent
// accidental keypresses from canceling the classifier prematurely
const GRACE_PERIOD_MS = 200
```

Classifier checkmark behavior:
```typescript
// Keep checkmark visible, then remove dialog.
// 3s if terminal is focused (user can see it), 1s if not.
// User can dismiss early with Esc via onDismissCheckmark.
const checkmarkMs = getTerminalFocused() ? 3000 : 1000
```

**Production insight:** Four concurrent sources with exactly-once resolution. The `claim()` pattern beats semaphores/mutexes for this case — it's a one-shot promise, not a shared resource. The channel path (Telegram) sends a structured notification and subscribes; the reply intercept happens before the message reaches Claude.

---

### `handlers/swarmWorkerHandler.ts` (159 lines)

```typescript
// Register callback BEFORE sending the request to avoid race condition
// where leader responds before callback is registered
registerPermissionCallback({ requestId: request.id, ... })
void sendPermissionRequestViaMailbox(request)
```

Registration-before-send ordering is the production lesson: sending before registering a callback creates a window where the response arrives and no one handles it.

**Production insight:** In distributed systems (even in-process), register before publish. The abort signal teardown clears the pending indicator — no dangling state.

---

### `useQueueProcessor.ts` (68 lines)

```typescript
export function useQueueProcessor({ executeQueuedInput, hasActiveLocalJsxUI, queryGuard }): void
```

Processes the command queue when conditions align:
- `isQueryActive` (from queryGuard via useSyncExternalStore) = false
- `hasActiveLocalJsxUI` = false
- `queueSnapshot.length > 0`

The hook uses `useSyncExternalStore` for both the queue and the guard — guarantees re-render when either changes, bypassing React context propagation delays in Ink.

**Production insight:** The queue processor is purely reactive. No polling, no timeouts. Two useSyncExternalStore subscriptions ensure re-evaluation on any relevant state change.

---

### `useTasksV2.ts` (250 lines)

`TasksV2Store` singleton — prevents watcher churn:

```typescript
class TasksV2Store {
  // Single fs.watch on the tasks directory
  // + onTasksUpdated (in-process subscription)
  // + 5s fallback poll (for incomplete tasks only)
  // Subscriber reference counting: #start on first subscribe, #stop on last
}
```

Why singleton: "The Spinner mounts/unmounts every turn — per-hook watchers caused constant watch/unwatch churn."

Hide timer: 5s after all tasks complete → `resetTaskList()` + `hidden = true`.

**Production insight:** The singleton store with subscriber counting is the React way to share expensive resources (file watchers) across multiple component instances that mount/unmount frequently.

---

### `useMailboxBridge.ts` (21 lines)

```typescript
export function useMailboxBridge({ isLoading, onSubmitMessage }): void {
  const revision = useSyncExternalStore(subscribe, getSnapshot)
  useEffect(() => {
    if (isLoading) return
    const msg = mailbox.poll()
    if (msg) onSubmitMessage(msg.content)
  }, [isLoading, revision, mailbox, onSubmitMessage])
}
```

The mailbox is an external queue. `useSyncExternalStore` on `revision` makes React re-render when any message arrives. The effect only consumes when not loading.

**Production insight:** External message queues bridge cleanly into React via useSyncExternalStore. The `revision` counter (not the message itself) is the snapshot — React re-renders on increment, then the effect reads the actual data.

---

### `useSwarmInitialization.ts` (81 lines)

Two initialization paths:
- **Resumed session**: reads `teamName`/`agentName` from first transcript message → `initializeTeammateContextFromSession()`
- **Fresh spawn**: reads from env vars via `getDynamicTeamContext()` → `initializeTeammateHooks()`

**Production insight:** Session resume is a first-class concern. The team context is serialized into the transcript (not just env vars) so `--resume` works correctly across process restarts.

---

## 5. `src/utils/` — Key Utility Files

### `agentContext.ts` (178 lines) — AsyncLocalStorage for concurrent agents

```typescript
const agentContextStorage = new AsyncLocalStorage<AgentContext>()

export function runWithAgentContext<T>(context: AgentContext, fn: () => T): T {
  return agentContextStorage.run(context, fn)
}
```

The comment explains why NOT AppState:
> "When agents are backgrounded (ctrl+b), multiple agents can run concurrently in the same process. AppState is single shared state that would be overwritten, causing Agent A's events to incorrectly use Agent B's context. AsyncLocalStorage isolates each async execution chain."

Two context types:
- `SubagentContext` — Agent tool agents (in-process, quick delegated tasks)
- `TeammateAgentContext` — swarm teammates (part of a team, have team coordination)

`consumeInvokingRequestId()` — emits the spawn/resume telemetry edge exactly once per invocation:
```typescript
// Sparse edge semantics: invokingRequestId appears on exactly one
// tengu_api_success/error per invocation, so a non-NULL value
// marks a spawn/resume boundary.
```

**Production insight:** AsyncLocalStorage is the correct tool when multiple async execution chains share a process. The "consume exactly once" pattern for telemetry prevents duplicate spawn edges in analytics.

---

### `activityManager.ts` (164 lines) — user vs CLI time tracking

```typescript
class ActivityManager {
  private activeOperations = new Set<string>()  // deduplicate overlapping ops
  startCLIActivity(operationId: string): void
  endCLIActivity(operationId: string): void
  recordUserActivity(): void  // only counted when CLI is inactive
}
```

CLI activity takes precedence — user time not recorded while CLI is active. 5s user activity timeout window (gap > 5s = inactive).

**Production insight:** The Set-based deduplication means multiple overlapping operations still count as one CLI active period. The singleton pattern with a `resetInstance()` for testing is the standard approach.

---

### `CircularBuffer.ts` (84 lines)

```typescript
class CircularBuffer<T> {
  add(item: T): void       // O(1), evicts oldest when full
  getRecent(count: number): T[]
  toArray(): T[]           // oldest → newest
}
```

**Production insight:** When you need a bounded rolling window (recent tool calls, context snapshots, error history), a circular buffer beats splice/shift on arrays for O(1) insertion.

---

### `cleanupRegistry.ts` (25 lines)

```typescript
const cleanupFunctions = new Set<() => Promise<void>>()

export function registerCleanup(cleanupFn): () => void {
  cleanupFunctions.add(cleanupFn)
  return () => cleanupFunctions.delete(cleanupFn)  // unregister function
}

export async function runCleanupFunctions(): Promise<void> {
  await Promise.all(Array.from(cleanupFunctions).map(fn => fn()))
}
```

**Production insight:** The returned unregister function lets callers clean up their registration without needing a central registry manager. `Promise.all` runs all cleanups concurrently — appropriate for independent teardown tasks.

---

### `commandLifecycle.ts` (21 lines)

```typescript
let listener: CommandLifecycleListener | null = null
export function setCommandLifecycleListener(cb): void { listener = cb }
export function notifyCommandLifecycle(uuid, state): void { listener?.(uuid, state) }
```

Single-listener notification for command start/complete. Used to drive shell completions and status line updates.

**Production insight:** Module-level singleton listener — appropriate when there's exactly one consumer. No need for a full pub/sub when cardinality is 1.

---

## Cross-cutting Production Insights

### 1. The 34-line store is the reactive substrate
The entire state management is `createStore`. Everything else (selectors, helpers, hooks) consumes it via `getState`/`setState`/`subscribe`. React hooks use `useSyncExternalStore` against the store's `subscribe`.

### 2. onChangeAppState is the "diff → side effect" pattern
Before this pattern, 8+ mutation sites forgot to notify CCR. After: any `setState` that changes a watched field automatically triggers persistence/sync. No callsite changes needed.

### 3. Memory instructions are eval-validated TypeScript strings
The prompt text in `memoryTypes.ts` has comments citing A/B test results. Section headers are chosen based on failure/success rates. Position in the prompt matters ("When buried as a bullet... dropped to 0/3 — position matters").

### 4. Memory selection is a side-query, not context injection
Rather than injecting all memory files every turn, a 256-token Sonnet call selects the 5 most relevant. This is the "meta-agent" pattern — a cheap LLM call to improve the main agent's context quality.

### 5. Multi-source async races use claim(), not locks
Permission resolution has 4+ concurrent sources. The `claim()` atomic check-and-mark pattern resolves the race without semaphores. First caller to `claim()` wins; others check `isResolved()` before heavy work.

### 6. AsyncLocalStorage for concurrent in-process agents
When multiple agents background-run in the same process, AppState is not thread-safe for agent identity. AsyncLocalStorage provides implicit context propagation per async execution chain.

### 7. Singleton stores prevent resource churn
`TasksV2Store` is one file watcher shared across N hook instances. Subscriber reference counting starts/stops the watcher lazily. The Spinner's frequent mount/unmount doesn't cause watcher churn.

### 8. Register before publish (swarm worker)
`registerPermissionCallback()` is called before `sendPermissionRequestViaMailbox()`. The ordering prevents a race where the leader responds before the callback is registered.

---

## Adoptable Patterns for This Project

| Pattern | Source | How to adopt |
|---|---|---|
| 34-line pub/sub store | `store.ts` | For Python agents: a `Store` class with `get_state/set_state/subscribe`. |
| diff-watcher side effects | `onChangeAppState.ts` | One function watches all state changes and triggers disk persistence/notifications. |
| 4-type memory taxonomy | `memoryTypes.ts` | user / feedback / project / reference. What NOT to save is as important as the types. |
| Side-query memory selection | `findRelevantMemories.ts` | Small LLM call selects relevant files from manifest rather than injecting all. |
| Human-readable memory ages | `memoryAge.ts` | "47 days ago" not ISO timestamp. Triggers staleness reasoning more reliably. |
| Atomic `createResolveOnce` | `PermissionContext.ts` | For multi-source async races: `claim()` returns true exactly once. |
| AsyncLocalStorage context | `agentContext.ts` | For concurrent agents in same process: `AsyncLocalStorage` vs shared state. |
| Background status streaming | `PluginInstallationManager.ts` | Start background work → initialize status in state → onProgress updates state. |
| Subscriber-counted singleton store | `useTasksV2.ts` | Shared expensive resource (file watcher) with lazy start/stop. |
| Register-before-publish ordering | `swarmWorkerHandler.ts` | In distributed callbacks, register callback before sending the triggering message. |
| `DIR_EXISTS_GUIDANCE` | `memdir.ts` | Harness creates directory → tells model it already exists → saves one `ls` turn. |
