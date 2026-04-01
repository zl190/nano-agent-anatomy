# Reader 3: AI + MCP Integration Layer

Source files analyzed:
- `src/tools/AgentTool/` — 6,782 lines (18 files)
- `src/tools/MCPTool/` — 1,086 lines (4 files)
- `src/tools/WebFetchTool/` — 1,131 lines (5 files)
- `src/tools/WebSearchTool/` — 569 lines (3 files)
- `src/tools/LSPTool/` — 2,005 lines (6 files)
- `src/tools/SkillTool/` — 1,477 lines (4 files)
- `src/services/api/` — 10,477 lines (20 files)
- `src/services/mcp/` — 12,310 lines (22 files)

**Total: ~35,837 lines**

---

## 1. AgentTool (6,782 lines)

### Core files

| File | Lines | Purpose |
|------|-------|---------|
| `AgentTool.tsx` | 1,397 | Entry point, schema gating, routing to sync/async/fork/teammate |
| `runAgent.ts` | 973 | Core agent loop: MCP init, system prompt assembly, query() call |
| `agentToolUtils.ts` | 686 | Tool filtering, async lifecycle, YOLO classifier |
| `loadAgentsDir.ts` | 755 | Parse agent frontmatter, validate schema, load from disk |
| `forkSubagent.ts` | 210 | Fork path: clone conversation context, inject boilerplate |
| `agentMemory.ts` | 177 | Three-scope memory dir lookup (user/project/local) |
| `agentMemorySnapshot.ts` | 197 | Sync memory snapshots across project/user scopes |
| `prompt.ts` | 287 | Generate AgentTool system prompt listing available agents |

### Key functions

**`AgentTool.call()`** — Routes a spawn request through four paths:
1. Multi-agent swarm: `spawnTeammate()` via tmux
2. Fork path (no `subagent_type`, gate enabled): clone parent context
3. Normal agent: find `AgentDefinition`, validate MCP requirements, then sync or async
4. Remote: `teleportToRemote()` for CCR environments

**`runAgent()`** — The actual agent execution engine (async generator):
```
initializeAgentMcpServers()  → connects agent-specific MCP servers
getSystemPrompt()            → builds system prompt for agent type
agentGetAppState()           → overrides permission mode, blocks prompts for async
resolveAgentTools()          → filter tools for agent (async gets subset)
executeSubagentStartHooks()  → runs SubagentStart lifecycle hooks
query()                      → the actual API loop
```

**`buildForkedMessages(directive, assistantMessage)`** — Fork cache optimization:
Constructs a message array where every tool_result block gets an **identical placeholder** (`"Fork started — processing in background"`). Only the per-child directive text block differs. This means all fork siblings share the same prompt cache prefix.

**`initializeAgentMcpServers(agentDefinition, parentClients)`** — Per-agent MCP:
- String ref: looked up from existing memoized pool (shared, not cleaned up)
- Inline `{ name: config }`: newly created, cleaned up on agent exit

**`loadAgentsDir.ts`** — Parses `.md` files with YAML frontmatter. Fields include:
`tools`, `disallowedTools`, `mcpServers`, `permissionMode`, `maxTurns`, `memory`, `effort`, `hooks`, `background`, `isolation`

**`agentMemory.ts`** — Three scopes:
- `user`: `~/.claude/agent-memory/<agentType>/`
- `project`: `.claude/agent-memory/<agentType>/`
- `local`: `.claude/agent-memory-local/<agentType>/` (or mounted remote path)

### Production insights

**Prompt cache sharing for fork children is explicitly engineered.** `buildForkedMessages()` ensures all siblings have byte-identical prefixes. The per-child directive is appended as a final text block after the tool_results — the comment in the code acknowledges this creates a `[tool_result, text]` pattern that could be smooshed but isn't worth the complexity.

**Tool filtering is deeply layered:**
- `ALL_AGENT_DISALLOWED_TOOLS`: blocked for all agents
- `CUSTOM_AGENT_DISALLOWED_TOOLS`: blocked for user-defined agents only
- `ASYNC_AGENT_ALLOWED_TOOLS`: allowlist for background agents (much smaller set)
- Per-agent `tools:` frontmatter: further restricts to named subset
- Per-agent `disallowedTools:` frontmatter: removes specific tools

