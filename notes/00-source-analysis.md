# Source Analysis: claw-code Rust Port

Source: `/Users/zl190/Developer/personal/claw-code/rust/crates/runtime/src/`

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
