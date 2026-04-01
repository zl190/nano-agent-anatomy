# Claude Code UI & Terminal Architecture Analysis
## Assigned: `/src/components/`, `/src/ink/`, `/src/cli/`

---

## Executive Summary

Claude Code's terminal UI is a ~44K LOC system built on three layers: a custom React renderer for terminals (Ink, ~13K LOC), a React component tree for the actual UI (24K+ LOC across 389 files), and CLI/remote integration handlers (~7K LOC). The architecture separates terminal rendering concerns from component logic, delegating layout to Yoga (C++ flexbox) and reconciliation to React's upstream reconciler — both proven systems maintained externally.

---

## 1. INK: CUSTOM TERMINAL REACT RENDERER

### 1.1 ink.tsx — 1722 lines

**Main Class: `Ink`**

```typescript
class Ink {
  constructor(options: {
    stdout: NodeJS.WriteStream
    stdin: NodeJS.ReadStream
    stderr: NodeJS.WriteStream
    exitOnCtrlC: boolean
    patchConsole: boolean
    waitUntilExit?: () => Promise<void>
    onFrame?: (event: FrameEvent) => void
  })

  render(element: ReactNode): void
  unmount(): void
  lastFrame(): Frame
}
```

**Architecture: Double Buffering & Frame Model**
- Maintains `frontFrame` and `backFrame` (Screen objects) for differential rendering
- Frame throttling at `FRAME_INTERVAL_MS` (~16ms) with microtask deferral
- Render scheduling uses React's reconciler `resetAfterCommit` hook to queue deferred renders
- Layout computation happens in React's commit phase before layout effects fire

**Key State:**
```typescript
private terminalColumns: number
private terminalRows: number
private selection: SelectionState
private searchHighlightQuery: string
private searchPositions: MatchPosition[]
private hoveredNodes: Set<DOMElement>
private altScreenActive: boolean
private cursorDeclaration: CursorDeclaration | null  // IME caret position
```

**Production Insight — Lifecycle Management:**
- Constructor hooks `signal-exit` for graceful unmount (prevents orphaned TTY mode)
- Registers SIGCONT handler for resume-from-suspend (clears frames to prevent clobbering shell)
- TTY resize handler invalidates layout and triggers full-render via `needsEraseBeforePaint` flag
- Console patching redirects `console.log` to terminal output, synchronized with frame updates

---

### 1.2 reconciler.ts — 512 lines

**React Reconciler Host Config:**

```typescript
createInstance(type, props, ...)
  → dom.createNode(type) with style attachment

appendChildToContainer(container, child)
  → dom.appendChildNode(container, child)
  → triggers markDirty cascade

commitUpdate(instance, updatePayload, type, oldProps, newProps)
  → setStyle, setAttribute, event handler updates
  → marks dirty for render scheduling

resetAfterCommit()
  → calls scheduleRender (microtask → onRender)
```

**Production Insight — Dirty Tracking:**
- Each DOMElement has a `dirty: boolean` flag
- `markDirty(node)` walks up the tree; stops if any ancestor is already dirty (cascade optimization)
- `renderChildren` checks `seenDirtyChild`: if any child was dirty, descendants cannot blit (must full-redraw)
- This prevents one dirty logo from forcing 2800 message re-renders in long sessions

**Study Mapping:** Implement a dirty-flag cascade for any hierarchical rendering system. The key insight: marking dirty upward (not downward) is O(depth), not O(tree size).

---

### 1.3 screen.ts — 1486 lines

**Memory Interning Pattern (CharPool, StylePool, HyperlinkPool):**

```typescript
class CharPool {
  intern(char: string): number
    // ASCII fast-path: direct array lookup
    // Multi-char: Map-based deduplication
    // Returns unique ID reused across frames

  get(index: number): string
    // O(1), defaults to space on miss
}

class StylePool {
  intern(styles: AnsiCode[]): number
    // Encodes bit 0 based on visible-on-space effect
    // Allows renderer to skip invisible spaces with single bitmask

  get(id: number): AnsiCode[]
    // Strips bit-0 flag via >>> 1 to recover styles
}
```