**Background agents cannot show permission prompts.** `isAsync` toggles `shouldAvoidPermissionPrompts: true`, meaning any tool requiring user approval auto-denies. Exception: `bubble` mode forwards prompts to the parent terminal.

**`omitClaudeMd`** for read-only agents (Explore, Plan) saves ~5-15 Gtok/week. The git status is also stripped from these agents' system context.

**Parent's cliArg permissions are preserved across agent boundaries** (`--allowedTools` SDK flag). Session-level rules are replaced per-agent with explicit `allowedTools` list.

**Agent-specific `hooks:` frontmatter.** When an agent starts, `registerFrontmatterHooks()` registers session-scoped hooks from the agent definition. These survive for the agent's lifetime.

### Mapping

| Pattern | What to adopt |
|---------|--------------|
| Fork cache optimization | Identical placeholder results for shared prefixes |
| Three-scope memory | user/project/local with normalize + MEMORY.md index pattern |
| Tool filtering by async | Different allowed-set for background vs. foreground agents |
| Permission bubble mode | Background agents can still surface prompts to parent |
| `omitClaudeMd` for read agents | Slim subagents that don't need project instructions |

---

## 2. MCPTool (1,086 lines)

### Core files

| File | Lines | Purpose |
|------|-------|---------|
| `MCPTool.ts` | 77 | Stub template — real implementation overridden in `client.ts` |
| `classifyForCollapse.ts` | 604 | Allowlist of search/read tool names for UI collapsing |
| `UI.tsx` | 402 | Renders MCP tool call in terminal |
| `prompt.ts` | 3 | Minimal description |

### Key functions

**`MCPTool`** — A template object. Every real MCP tool is created by `client.ts` via `Object.assign()` against this template. The template provides:
- `isMcp: true` flag
- `checkPermissions()` returning `behavior: 'passthrough'` (permission is handled by channel-level rules)
- `mapToolResultToToolResultBlockParam()` — maps string output to `tool_result` block

**`classifyMcpToolForCollapse(toolName)`** — Allowlist-based heuristic:
- Normalizes camelCase/kebab-case to snake_case
- Matches against hardcoded sets: `SEARCH_TOOLS`, `READ_TOOLS`
- Returns `{ isSearch: boolean, isRead: boolean }`
- Unknown tools → `{ isSearch: false, isRead: false }` (conservative, never collapse)

### Production insight

**MCP tools are late-bound.** `MCPTool.ts` is just a schema template. All of `name`, `description`, `prompt`, `call`, and `userFacingName` are overridden at runtime in `client.ts` for each connected server+tool combination. This means one canonical tool definition spawns N actual tools at connection time.

**UI collapse is per-tool, not per-server.** The tool name allowlist covers 15+ major MCP servers (Slack, GitHub, Linear, Datadog, Sentry, Notion, Gmail, Google Drive, Jira, Confluence, Asana, Filesystem, Memory, Brave, Grafana, PagerDuty). Tools not on the list never collapse — even if they're reads.

### Mapping

| Pattern | What to adopt |
|---------|--------------|
| Template + override pattern | Build one canonical tool def, specialize at connection time |
| Conservative collapse | Never collapse unknown operations |

---

## 3. WebFetchTool (1,131 lines)

### Core files

| File | Lines | Purpose |
|------|-------|---------|
| `WebFetchTool.ts` | 318 | Tool definition, permission checks, redirect handling |
| `utils.ts` | 530 | Fetch pipeline: domain blocklist, HTML→Markdown, LRU cache |
| `preapproved.ts` | 166 | ~150 hardcoded allowed hostnames |
| `prompt.ts` | 46 | Auth warning + description |
| `UI.tsx` | 71 | Progress and result rendering |

### Key functions

**`checkDomainBlocklist(domain)`** — Two-level caching:
1. In-memory hostname-keyed LRU (5 min TTL, 128 entries)
2. Calls `https://api.anthropic.com/api/web/domain_info?domain=<domain>`
- Only caches `allowed` results — blocked/failed re-check next time

