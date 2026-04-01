# Source Analysis: claw-code Rust Port

Source: `claw-code/rust/crates/runtime/src/`

## 14 Patterns: Tutorial vs Production

| # | Pattern | Tutorial | Production |
|---|---------|----------|------------|
| 1 | Iteration limit | while True until no tool call | max_iterations=16, RuntimeError on exceed |
| 2 | Deny → tool_result | Permission deny = skip tool | Deny reason as is_error=true tool_result, LLM perceives rejection |
| 3 | Compaction without LLM | LLM generates summary (costly) | Deterministic rules: stats + keywords + path scan |
| 4 | Compaction as System role | Insert user-role summary | System role message, preserves user/assistant alternation |
| 5 | Suppress follow-up questions | No concept | Post-compaction flag: "Continue directly, do not recap" |
| 6 | Default highest permission | Unknown tool = allow | Unknown tool = DangerFullAccess required (fail-secure) |
| 7 | Headless via Option<prompter> | Separate headless flag | None = auto-deny tools needing prompt |
| 8 | Usage from session restore | Cost resets on restore | UsageTracker::from_session() rebuilds cumulative cost |
| 9 | 4D token counting | input + output | + cache_creation + cache_read (reflects actual bill) |
| 10 | System prompt dynamic boundary | No static/dynamic split | SYSTEM_PROMPT_DYNAMIC_BOUNDARY constant, cache only static part |
| 11 | CLAUDE.md dedup | Concatenate all | Content hash dedup, prevents monorepo duplication |
| 12 | Instruction file char budget | Inject everything | 4000 chars/file, 12000 total, truncate with [truncated] |
| 13 | Compaction dual trigger | Check token count only | message_count > N AND tokens >= budget, both must be true |
| 14 | Deny reason with full context | "Permission denied" | "tool 'bash' requires approval to escalate from workspace-write to danger-full-access" |

## Key Files

- `conversation.rs` (584L) — ConversationRuntime<C,T> with trait-based API client + tool executor
- `compact.rs` (485L) — Deterministic compaction: summarize_messages(), infer_pending_work(), extract_file_candidates()
- `permissions.rs` (232L) — PermissionMode ordered enum, PermissionPolicy with BTreeMap, PermissionPrompter trait
- `usage.rs` — 4D token tracking, session restore, model-based pricing
- `prompt.rs` — CLAUDE.md ancestor traversal, hash dedup, char budgets, dynamic boundary
- `session.rs` — Versioned sessions, is_error bool on ContentBlock, custom JSON serialization

## Priority Improvements for nano-agent-anatomy

1. **loop.py**: Add max_iterations=16; deny writes is_error=true tool_result back to messages
2. **context.py**: Replace LLM summary with deterministic rules; use System role; add suppress_follow_up_questions
3. **New permissions.py**: PermissionPolicy class, PermissionMode enum, default DangerFullAccess, deny reason to LLM

---

# Source Analysis: claw-code Full (Python + Rust + TS Reference)

Source: `claw-code/` (Python clean-room rewrite + Rust port)
- Python clean-room rewrite: `src/` (~37 .py files, 2138 lines)
- Rust port: `rust/` (~20,000 lines)
- TS reference data: `src/reference_data/` (1902 .ts file paths, 207 commands, 184 tools)

Original TS deleted by author. Three layers combined = high-fidelity architecture reconstruction.

## Merged Pattern Table: Tutorial vs Production (17 unique)