**Production Insight — Bit-Packing:**
Style IDs encode visibility in bit 0: `id = (rawId << 1) | (hasVisibleEffect ? 1 : 0)`.
Renderer skips drawing spaces when `(styleId & 1) === 0` (no bg/underline effect).
Eliminates ANSI codes for invisible spaces, compressing output significantly.

**Screen Structure:**
```typescript
type Screen = {
  width: number
  height: number
  cells: Uint32Array  // packed: styleId | charId | hyperlinkId | CellWidth
}
```

---

### 1.4 render-node-to-output.ts — 1462 lines

**Tree Traversal & Blit Optimization:**

```typescript
function renderNodeToOutput(
  node: DOMElement,
  output: Output,
  scrollTop: number = 0,
): void {
  // Pre-order depth-first traversal
  // 1. Check dirty flag + caching
  // 2. Check visibility (display: none)
  // 3. Apply clip region (overflow: hidden)
  // 4. Text nodes: word-wrap, apply styles
  // 5. Box nodes: blit children via optimized region copy
  // 6. Handle scroll draining (pendingScrollDelta)

  if (node.cached && !hasChildDirty) {
    output.blit(cachedScreen, x, y, w, h)
    return  // skip children entirely
  }
}
```

**Production Insight — Layout Shift Detection:**
`layoutShifted` flag: if any node's Yoga position differs from cache, blit optimization is disabled (forces full-damage redraw). This is how the renderer avoids blitting stale geometry after a window resize.

**Production Insight — Scroll Hints (DECSTBM Hardware Scroll):**
When a ScrollBox's `scrollTop` changes, emits `ScrollHint { top, bottom, delta }`. The log-update layer uses this to emit `CSI r` (DECSTBM) + `CSI n S/T` (SU/SD) — hardware scroll. Saves 90% output bandwidth for pure-scroll frames.

**Production Insight — Adaptive Scroll Drain:**
- Detects terminal via `isXtermJs()` probe at startup
- Native (iTerm2/Ghostty): proportional drain (75% of pending per frame) → log₄ catch-up
- VS Code (xterm.js): smooth drain (fixed 2-3 rows/frame) → constant velocity
- Prevents jank on fast wheel flicks

---

### 1.5 log-update.ts — 773 lines

**Frame Diffing Strategy:**

```typescript
class LogUpdate {
  render(prevFrame: Frame, nextFrame: Frame, altScreen?: boolean): Diff {
    if (!this.options.isTTY) {
      return this.renderFullFrame(nextFrame)
    }

    // 1. Check viewport size change → full erase + redraw
    // 2. Check for DECSTBM scroll opportunity
    //    → emit: CSI top;bot r + CSI n S/T + CSI r
    // 3. Else: diff each cell (Uint32Array comparison)
    //    → emit ANSI codes only for changed cells
  }
}
```

**Study Mapping:** Double buffering + Uint32Array cell diff is a direct pattern to extract. Compare two screen buffers, emit ANSI only for changed positions. For a 200-column × 50-row terminal, Uint32Array diff is ~40K integer comparisons — extremely fast.

---

### 1.6 parse-keypress.ts — 801 lines

**Multi-Protocol Keyboard Parser:**

```typescript
type ParsedKey = {
  name: string         // 'ArrowUp', 'Enter', 'f', etc.
  sequence: string     // raw escape sequence
  ctrl: boolean, meta: boolean, shift: boolean, fn: boolean
  isPasted: boolean    // true if >1 char (pasted content)
}

// Recognized protocols:
// 1. CSI u (Kitty keyboard protocol)
// 2. xterm modifyOtherKeys (Ghostty/tmux/SSH)
// 3. Legacy F-key sequences (xterm/iTerm2)
// 4. Mouse events (SGR format: CSI < btn;x;y M/m)
// 5. Terminal query responses (DA1, DA2, DECRPM, XTVERSION)
```

**Production Insight — Terminal Detection:**
```typescript
stdout.write('\x1b[?u')     // Kitty keyboard: response flags
stdout.write('\x1b[>0q')    // XTVERSION: terminal name/version
stdout.write('\x1b[c')      // DA1: capabilities
```
Parse responses to set capability flags. Enables fallback chains: Kitty → xterm → legacy.

---

### 1.7 dispatcher.ts — 234 lines

**Capture/Bubble Event Dispatch:**