**`getURLMarkdownContent(url, abortController)`** — Full fetch pipeline:
1. Validate URL (no auth, no private IPs, length cap)
2. Domain blocklist check (with cache)
3. HTTP fetch via axios (60s timeout, 10MB limit, 10 redirect cap)
4. Same-origin redirect check: only allows `www.` add/remove + path changes
5. Binary content → persist to disk, return path reference
6. HTML → Markdown via turndown (lazy-loaded singleton, ~1.4MB)
7. Markdown → truncate to 100K chars
8. LRU cache result (15 min TTL, 50MB total)

**`applyPromptToMarkdown(markdown, prompt)`** — Calls `queryHaiku` with the content as context and `prompt` as the user question. This is the **two-model pipeline**: fetch → Haiku summarizes → result returned to main model.

**`checkPermissions()`** — Permission is keyed on hostname, not full URL:
- `domain:hostname` is the permission rule content
- Preapproved list bypasses all checks
- Deny/ask/allow rules checked in order

### Production insights

**WebFetch uses a secondary model (Haiku) to summarize content.** The tool doesn't return raw HTML or even raw Markdown to the main model — it runs a Haiku query over the fetched content with the user-supplied `prompt`, then returns the result. This is a two-model pipeline where Haiku acts as a content extractor/summarizer.

**The domain blocklist exists to prevent prompt injection.** When `can_fetch: false` is returned by Anthropic's domain API, the tool errors with `DomainBlockedError`. This is a server-side policy mechanism.

**Redirect safety is hostname-based.** Only `www.` normalization redirects are allowed automatically. Cross-domain redirects return a structured response asking the model to retry with the new URL — it doesn't auto-follow. This prevents open redirect exploitation.

**Preapproved hosts bypass the domain blocklist API call entirely** — not just permission prompts. This is a performance optimization (no network round-trip) with a security annotation: preapproved is only for GET, and sandbox network restrictions still require explicit rules.

### Mapping

| Pattern | What to adopt |
|---------|--------------|
| Two-model pipeline | Use small model to summarize large inputs before passing to main model |
| Hostname-keyed permissions | Match at structural level, not URL level |
| Conservative redirect policy | Only allow same-origin redirects; surface cross-domain to caller |

---

## 4. WebSearchTool (569 lines)

### Core files

| File | Lines | Purpose |
|------|-------|---------|
| `WebSearchTool.ts` | 435 | Tool definition, Anthropic web search API wrapper |
| `UI.tsx` | 100 | Progress/result rendering |
| `prompt.ts` | 34 | Search prompt |

### Key functions

**`makeToolSchema(input)`** — Builds `BetaWebSearchTool20250305` schema for API:
```ts
{ type: 'web_search_20250305', name: 'web_search',
  allowed_domains, blocked_domains, max_uses: 8 }
```

**`WebSearchTool.call()`** — Calls `queryModelWithStreaming()` with:
- The search query as user message
- `web_search` as an API-side server tool
- Collects streaming blocks: `server_tool_use`, `web_search_tool_result`, `text`, `citation`
- Returns structured result: `{ query, results: (SearchResult | string)[], durationSeconds }`

**`isEnabled()`** — Provider-gated:
- `firstParty`: always enabled
- `vertex`: only Claude 4.0+ models
- `foundry`: always enabled
- `bedrock`: disabled

### Production insight

**WebSearch is a server-side tool, not a client-side fetch.** The model sends a `web_search` block in its response, the server executes the search, returns `web_search_tool_result` in the next streaming chunk. The client-side tool wraps this server-side capability — it's not making HTTP requests itself, just triggering the API's built-in search. `max_uses: 8` is hardcoded.

**The result parser must handle interleaved streaming blocks.** Text, search tool use, and search results arrive interleaved. The parser tracks `inText` state and accumulates text blocks between search results.

### Mapping

| Pattern | What to adopt |
|---------|--------------|
| Server-side tool wrapper | Wrap API-native capabilities in the tool interface |
| Block stream parsing | State machine to interleave text + structured results |

---

## 5. LSPTool (2,005 lines)

### Core files

| File | Lines | Purpose |
|------|-------|---------|
| `LSPTool.ts` | 860 | Tool definition + all 9 LSP operations |
| `formatters.ts` | 592 | Format LSP protocol responses to human-readable strings |
| `schemas.ts` | 215 | Discriminated union input schema per operation |
| `symbolContext.ts` | 90 | Extract symbol context from LSP hover/definition results |
| `UI.tsx` | 227 | Result rendering |
| `prompt.ts` | 21 | Description |