| # | Pattern | Tutorial | Production | Source |
|---|---------|----------|------------|--------|
| 1 | **Iteration limit** | while True | max_iterations=16, RuntimeError | conversation.rs |
| 2 | **Deny → is_error tool_result** | Skip tool | LLM perceives rejection, can recover | conversation.rs |
| 3 | **Compaction without LLM** | LLM summary ($$$) | Deterministic: stats + keywords + paths | compact.rs |
| 4 | **Summary as System role** | User role (breaks alternation) | System role message | compact.rs |
| 5 | **Suppress follow-up questions** | No concept | "do not acknowledge, do not recap" | compact.rs |
| 6 | **Default highest permission** | Unknown = allow | Unknown = DangerFullAccess | permissions.rs |
| 7 | **Headless = Option\<prompter\>** | Separate flag | None = auto-deny | permissions.rs |
| 8 | **Usage from session restore** | Cost resets | from_session() rebuilds cumulative | usage.rs |
| 9 | **4D token counting** | input + output | + cache_creation + cache_read | usage.rs |
| 10 | **System prompt dynamic boundary** | No split | DYNAMIC_BOUNDARY: cache only static part | prompt.rs |
| 11 | **CLAUDE.md dedup** | Concatenate | Content hash dedup | prompt.rs |
| 12 | **Instruction file char budget** | Inject all | 4000/file, 12000 total, [truncated] | prompt.rs |
| 13 | **Compaction dual trigger** | Token only | message_count > N AND tokens >= budget | compact.rs |
| 14 | **Deny reason full context** | "Permission denied" | "tool X requires Y but mode is Z" | permissions.rs |
| 15 | **Agent tool = DangerFullAccess** | Not discussed | Multi-agent disabled in default mode | tools/lib.rs |
| 16 | **agentMemorySnapshot** | Return value only | Subagents share state via memory snapshot | AgentTool/ |
| 17 | **Cron, not daemon** | Long-running process | ScheduleCronTool (Create/Delete/List) | tools snapshot |

## Layer Architecture (from TS reference data)

### Layer 1: Tool Loop
- `QueryEngine.ts` (~46K lines) → Python `query_engine.py` (193L) → Rust `conversation.rs` (584L)
- ConversationRuntime<C,T>: trait-based API client + tool executor (DI)
- Loop terminates on: no pending tool_use blocks (not stop_reason)

### Layer 2: Memory
- TWO subsystems: `memdir/` (persistent files, cross-session) vs `SessionMemory/` (runtime summary, within-session)
- memdir: 8 TS files including memoryAge, memoryScan, findRelevantMemories, teamMemPaths
- Instruction file discovery: cwd → ancestors, check CLAUDE.md variants, hash dedup
- Team-shared memory paths exist (teamMemPaths.ts, teamMemPrompts.ts)

### Layer 3: Context Compression
- compact.rs (485L): pure function, no side effects
- Token estimate: len/4+1 (intentionally underestimates → compact triggers late)
- Summary: XML <summary> block with scope, tools, recent requests, pending work, key files (max 8), timeline
- Continuation message strips <analysis> blocks (internal analysis hidden from user)

### Layer 4: Coordinator
- coordinatorMode.ts = lightweight mode flag (1 file), not a system
- AgentTool: fork/run/resume lifecycle, 5 built-in agent types
- Built-in agents: explore, general-purpose, plan, verification, claude-code-guide
- Separate permission handlers: coordinatorHandler vs swarmWorkerHandler
- agentMemorySnapshot: cross-agent state sharing beyond return values

### Layer 5: Remote / Daemon
- 6 run modes: local / remote / ssh / teleport / direct-connect / deep-link
- Remote: CLAUDE_CODE_REMOTE env var + WebSocket + permission bridge
- Background: ScheduleCronTool (Create/Delete/List) — cron, not daemon process
- Bootstrap: 7 stages, prefetch → trust gate → deferred init → mode routing → query loop
- Enterprise: upstream proxy, CA bundle replacement, token path at /run/ccr/session_token

## Surface Area
- 207 commands, 184 tools, 1902 TS files
- This refutes "CC is just a wrapper" — it's a full platform

## Priority Improvements for nano-agent-anatomy

Already done (this session):
- [x] loop.py: max_iterations=16, permission check, deny→is_error
- [x] context.py: deterministic compaction, suppress follow-up, dual trigger
- [x] permissions.py: PermissionMode enum, fail-secure default

Production patterns not yet rebuilt in nano-agent-anatomy:
- Memory: split into memdir (persistent) vs session memory (runtime)
- Memory: instruction file discovery (ancestor traversal + hash dedup)
- Memory: age-based pruning (memoryAge pattern)
- Coordinator: agent fork/resume lifecycle
- Coordinator: separate coordinator vs worker permissions
- Context: key file extraction, pending work inference
- Usage: 4D token counting (cache_creation + cache_read)
- System prompt: DYNAMIC_BOUNDARY for prompt cache optimization