```typescript
export class Dispatcher {
  dispatch(target: DOMElement, event: TerminalEvent): boolean {
    const listeners = collectListeners(target, event)
    // capture phase: root → target (unshift)
    // bubble phase: target → root (push)
    processDispatchQueue(listeners, event)
    return !event.defaultPrevented
  }

  dispatchDiscrete(target, event)    // keyboard, click, focus → React DiscreteEventPriority
  dispatchContinuous(target, event)  // resize, scroll, mousemove → ContinuousEventPriority
}
```

**Study Mapping:** The capture/bubble collector pattern is reusable. Walk the ancestor chain once, build two ordered lists (capture/bubble), execute with stopPropagation short-circuit. Matches browser behavior exactly.

---

### 1.8 selection.ts — 917 lines

**Text Selection Model:**
```typescript
type SelectionState = {
  anchor: Position | null     // mouse-down start
  focus: Position | null      // current end
  selectedRows: Set<number>   // cached row indices for overlay pass
}

function startSelection(state, clickPos)
function updateSelection(state, movePos)
function extendSelection(state, movePos)  // shift+click extend
function getSelectedText(): string        // for copy buffer
```

**Production Insight — Selection Overlay Ordering:**
Selection overlay is applied AFTER full-render, BEFORE screen diff. Text is read from `frontFrame` before front/back swap. Reason: selection overlay mutates screen cells; next frame needs fresh baseline, not the mutated overlay.

---

### 1.9 use-input.ts — 93 lines

**React Integration for Keyboard Input:**

```typescript
function useInput(
  inputHandler: (input: string, key: Key, event: InputEvent) => void,
  options?: { isActive?: boolean }
) {
  // useLayoutEffect (NOT useEffect) → raw mode enabled during commit phase
  useLayoutEffect(() => {
    if (options.isActive !== false) setRawMode(true)
    return () => setRawMode(false)
  }, [options.isActive, setRawMode])

  // Register listener once; useEventCallback keeps closure fresh without re-registering
  const handleData = useEventCallback(...)
  useEffect(() => {
    internal_eventEmitter.on('input', handleData)
    return () => internal_eventEmitter.removeListener('input', handleData)
  }, [internal_eventEmitter, handleData])
}
```

**Production Insight — `useLayoutEffect` vs `useEffect` for Raw Mode:**
`useLayoutEffect` enables raw mode during React's commit phase (synchronous). `useEffect` would defer to the next event loop tick — leaving the terminal in cooked mode briefly (keystrokes echo to screen before handler activates). This is a subtle timing bug that tutorials never cover.

---

## 2. COMPONENT ARCHITECTURE

### 2.1 Directory Structure

```
/src/components/ (389 files, 24K+ LOC)
├── App.tsx                     — top-level provider wrapper
├── REPL.tsx                    — main app screen
├── FullscreenLayout.tsx        (636 lines) — scroll layout manager
├── Messages.tsx                (833 lines) — message list orchestration
├── Message.tsx                 (626 lines) — per-message type router
├── MessageRow.tsx              (382 lines) — per-message container
├── VirtualMessageList.tsx      (1081 lines) — scroll virtualization
├── ScrollKeybindingHandler.tsx (1011 lines) — keyboard navigation
├── Messages/                   — message type renderers
│   ├── AssistantTextMessage.tsx
│   ├── AssistantToolUseMessage.tsx
│   ├── UserTextMessage.tsx
│   ├── AssistantThinkingMessage.tsx
│   └── UserToolResultMessage/
├── PromptInput/                — text input + command palette
├── permissions/                — tool permission UI
├── Settings/                  — preference dialogs
├── agents/                    — subagent management
└── ui/                        — generic controls (Button, TreeSelect, etc.)
```

---

### 2.2 Messages.tsx — 833 lines

**List-Level Orchestration:**
```typescript
// 1. Normalize messages: merge split streaming blocks, resolve tool results
// 2. Build lookups: tool_use_id → tool_result, uuid → index
// 3. Grouping: consecutive tool_use blocks from same agent → collapsed group
// 4. Brief mode filter: show only Brief tool calls + results
// 5. Summary collapse: hook outputs, read/search groups, bash notifications
// 6. Pass to VirtualMessageList for viewport culling
```