### Key functions

**`LSPTool.call(input)`** — Routes to one of 9 operations:
- `goToDefinition` → `goToDefinition()` → format with `formatGoToDefinitionResult()`
- `findReferences` → `findReferences()` → `formatFindReferencesResult()`
- `hover` → `hover()` → `formatHoverResult()`
- `documentSymbol` → `documentSymbol()` → `formatDocumentSymbolResult()`
- `workspaceSymbol` → `workspaceSymbol()` → `formatWorkspaceSymbolResult()`
- `goToImplementation`, `prepareCallHierarchy`, `incomingCalls`, `outgoingCalls`

**`isEnabled()`** — Returns `isLspConnected()`. Tool is **not present in tool list** when no LSP server connected — it disappears from the model's view entirely.

**`shouldDeferLspTool(tool)`** (in `claude.ts`) — When LSP init is `pending`, the tool gets `defer_loading: true` in the API call. This tells the model the tool exists but isn't ready yet; the model can discover it via ToolSearch once init completes.

**`validateInput()`** — Validates against discriminated union schema first (better error messages), then checks file existence and that it's a regular file. SECURITY: skips UNC path `\\` validation to prevent NTLM credential leaks.

### Production insight

**LSP tool has two visibility states before disappearing.** When LSP is:
- `connected`: fully present in tool list
- `pending` (still initializing): present with `defer_loading: true`
- `not-started` / `failed`: absent from tool list entirely

This prevents the model from attempting LSP operations before the server is ready, without completely hiding the tool during the startup window.

**Each LSP operation gets its own result formatter.** `formatters.ts` (592 lines) transforms raw LSP protocol responses — `Location[]`, `DocumentSymbol[]`, `CallHierarchyItem[]` etc. — into strings the model can read. This is non-trivial: location arrays need file path resolution and line context, call hierarchies need tree rendering.

### Mapping

| Pattern | What to adopt |
|---------|--------------|
| Conditional tool presence | Remove tool from list when capability not available |
| Deferred loading during init | Present tool but mark `defer_loading` during startup |
| Result formatter layer | Separate protocol response → model-readable string |

---

## 6. SkillTool (1,477 lines)

### Core files

| File | Lines | Purpose |
|------|-------|---------|
| `SkillTool.ts` | 1,108 | Tool definition, skill discovery, fork execution |
| `prompt.ts` | 241 | Describe available skills to model |
| `UI.tsx` | 127 | Progress/result rendering |
| `constants.ts` | 1 | SKILL_TOOL_NAME |

### Key functions

**`getAllCommands(context)`** — Merges local commands with MCP-sourced skills (filtered to `loadedFrom === 'mcp'`), deduped by name.

**`executeForkedSkill(command, ...)`** — Runs a skill in a forked subagent:
1. `prepareForkedCommandContext()` → builds system prompt from skill frontmatter + args
2. `runAgent()` with `isAsync: false` — synchronous, shares terminal
3. Collects messages, reports progress via `onProgress`
4. `extractResultText()` — gets last assistant message text

**`SkillTool.call()`** — Full pipeline:
1. Resolve skill name (handle `/<name>` format, fuzzy match)
2. Check permissions (allow/deny rules keyed on command name)
3. Execute: either `executeForkedSkill()` or direct message injection
4. `recordSkillUsage()` for analytics + `addInvokedSkill()` for session state

**Permission rules** are keyed on `command:<name>` so skills can be individually allowed/denied in settings.

### Production insight

**Skills are agents in disguise.** `executeForkedSkill()` calls `runAgent()` directly — a skill is just an agent whose definition comes from a markdown file with frontmatter, loaded via `getCommands()` rather than `loadAgentsDir()`. The distinction is mostly in how they're discovered and invoked (slash command vs. Agent tool).

**MCP can serve skills.** Commands with `loadedFrom === 'mcp'` are MCP prompts that have been decorated as skills. The SkillTool treats them identically to local `.md` skills. This allows external MCP servers to dynamically inject skills into the skill list.

**Skill invocation is tracked for feature discovery.** `addInvokedSkill()` records which skills fire in this session, feeding the suggestion engine that learns user patterns.

### Mapping

| Pattern | What to adopt |
|---------|--------------|
| Skills as agents | Route skill execution through the same runAgent() machinery |
| MCP-sourced skills | Any prompt-capable MCP server can inject skills |
| Invocation tracking | Record what skills fire for session-level learning |

---

## 7. services/api/ (10,477 lines)

### Core files

| File | Lines | Purpose |
|------|-------|---------|
| `claude.ts` | 3,419 | queryModel generator, prompt caching, tool schema assembly, retry |
| `errors.ts` | 1,207 | Error classification and structured error messages |
| `withRetry.ts` | 822 | Retry strategy: 529/429, OAuth 401, model fallback |
| `logging.ts` | 788 | API request/response logging, usage tracking |
| `filesApi.ts` | 748 | Files API for large tool results |
| `promptCacheBreakDetection.ts` | 727 | Detect when prompt cache breaks unexpectedly |
| `sessionIngress.ts` | 514 | Remote session authentication |
| `grove.ts` | 357 | Anthropic-internal API routes |
| `client.ts` | 389 | Anthropic SDK client factory |

### Key functions

**`queryModel(messages, systemPrompt, thinkingConfig, tools, signal, options)`** — The core API generator. Key behaviors:

1. **Off-switch**: checks GrowthBook `tengu-off-switch` before any Opus calls
2. **Tool search gate**: decides whether to use deferred tool loading
3. **Dynamic tool filtering**: only include discovered deferred tools
4. **Prompt cache placement**: `cache_control` on last message, system prompt segments, and tool block
5. **Global vs. per-user cache**: MCP tools prevent global cache (user-specific → can't share)
6. **Streaming + non-streaming fallback**: tries streaming first; 529 after 3 consecutive → non-streaming retry
7. **Context management**: sends `context_management` beta header for auto-compaction
8. **Deferred tool discovery**: parses `tool_reference` blocks to expand the tool list

**`getCacheControl()`** — Cache control object with optional 1h TTL:
```ts
{ type: 'ephemeral', ttl?: '1h', scope?: 'global' }
```
1h TTL gated on: user eligibility (subscriber + no overage) + GrowthBook allowlist by `querySource`. Latched in bootstrap state for session stability (no mid-session flips).

**`withRetry(getClient, operation, options)`** — AsyncGenerator retry loop:
- 10 retries max (default)
- 3 consecutive 529s → non-streaming fallback
- 401 → force OAuth token refresh, get fresh client
- 403 "token revoked" → same path
- ECONNRESET/EPIPE → disable keep-alive, reconnect
- Bedrock/Vertex auth errors → clear credentials cache
- Foreground query sources only retry 529 (background tasks bail immediately)

**`should1hCacheTTL(querySource)`** — The 1h cache TTL decision:
- Bedrock + `ENABLE_PROMPT_CACHING_1H_BEDROCK` env → always
- `ant` user_type → always
- Claude.ai subscriber, not overaging → check GrowthBook allowlist by querySource pattern

**`configureEffortParams()`** — Maps effort values to API output_config:
- String effort (`low`/`medium`/`high`) → `output_config.effort`
- Numeric override → `anthropic_internal.effort_override` (ant-only)

### Production insights

**MCP tools prevent global prompt cache.** The comment in `queryModel`: "MCP tools are per-user → dynamic tool section → can't globally cache." When an MCP tool is present and not deferred, the cache scope stays `ephemeral` (per-user) rather than `global` (shared across users for same system prompt).

**Prompt cache stability is obsessive.** TTL is latched in bootstrap state so a mid-session GrowthBook update doesn't flip the TTL and bust a 20K-token cache hit. Tool schema building order is deterministic. The off-switch check is skipped for non-Opus to avoid the GrowthBook await.

**529 retry is query-source-aware.** Background tasks (summaries, titles, classifiers) bail on 529 immediately — each retry is "3-10× gateway amplification during a capacity cascade." Only foreground sources (main thread, subagents, SDK) retry.

**The streaming fallback path is engineered.** If streaming 529s 3 times, it falls back to non-streaming with `initialConsecutive529Errors: 3` pre-seeded so the non-streaming retry counter starts from where the streaming counter left off.

### Mapping

| Pattern | What to adopt |
|---------|--------------|
| querySource-aware retry | Different retry strategies for foreground vs. background |
| Latched cache state | Freeze decisions at session start, don't re-evaluate mid-session |
| 1h TTL via subscriber eligibility | Gate expensive features on subscription tier |
| Non-streaming fallback | When streaming fails, retry with non-streaming before giving up |

---

## 8. services/mcp/ (12,310 lines)

### Core files

| File | Lines | Purpose |
|------|-------|---------|
| `client.ts` | 3,348 | Connect, fetch tools, call tools, reconnect, session expiry |
| `auth.ts` | 2,465 | OAuth 2.0 flow, token storage, ClaudeAuthProvider |
| `config.ts` | 1,578 | Parse settings, merge configs (global/project/managed), scope tagging |
| `useManageMCPConnections.ts` | 1,141 | React hook: connection lifecycle, reconnect, elicitation handler |
| `xaa.ts` | 511 | XAA (enterprise auth) integration |
| `xaaIdpLogin.ts` | 487 | XAA IdP SAML/OIDC login |
| `channelPermissions.ts` | 240 | Per-channel tool permission rules |
| `channelNotification.ts` | 316 | Notification routing for MCP channels |
| `types.ts` | 258 | MCPServerConnection union type, config types |

### Key functions

**`connectToServer(name, serverRef)` — memoized** — Transport selection:
- `stdio`: `StdioClientTransport` (spawns subprocess)
- `sse`: `SSEClientTransport` + ClaudeAuthProvider + timeout wrapper
- `http`: `StreamableHTTPClientTransport` + ClaudeAuthProvider + timeout wrapper
- `ws` / `ws-ide`: `WebSocketTransport` (custom)
- `claudeai-proxy`: `StreamableHTTPClientTransport` + OAuth bearer
- `sdk`: error — handled in `print.ts`
- Chrome MCP / Computer Use: **in-process** via `InProcessTransport`

Connection returns `MCPServerConnection`:
```ts
type MCPServerConnection =
  | { type: 'connected'; name; client; ... }
  | { type: 'failed'; name; error; ... }
  | { type: 'needs-auth'; name; config; ... }
  | { type: 'pending'; name; ... }
  | { type: 'disabled'; ... }
```

**`wrapFetchWithTimeout(baseFetch)`** — Per-request 60s timeout using `setTimeout` (not `AbortSignal.timeout`):
- Reason: `AbortSignal.timeout()`'s internal timer is only released on GC in Bun — ~2.4KB of native memory lingers for 60s per request
- GET requests excluded (SSE streams are long-lived)
- Normalizes `Accept: application/json, text/event-stream` header on POST (MCP Streamable HTTP spec)

**`createClaudeAiProxyFetch(innerFetch)`** — OAuth retry with token change detection:
1. Check+refresh token, attach Bearer header
2. If 401: call `handleOAuth401Error(sentToken)` — only retries if token actually changed
3. Guards against ELOCKED contention: check if another process refreshed underneath

**Connection drop detection** — `client.onerror` is overridden to:
- Count consecutive terminal errors (ECONNRESET, ETIMEDOUT, EPIPE, etc.)
- After `MAX_ERRORS_BEFORE_RECONNECT = 3`: trigger `closeTransportAndRejectPending()`
- `client.close()` → rejects all pending `callTool()` promises via SDK internal
- Clear memoize cache → next `connectToServer()` call reconnects fresh

**MCP session expiry** — HTTP 404 + JSON-RPC code `-32001` = session expired:
```ts
isMcpSessionExpiredError(error): error.code === 404 &&
  (error.message.includes('"code":-32001') || ...)
```
Triggers `closeTransportAndRejectPending('session expired')` → auto-reconnects on next call.

**Tool call** (in `client.ts`, override of MCPTool.call) — Full pipeline:
1. Auth cache check (15 min TTL, disk-persisted)
2. `client.callTool()` with ~27.8hr timeout
3. Handle `isError: true` result
4. Truncate oversized content (2048 char description cap, content size limits)
5. Process media: images resize+downsample, binary blobs persist to disk
6. Session expiry retry: on McpSessionExpiredError, get fresh client + retry once

### Production insights

**`connectToServer` is memoized on `${name}-${JSON.stringify(config)}`** — All agents sharing the same MCP server get the same connection object. The memoize cache is cleared on `client.onclose` so reconnection creates a fresh entry.

**Auth cache is a disk-persisted JSON file** (`mcp-needs-auth-cache.json`). Multiple MCP connections batching in parallel read this file — the promise-based singleton (`authCachePromise`) prevents N concurrent reads. Write chain is serialized via `writeChain` promise to prevent read-modify-write races.

**In-process servers avoid subprocess overhead.** Chrome MCP and Computer Use MCP run inside the same Bun process via `InProcessTransport` (linked transport pair), avoiding ~325MB subprocess spawning. The server gets `createLinkedTransportPair()` → one transport for client, one for server, connected in-memory.

**Stdio cleanup is SIGINT → SIGTERM with 100ms escalation window.** Total cleanup budget: 600ms. Polling `process.kill(pid, 0)` every 50ms to detect clean exit. Docker containers need explicit signals; StdioClientTransport's `close()` only sends abort.

**Tool descriptions are capped at 2048 chars.** OpenAPI-generated servers dump 15-60KB of endpoint docs; the cap prevents token waste without losing intent.

### Mapping

| Pattern | What to adopt |
|---------|--------------|
| Discriminated union for connection state | Track connected/failed/pending/needs-auth separately |
| Per-request timeout via setTimeout | Avoid AbortSignal.timeout memory leak in Bun |
| Memoized connections with clear-on-close | Share connections, auto-reconnect on cache clear |
| Disk-persisted auth cache | Cross-session memory for "this server needs auth" |
| In-process transport | Same-process servers for latency-critical or large-binary integrations |

---

## Cross-cutting patterns

### The layered permission model

Every tool goes through multiple permission layers before executing:

```
1. Tool-level: checkPermissions() → allow/deny/ask/passthrough
2. Permission rules: getRuleByContentsForTool() → session/project/user rules
3. Agent-level: allowedTools list replaces session rules
4. Async flag: shouldAvoidPermissionPrompts → auto-deny if can't show UI
5. YOLO classifier: classifyYoloAction() → AI decides safety
```

### The prompt cache budget allocation

The system treats prompt cache as a budget to be preserved:
- TTL latched at session start (no mid-session flips)
- MCP tools detected and scope downgraded to per-user when present
- Tool schema building order is deterministic
- Fork children share byte-identical prefixes
- Context normalization strips tool-search fields from non-supporting models

### The agent spawn hierarchy

```
User → main Claude loop
  └─ AgentTool.call()
       ├─ spawnTeammate() → tmux process (fully independent)
       ├─ runAgent() sync → shares parent abort controller
       ├─ runAgent() async → new AbortController (independent)
       └─ Fork path → clone context + unique directive
            └─ runAgent() async with useExactTools=true
```

Background agents:
- New AbortController (unlinked from parent)
- Auto-deny permission prompts (except `bubble` mode)
- Subset of allowed tools (ASYNC_AGENT_ALLOWED_TOOLS)
- Can be killed via task ID

---

## What tutorials don't teach

1. **Prompt cache is an active engineering concern, not a side effect.** Every schema decision — tool order, message structure, fork placeholder text, TTL latching — is made with cache hit rate in mind.

2. **Agent tool filtering is bidirectional.** It's not just "what can this agent do" but "what the parent can't let this agent do." Session rules are replaced (not merged) when spawning agents, preserving only the SDK-level (`cliArg`) permissions.

3. **MCP connections are resilient by design.** Connection drop → count errors → force close → reject pending callTool() → clear memo cache → next call reconnects. No tool call ever hangs indefinitely; the SDK's design bug (onerror without onclose) is explicitly worked around.

4. **WebSearch is not HTTP.** It's a server-side capability wrapped in the client tool interface. The client triggers it, the server executes it. The client just parses the result stream.

5. **Skills are agents.** The SkillTool calls `runAgent()` — skills and subagents use the same execution engine. The difference is discovery (slash commands vs. Agent tool) and lifecycle (sync in-session vs. async background).

6. **The 2048-char description cap is a token protection mechanism.** Without it, one badly-behaved MCP server can silently eat 15-60K tokens per request just in tool schema.

7. **Fork children have a structured output contract.** `buildChildMessage()` injects a system message demanding: start with "Scope:", no preamble, under 500 words, commit changes before reporting. This is enforced through prompt, not code — the fork pattern is disciplined via the injected boilerplate.