**Production Insight — React Compiler Cache Slots:**
`_c(N)` calls throughout Messages.tsx are inserted by the React Compiler. Each slot is a stable closure slot that memoizes a subtree. Re-render of Messages does not cascade to children if inputs haven't changed. Works without `useMemo`/`React.memo` — the compiler handles it.

---

### 2.3 VirtualMessageList.tsx — 1081 lines

**Virtual Scroll Implementation:**
```typescript
export function VirtualMessageList(props: {
  items: MessageType[]
  renderItem: (msg, idx) => ReactNode
  height: number
  estimateItemHeight: (msg) => number
  ref: RefObject<JumpHandle>
}) {
  // Measure actual height during render → cache in Map<uuid, height>
  // Compute cumulative offsets → binary search for viewport intersection
  // Render only viewport + overscan buffer
  // Update ScrollBox.scrollTop when jumping to message
}
```

**Production Insight — Streaming Height Estimation:**
During streaming text append, height estimate becomes stale. `ScrollBox`'s `stickyScroll` flag auto-pins to bottom until next stable render. The system renders messages twice: narrow pass (estimate) then wide pass (measure) to avoid layout thrashing.

**Study Mapping:** Height cache in `Map<id, height>` + cumulative offsets + binary search is the minimal virtual list. For a study project: skip the two-pass rendering, just remeasure when items change. The key is the `stickyScroll` flag — essential for any streaming content list.

---

### 2.4 ScrollKeybindingHandler.tsx — 1011 lines

**Input Bindings (40+ total):**
```typescript
useInput((input: string, key: Key) => {
  if (key.upArrow)        scrollUp()
  if (key.downArrow)      scrollDown()
  if (key.pageUp)         scrollTo(0)
  if (key.pageDown)       scrollToBottom()
  if (key.ctrl && key.f)  openSearch()
  if (key.ctrl && key.k)  openCommandPalette()
  if (key.ctrl && key.o)  toggleTranscriptMode()
  // ...
})
```

**Production Insight — Adaptive Scroll Drain:**
Adaptive drain is configured in this handler based on `isXtermJs()` probed at startup. Native = proportional (75%/frame), VS Code = smooth (2-3 rows/frame). Different math, different UX.

---

### 2.5 Provider Hierarchy (App.tsx)

```typescript
<FpsMetricsProvider getFpsMetrics={getFpsMetrics}>
  <StatsProvider store={stats}>
    <AppStateProvider initialState={initialState} onChangeAppState={...}>
      {/* REPL screen */}
    </AppStateProvider>
  </StatsProvider>
</FpsMetricsProvider>
```

**AppState Shape:**
```typescript
type AppState = {
  messages: Message[]
  selectedMessageIndex: number | null
  inputText: string
  isStreaming: boolean
  tools: Tools
  permissionMode: 'manual' | 'prompt' | 'always-yes'
  settings: UserSettings
  // 20+ more
}
```

**Study Mapping:** Nested providers with context hooks is the correct pattern. Each provider is a memoization boundary — when `AppState` changes, `FpsMetrics` consumers don't re-render. Keep concerns separated at provider level.

---

### 2.6 Streaming Markdown (Markdown.tsx — 235 lines)

```typescript
export function StreamingMarkdown({ content, isStreaming }) {
  const [cached, setCached] = useState<CachedMarkdown | null>(null)

  useEffect(() => {
    const parsed = parseMarkdown(content)   // expensive
    setCached({ content, blocks: parsed, renderedAt: Date.now() })
  }, [content])

  return (
    <>
      {cached?.blocks.map(block => <MarkdownBlock block={block} />)}
      {isStreaming && <Spinner />}
    </>
  )
}
```

**Production Insight — Parser Memoization:**
Parsed blocks are cached. Re-render of parent doesn't re-parse. Streaming text accumulates, but re-parse is debounced — batching 50ms of input before parsing again. Completed blocks use cached AST from previous parse; only new tail is parsed incrementally.

---

## 3. CLI INTEGRATION LAYER

### 3.1 print.ts — 5594 lines (largest file in codebase)

**Main Entry Point for Interactive Sessions:**

```typescript
// Orchestrates in order:
// 1. Tool Pool Assembly
const tools = await assembleToolPool({
  includeBuiltIns: true,
  userDefinedDir: '~/.claude/agents',
  denialRules: config.deniedTools,
})

// 2. Permission Mode State Machine
type PermissionMode = 'manual' | 'prompt' | 'always-yes'
const permissionMode = loadPermissionMode()
setPermissionModeChangedListener((newMode) => {
  applyToolFilter(tools, newMode)
})

// 3. Conversation Loading (resume support)
const messages = await loadConversationForResume(sessionId)
const appState = createInitialAppState(messages)

// 4. Ink Mount
const root = render(<App initialState={appState} {...} />, {
  stdout, stdin, stderr,
  exitOnCtrlC: true,
  patchConsole: true,
})

// 5. Event Loop: drain SDK commands → execute → send response
```

**Production Insight — Command Queuing:**
SDK messages can arrive mid-render. Rather than blocking the UI:
```typescript
onSDKMessage((msg) => {
  if (msg.type === 'user_message') {
    enqueue(msg.command, { priority: 'normal' })
    scheduleRender()  // show "waiting" state
  }
})

while (hasCommandsInQueue()) {
  const cmd = dequeue()
  const result = await executeCommand(cmd)
  sendResponse(result)
}
```
The queue decouples SDK I/O from UI rendering. SDK sends at its own rate; UI renders at its own rate.

---

### 3.2 structuredIO.ts — 859 lines

**SDK Communication Protocol:**

```typescript
export class StructuredIO {
  private readonly pendingRequests = new Map<string, PendingRequest>()

  async sendPermissionRequest(tool: Tool, input: Record<string, unknown>):
    Promise<PermissionResult> {
    // 1. Write control_request as NDJSON to stdout
    // 2. Create Promise, store in pendingRequests[requestId]
    // 3. Await response on stdin (matched by requestId)
    // 4. Resolve/reject promise
  }
}
```

**Production Insight — Deduplication for Reconnect Safety:**
```typescript
private readonly resolvedToolUseIds = new LRUCache(MAX_RESOLVED_TOOL_USE_IDS)

// On duplicate control_response (e.g. from reconnect):
if (this.resolvedToolUseIds.has(toolUseId)) {
  return  // silently drop
}
```

**Permission Decision Cascade:**
```typescript
async function canUseTool(tool, input, context): Promise<PermissionResult> {
  // 1. Deny rules → immediate reject
  // 2. Saved decisions → use stored result
  // 3. Permission hooks (user scripts) → early exit if decisive
  // 4. Interactive prompt (manual mode only) → render PermissionRequest component
  // 5. Default based on mode
}
```

**Production Insight — Hook Execution:**
User hooks are bash/python scripts at `~/.claude/hooks/tool-permission.sh`. They receive `TOOL_NAME` + `INPUT_JSON` on stdin, return via exit code (0=allow, 1=deny, 2=prompt). Executed before rendering UI, so slow network calls don't block the frame.

**Study Mapping:** The permission cascade (rules → saved → hooks → interactive → default) is a clean pattern for any gating mechanism. Each level can short-circuit. Store the reason alongside the decision for audit trails.

---

### 3.3 remoteIO.ts — 255 lines

**Remote Transport:**
```typescript
export class RemoteIO extends StructuredIO {
  private transport: Transport  // WebSocketTransport | SSETransport
  private inputStream: PassThrough

  constructor(streamUrl: string) {
    this.transport = getTransportForUrl(url, headers, sessionId, refreshHeaders)
    this.transport.setOnData((data) => this.inputStream.write(data))
    this.transport.setOnClose(() => this.inputStream.end())

    // CCR v2: Conversation Context Restoration
    if (CLAUDE_CODE_USE_CCR_V2) {
      this.ccrClient = new CCRClient(this.transport, this.url)
      this.restoredWorkerState = this.ccrClient.initialize()
    }
  }
}
```

**Production Insight — Token Refresh on Reconnect:**
```typescript
const refreshHeaders = (): Record<string, string> => {
  const freshToken = getSessionIngressAuthToken()  // re-read on each call
  if (freshToken) h['Authorization'] = `Bearer ${freshToken}`
  return h
}
// Transport calls refreshHeaders() on reconnection — handles token rotation mid-session
```

---

## 4. LAYOUT ENGINE (YOGA INTEGRATION)

### 4.1 dom.ts — 484 lines

**Yoga Node Lifecycle:**
```typescript
export const createNode = (nodeName: ElementNames): DOMElement => {
  const needsYogaNode =
    nodeName !== 'ink-virtual-text' &&   // no layout
    nodeName !== 'ink-link' &&           // inline link
    nodeName !== 'ink-progress'          // progress bar

  const node: DOMElement = {
    nodeName,
    style: {}, attributes: {}, childNodes: [],
    yogaNode: needsYogaNode ? createLayoutNode() : undefined,
  }

  // Register measure functions for intrinsic sizing
  if (nodeName === 'ink-text') {
    node.yogaNode?.setMeasureFunc(measureTextNode.bind(null, node))
  } else if (nodeName === 'ink-raw-ansi') {
    node.yogaNode?.setMeasureFunc(measureRawAnsiNode.bind(null, node))
  }

  return node
}
```

**Measure Function Pattern:**
```typescript
function measureTextNode(node, width, widthMode) {
  // Yoga calls this when it needs intrinsic size of text
  if (widthMode === LayoutMeasureMode.Exactly) {
    const wrapped = wrapText(nodeValue, width)
    return { width, height: wrapped.length }
  }
  if (widthMode === LayoutMeasureMode.AtMost) {
    const measuredWidth = measureText(nodeValue).width
    return { width: Math.min(measuredWidth, width), height: 1 }
  }
  return { width: measureText(nodeValue).width, height: 1 }
}
```

**Production Insight — Width Measurement Caching:**
Text measurement (per-codepoint advance calculation, combining marks) is expensive. Ink caches measurements in `line-width-cache.ts` keyed by (text, styleCode). Saves ~10x on repeated renders of same content.

**Production Insight — Node Pool Reset:**
Yoga nodes (WASM objects) are pooled and reset every 5 minutes to free WASM memory. Unchecked growth of Yoga nodes in long sessions causes steady memory increase. This is the only explicit GC-assist in Ink.

---

## 5. NON-OBVIOUS IMPLEMENTATION DETAILS

### 5.1 IME Cursor Declaration
- Components declare cursor position via `useDeclaredCursor(x, y)` — stored on Ink instance
- On each render, Ink emits `CSI y;x H` (cursor position escape sequence)
- Terminal renders IME preedit inline at that position (CJK input)
- Without this, IME floating window appears at wrong position

### 5.2 Selection Overlay & Frame Swap Ordering
- Selection overlay applied AFTER full-render, BEFORE front/back swap
- Text read from `frontFrame` before swap
- Selection overlay mutates cells; next frame must start from clean baseline (not mutated overlay)
- This ordering is invisible in the code unless you trace the frame lifecycle

### 5.3 Focus Stack Deduplication
- FocusManager maintains focus stack (max 32 entries)
- On node removal, ancestors popped until a still-mounted node found
- Deduplication before push prevents stack growing during rapid Tab cycling
- Edge case: Tab cycling 100 times would push 100 duplicates without dedup

### 5.4 Search Highlight — Scan Once, Overlay Per Frame
- VirtualMessageList scans messages for search hits once, stores `MatchPosition[]` relative to message
- Each frame: apply overlay based on current `scrollTop` offset
- No re-scan feedback loop; navigation is index arithmetic
- Prevents O(text_size) work per frame during search

### 5.5 Hyperlink Padding Inside Envelope
- OSC 8 hyperlinks: `\x1b]8;;URL\x07 text \x1b]8;;\x07`
- Padding around text must be inside the envelope (not outside)
- Matters when a link wraps across lines — padding outside would break the link sequence

### 5.6 `useLayoutEffect` for Raw Mode Timing
- `useInput` uses `useLayoutEffect`, enabling raw mode during React's commit phase
- `useEffect` would defer to next event loop tick → brief cooked mode (keystrokes echo)
- This is a production-quality detail that most tutorials never cover

---

## 6. SUMMARY TABLE

| File | Lines | Core Purpose |
|------|-------|-------------|
| `ink/ink.tsx` | 1722 | Main renderer, frame loop, alt-screen, selection, IME |
| `ink/reconciler.ts` | 512 | React host config, dirty tracking |
| `ink/dom.ts` | 484 | Terminal DOM model, Yoga integration |
| `ink/screen.ts` | 1486 | Screen buffer, CharPool/StylePool/HyperlinkPool |
| `ink/render-node-to-output.ts` | 1462 | Tree traversal, blit optimization, scroll drain |
| `ink/log-update.ts` | 773 | Frame diffing, DECSTBM hardware scroll |
| `ink/output.ts` | 797 | Write operations: clip, blit, write, shift |
| `ink/parse-keypress.ts` | 801 | Keyboard event parser, terminal detection |
| `ink/selection.ts` | 917 | Text selection model, copy buffer |
| `ink/dispatcher.ts` | 234 | Capture/bubble event dispatch |
| `ink/use-input.ts` | 93 | React keyboard hook, raw mode timing |
| `components/Messages.tsx` | 833 | Message list orchestration |
| `components/VirtualMessageList.tsx` | 1081 | Virtual scroll, height cache |
| `components/ScrollKeybindingHandler.tsx` | 1011 | Keyboard nav, adaptive drain |
| `components/FullscreenLayout.tsx` | 636 | Scroll layout manager |
| `components/Message.tsx` | 626 | Message type router |
| `cli/print.ts` | 5594 | Main REPL entry: tool pool, permissions, Ink setup |
| `cli/structuredIO.ts` | 859 | SDK communication, permission cascade |
| `cli/remoteIO.ts` | 255 | Remote transport, token refresh |

---

## 7. PATTERNS TO ADOPT

| Pattern | Source | What to Extract |
|---------|--------|----------------|
| **Dirty-flag cascade** | reconciler.ts | Mark dirty upward (O(depth)); blit clean siblings |
| **Double buffering + Uint32Array diff** | log-update.ts | Compare two screen buffers, emit ANSI only for changes |
| **Bit-packed style pool** | screen.ts | Encode visibility in bit 0; skip invisible cells without branch |
| **Permission decision cascade** | structuredIO.ts | Rules → saved → hooks → interactive → default; attach reason |
| **Height cache + virtual scroll** | VirtualMessageList.tsx | Map<id, height> + cumulative offsets + stickyScroll |
| **Measure function for intrinsic sizing** | dom.ts | Yoga calls back for text size; one pass vs. multiple iterations |
| **useLayoutEffect for raw mode** | use-input.ts | Synchronous mode switch during commit, not next tick |
| **Capture/bubble collector** | dispatcher.ts | Walk ancestor chain once, build two ordered lists |
| **Streaming content state machine** | Messages.tsx | Accumulate blocks, show spinner while incomplete, cache completed |
| **Command queue decoupling** | print.ts | Enqueue SDK messages; UI renders at its own rate |
| **Token refresh on reconnect** | remoteIO.ts | `refreshHeaders` callback re-reads token on each reconnect |
| **Hardware scroll (DECSTBM)** | render-node-to-output.ts | CSI r + CSI S/T for 90% output reduction on pure-scroll frames |

---

## 8. ARCHITECTURAL TAKEAWAYS

1. **Don't reimplement React core.** Ink implements only the host config (`react-reconciler`). React's reconciler, scheduler, and batching come for free — including future improvements.

2. **The dirty bit is the performance budget.** Every optimization flows from the dirty-flag cascade. Without it, 2800 messages redraw on every keypress.

3. **Terminal rendering is a diff problem.** Two screen buffers, cell-level comparison, ANSI only for changes. The rendering layer is essentially a terminal-specific vdom.

4. **Yoga for layout; custom for render.** Yoga (C++ flexbox) handles layout math. Ink handles rendering. Don't mix concerns — layout libraries aren't renderers.

5. **Streaming needs a clock.** StreamingMarkdown debounces parsing. VirtualMessageList uses stickyScroll. ScrollKeybindingHandler uses adaptive drain. Each streaming concern has its own timing strategy.

6. **Permission is a cascade, not a flag.** Rules → saved decisions → hooks → interactive → mode default. Each level short-circuits. Attach reason to every decision for audit trails.

7. **`useLayoutEffect` matters for I/O.** Raw mode, cursor positioning, and any synchronous TTY interaction needs `useLayoutEffect` (commit phase), not `useEffect` (next tick).
