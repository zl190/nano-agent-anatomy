# Source Reading: commands/, skills/, plugins/, utils/bash/specs/

Reader: session 3, assigned group 6.
Codebase: Claude Code (TypeScript, ~513K lines).
Files read: ~60 of ~180 total in scope. Focus on architecturally important files.

---

## 1. commands/ — Structure Overview

**Total lines:** ~26,400 TS/TSX across ~150 files
**Pattern:** Every command is a directory (`command-name/`) with `index.ts` (re-export barrel) + main implementation file.

### Command types (from usage)

| Type | Description | Example |
|------|-------------|---------|
| `LocalJSXCommand` | Pure React UI, no model call | `/plan`, `/config`, `/theme` |
| `LocalCommand` | Returns text, no model call | `/context`, `/compact`, `/version` |
| `PromptCommand` | Returns prompt content → model | `/simplify`, all skills |

### Architecturally important commands

#### `/compact` (compact/compact.ts — 287 lines)

Three-path compaction decision tree, executed in order:

```
1. trySessionMemoryCompaction()   — cheap, uses pre-computed summary
2. isReactiveOnlyMode()           — feature flag REACTIVE_COMPACT
3. compactConversation()          — classic: summarize → replace
```

**Production insight:** Before calling the LLM, the compact command strips UI-only "snipped" messages (`getMessagesAfterCompactBoundary`). The REPL keeps them for scrollback, but the model should never see intentionally removed content. This is the gap between "what the UI shows" and "what gets summarized."

**Reactive compaction** (`compactViaReactive`) runs hooks and cache-param builds **concurrently** via `Promise.all`. The comment is explicit: hook spawns subprocesses, cache-params walks all tools — neither depends on the other. Concrete pattern.

#### `/plan` (plan/plan.tsx — 121 lines)

`/plan` is a **mode toggle**, not a wizard. It calls `applyPermissionUpdate({ type: 'setMode', mode: 'plan' })` on the `AppState.toolPermissionContext`. If already in plan mode, it shows the current plan file and optionally opens it in an editor.

**Production insight:** Plan mode is a permission context mutation, not a conversation branch. The plan file lives on disk (`getPlanFilePath()`), readable by all tools. The command just flips a flag in `toolPermissionContext.mode`.

#### `/init` (init.ts — 256 lines)

New `/init` (behind `feature('NEW_INIT')`) is a 7-phase interview-driven onboarding flow:

```
Phase 1: AskUserQuestion — what to create (CLAUDE.md, skills, hooks)
Phase 2: launch subagent to survey codebase
Phase 3: gap-fill interview for what code can't reveal
Phase 4: write CLAUDE.md
Phase 5: write CLAUDE.local.md (personal, gitignored)
Phase 6: create skills
Phase 7: set up hooks
```

**Production insight:** Phase 2 explicitly launches a subagent to avoid polluting the main context with large file reads. The gap-fill interview (Phase 3) is filtered by Phase 1's choices — if user said "no hooks", every hook suggestion is downgraded to a skill or note. The pipeline enforces user-stated scope as a hard filter.

The proposal is shown inside `AskUserQuestion`'s `preview` field (markdown side-panel), not as a separate text message. Reason stated in comments: "the dialog overlays your output, so preceding text is hidden."

#### `createMovedToPluginCommand.ts` (65 lines)

Migration shim for commands being moved to the marketplace. Checks `process.env.USER_TYPE === 'ant'`:
- Internal (ant): tells the user to `claude plugin install <name>@claude-code-marketplace`
- External: runs `getPromptWhileMarketplaceIsPrivate()` fallback

**Production insight:** This is how you migrate a built-in command to a plugin without breaking external users during the transition period. The command name stays stable; behavior diverges by user type.

#### `/context` (context-noninteractive.ts — partial)

`collectContextData()` mirrors the exact pre-API transforms: compact boundary → context collapse → microcompact. This ensures the token count the user sees (`/context`) matches what the model actually receives. Used by both the slash command and the SDK `get_context_usage` control request.

#### `/insights` (insights.ts — 3,200 lines)

Contains `deduplicateSessionBranches()` (line 812), `detectMultiClauding()` (line 1062), and `buildExportData()` (line 2679). This is the usage analytics/session visualization command. Not read in full but confirms the pattern: large commands get their own file.

---

## 2. skills/ — The Skill System

### Core files

| File | Lines | Role |
|------|-------|------|
| `loadSkillsDir.ts` | 1,086 | Main loader: file-based skills, frontmatter parser, command builder |
| `bundledSkills.ts` | 220 | Registry for compiled-in skills + security for file extraction |
| `mcpSkillBuilders.ts` | 44 | Dependency-cycle breaker for MCP skill loading |
| `bundled/index.ts` | 79 | Startup init: registers all bundled skills |

### BundledSkillDefinition (bundledSkills.ts)

```typescript
type BundledSkillDefinition = {
  name: string
  description: string
  aliases?: string[]
  whenToUse?: string           // triggers auto-invocation
  argumentHint?: string
  allowedTools?: string[]      // tool permission scope
  model?: string               // model override
  disableModelInvocation?: boolean
  userInvocable?: boolean      // show in /skills list
  isEnabled?: () => boolean    // per-invocation toggle
  hooks?: HooksSettings
  context?: 'inline' | 'fork' // fork = sub-agent with own context
  agent?: string
  files?: Record<string, string>  // reference files extracted to disk
  getPromptForCommand: (args, ctx) => Promise<ContentBlockParam[]>
}
```

**Production insight — `files` field:** If a skill needs reference files (docs, schemas), include them as `files: { 'subdir/file.md': content }`. On first invocation, they're extracted to a per-skill directory with hardened security:
- Path traversal guard: rejects `..` in any segment
- O_NOFOLLOW|O_CREAT|O_EXCL flags (belt-and-suspenders against symlink attacks)
- 0o600 mode (owner-only read/write)
- Per-process nonce in the parent dir (prevents pre-created symlinks)
- Concurrent callers await the same extraction promise (memoized by Promise, not result)

Then `getPromptForCommand` prepends `Base directory for this skill: <dir>` so the model can Read/Grep files on demand. Same contract as disk-based skills.

**Production insight — extraction is lazy and memoized per-process.** The extraction promise is captured in a closure variable:
```typescript
let extractionPromise: Promise<string | null> | undefined
getPromptForCommand = async (args, ctx) => {
  extractionPromise ??= extractBundledSkillFiles(definition.name, files)
  const extractedDir = await extractionPromise
  ...
}
```
First call extracts, all subsequent calls await the same promise. No race, no double-write.

### loadSkillsDir.ts — Key Functions

**`parseSkillFrontmatterFields()`** — parses all frontmatter fields shared between file-based and MCP skills:
- `model: 'inherit'` → undefined (use parent's model)
- `context: 'fork'` → sub-agent execution
- `paths: ['src/**', 'tests/**']` → skill only surfaces when working in matching paths
- `shell:` → inline shell execution config
- `effort:` → effort level override
- `user-invocable: false` → hides from `/skills` listing but still auto-invocable

**`createSkillCommand()`** — builds a `Command` object. `getPromptForCommand` does 4 transforms in order:
1. Prepend `Base directory for this skill: <dir>` if skill has a base dir
2. `substituteArguments()` — replace `$arg_name` with user-provided args
3. Replace `${CLAUDE_SKILL_DIR}` with the skill's directory (for bash injection scripts)
4. Replace `${CLAUDE_SESSION_ID}` with current session ID
5. `executeShellCommandsInPrompt()` — run inline `!`...`\`` blocks (disabled for MCP skills)

**Token budgeting:** Skills only load `name + description + whenToUse` tokens for the model's tool list. Full content loaded only on invocation (`contentLength: markdownContent.length` tracks this but content itself isn't kept in memory at load time).

**Deduplication:** Uses `realpath()` to resolve symlinks → canonical path. Reason in comments: "inode values unreliable on ExFAT/NFS/container filesystems." Realpath is filesystem-agnostic.

**Source tracking:** `LoadedFrom` type:
```typescript
type LoadedFrom = 'commands_DEPRECATED' | 'skills' | 'plugin' | 'managed' | 'bundled' | 'mcp'
```
This determines trust level (e.g., MCP skills can't execute shell commands).

### mcpSkillBuilders.ts — Dependency Cycle Breaker

**Problem:** `client.ts` → `mcpSkills.ts` → `loadSkillsDir.ts` → (everything) → `client.ts`. Circular.

**Solution:** A leaf module (`mcpSkillBuilders.ts`) that:
1. Imports nothing except types
2. Exports a write-once registry: `registerMCPSkillBuilders()` / `getMCPSkillBuilders()`
3. Gets populated at `loadSkillsDir.ts` module init (which runs at startup via static import)
4. MCP client calls `getMCPSkillBuilders()` when needed

Non-literal dynamic imports (`await import(variable)`) fail in Bun-bundled binaries. The comment explains why literal dynamic imports also don't work (dependency-cruiser tracks them, creating cycle violations). The registry pattern is the only viable option.

---

## 3. Bundled Skills — Analysis

### /simplify (simplify.ts — 69 lines)

Spawns **3 parallel review agents** in a single Agent tool call:
1. **Code Reuse** — search for existing utilities that replace new code
2. **Code Quality** — redundant state, parameter sprawl, copy-paste, leaky abstractions, stringly-typed code, unnecessary JSX nesting, unnecessary comments
3. **Efficiency** — N+1 patterns, missed concurrency, hot-path bloat, TOCTOU anti-patterns, memory leaks

After all three report: aggregate findings, fix each issue. False positives: note and skip, don't argue.

**Production insight:** The efficiency review explicitly checks for "recurring no-op updates" — state updates inside polling loops that fire unconditionally without change detection. Also explicitly calls out the TOCTOU anti-pattern (pre-checking file existence before operating).

### /batch (batch.ts — 124 lines)

Full parallel work orchestration pattern:

```
Phase 1: Plan Mode
  - research scope (foreground subagents — need results)
  - decompose into 5–30 independent units
  - determine e2e test recipe (ask user if not discoverable)
  - write plan, exit plan mode for approval

Phase 2: Spawn Workers
  - all agents: isolation: "worktree", run_in_background: true
  - single message with all Agent tool calls (true parallelism)
  - each prompt: self-contained (goal + task + conventions + e2e recipe + worker instructions)

Phase 3: Track Progress
  - render status table
  - parse PR: <url> from each completion notification
  - re-render table as agents complete
```

**Production insight — worker instructions are embedded verbatim.** The worker instruction template (simplify → tests → e2e → commit+push → PR → report `PR: <url>`) is string-embedded into every agent's prompt. Workers cannot deviate from the protocol. The coordinator parses `PR: <url>` as a machine-readable status signal.

**E2e test recipe determination** is mandatory — either discoverable (claude-in-chrome, tmux CLI, dev-server+curl, existing e2e suite) or ask the user with 2-3 concrete options. Workers cannot ask the user themselves (they run in background).

### /loop (loop.ts — 92 lines)

Interval parsing with 3-rule priority:
1. Leading `Ns/Nm/Nh/Nd` token → interval
2. Trailing `every <N><unit>` clause → extract interval, strip from prompt
3. Default: `10m`, entire input is prompt

Converts interval to cron expression with explicit rounding rules (e.g., 7m → nearest clean division). If interval doesn't cleanly divide, rounds and tells user. Then calls `CronCreate`, confirms, and **immediately executes the prompt** without waiting for first cron fire.

### /skillify (skillify.ts — 197 lines)

Session-to-skill converter. At invocation:
1. Reads `getSessionMemoryContent()` (pre-computed summary)
2. Extracts user messages from `getMessagesAfterCompactBoundary(context.messages)`
3. Templates both into `SKILLIFY_PROMPT` with `{{sessionMemory}}` and `{{userMessages}}`

Interview is 4 rounds via `AskUserQuestion` (not plain text — explicitly enforced). Round 3 breaks down each step with explicit questions about: data/artifacts produced, success criteria, human checkpoints for irreversible actions, concurrency opportunities, execution model (Direct/Task agent/Teammate/[human]).

The generated SKILL.md format is specified in detail in the prompt, including per-step `**Success criteria**` as mandatory.

### /remember (remember.ts — 82 lines)

Multi-layer memory audit. Classifies each auto-memory entry against:
- `CLAUDE.md` — project conventions all contributors should follow
- `CLAUDE.local.md` — personal instructions for this user
- Team memory — org-wide across repos
- Stay in auto-memory — uncertain or ephemeral

Explicitly distinguishes: CLAUDE.md/CLAUDE.local.md contain **instructions for Claude**, not user preferences for external tools (editor themes, IDE keybindings don't belong here). Reports proposed changes grouped by action type before applying any.

### /update-config (updateConfig.ts — 475 lines)

Largest bundled skill. Generates settings schema dynamically from the `SettingsSchema()` Zod type at invocation time (`toJSONSchema(SettingsSchema(), { io: 'input' })`), ensuring the skill docs stay in sync with the actual TypeScript types.

Contains a 6-step **hook construction and verification flow**:
1. Dedup check (read existing file first)
2. Construct command for THIS project (don't assume package manager)
3. Pipe-test the raw command with synthesized stdin
4. Write the JSON
5. Validate with `jq -e` (exit codes 4/5 distinguish matcher vs malformed JSON)
6. Prove the hook fires in-turn (for Write|Edit/Bash matchers)

**Production insight:** Step 3 ("pipe-test") is explicitly required before writing. The comment: "A hook that silently does nothing is worse than no hook." The verification workflow is more rigorous than most CI setups.

Supports `[hooks-only]` prefix arg to return only hook docs + verification flow (for when the user only needs hook setup).

### /claudeApi (claudeApi.ts — 196 lines)

Lazy-loads 247KB of API documentation (`claudeApiContent.js`) only on invocation. At invocation:
1. Reads cwd directory listing to detect language (`.py`, `tsconfig.json`, `pom.xml`, etc.)
2. Filters skill files to `${lang}/` + `shared/` directories
3. Strips HTML comments from markdown (loop until stable, handles nested comments)
4. Substitutes `{{variable}}` template vars from `SKILL_MODEL_VARS`

**Production insight:** Heavy content is lazy-loaded and language-filtered. The skill only serves relevant docs — a Python project doesn't get TypeScript examples. The 247KB is the full SDK docs for all languages; per-invocation payload is a fraction of that.

### /stuck (stuck.ts — 79 lines)

ANT-only diagnostic skill. Uses `ps -axo pid=,pcpu=,rss=,state=,comm=,command=` to identify stuck Claude Code sessions. Diagnostic criteria:
- High CPU (≥90%) sustained — sample twice 1-2s apart
- Process state `D` (uninterruptible sleep) — I/O hang
- Process state `T` (stopped) — user hit Ctrl+Z
- Process state `Z` (zombie) — parent not reaping
- High RSS (≥4GB) — memory leak
- Hung child process (`pgrep -lP <pid>`)

Posts to `#claude-code-feedback` Slack channel using Slack MCP tool if a stuck session found. Uses `ToolSearch` to find `slack_send_message` if not loaded. Two-message structure: top-level terse summary, thread reply for full diagnostics.

---

## 4. plugins/ — Plugin Registry

### builtinPlugins.ts (159 lines)

```typescript
// Plugin ID format: {name}@builtin
const BUILTIN_PLUGINS: Map<string, BuiltinPluginDefinition> = new Map()
```

**Distinction between bundled skills and builtin plugins:**
- **Bundled skills** (`src/skills/bundled/`): always-on, invisible to user, not user-toggleable
- **Builtin plugins** (`src/plugins/builtinPlugins.ts`): appear in `/plugin` UI, user can enable/disable, persist to `settings.enabledPlugins`

Enabled state resolution: `user preference > plugin default > true`

`skillDefinitionToCommand()` converts a `BundledSkillDefinition` to a `Command` but uses `source: 'bundled'` (not `'builtin'`). Comment explains why: `'builtin'` in `Command.source` means hardcoded slash commands like `/help`, `/clear`. Using `'bundled'` keeps plugin skills in the Skill tool listing, analytics name logging, and prompt-truncation exemption.

### plugins/bundled/index.ts (23 lines)

`initBuiltinPlugins()` is currently empty scaffolding. Comment: "this is the scaffolding for migrating bundled skills that should be user-toggleable." The infrastructure exists; no features have migrated yet.

---

## 5. utils/bash/specs/ — Bash Command Specifications

**Total lines:** ~213 across 8 files

```
alias.ts    — alias definition (variadic args)
nohup.ts    — nohup wrapper (isCommand: true arg)
pyright.ts  — Python type checker (full option spec: 91 lines)
sleep.ts    — sleep
srun.ts     — SLURM cluster runner (ntasks, nodes options)
timeout.ts  — timeout wrapper (isCommand: true arg)
time.ts     — time wrapper
index.ts    — exports all 7 as CommandSpec[]
```

**`CommandSpec` type** (not read directly but inferred from usage):
```typescript
type CommandSpec = {
  name: string
  description: string
  options?: { name: string | string[], description: string, args?: {...} }[]
  args?: { name: string, description: string, isOptional?: boolean, isVariadic?: boolean, isCommand?: boolean } | {...}[]
}
```

`isCommand: true` marks an argument as a subcommand — the CLI can then recurse into that command's own argument specs for autocompletion and help text.

**Production insight:** These specs feed into the bash tool's permission/autocompletion registry. Claude Code knows the formal argument structure of these shell commands, not just their existence. This enables structured permission rules like `Bash(timeout:*)` — matching the spec name, not a substring.

**`srun` for SLURM** is notable — this is a HPC cluster job scheduler. Claude Code explicitly supports running on compute clusters, not just developer laptops.

---

## 6. Production Insights — Cross-Cutting

### Feature flag pattern (`bun:bundle`)

```typescript
import { feature } from 'bun:bundle'

// Compile-time constant:
const reactiveCompact = feature('REACTIVE_COMPACT')
  ? (require('../../services/compact/reactiveCompact.js') as typeof import(...))
  : null

// Later:
if (reactiveCompact?.isReactiveOnlyMode()) { ... }
```

`feature()` is a Bun bundler macro — evaluated at build time, dead code eliminated. `require()` (not `import`) inside the conditional avoids the bundler from including the module in the output when the flag is false. This is how you ship feature-flagged code in a single binary.

### Skill loading hierarchy

Skills load from 4 sources, merged in priority order:
1. **Policy (managed)** — MDM/enterprise settings, cannot be overridden
2. **User settings** — `~/.claude/skills/`
3. **Project settings** — `.claude/skills/`
4. **Bundled** — compiled into binary

MCP skills are discovered separately at server connection time and injected into the same Command registry.

### MCP skill security boundary

MCP skills come from remote, untrusted servers. Two restrictions:
1. `${CLAUDE_SKILL_DIR}` substitution is skipped (meaningless for MCP)
2. Inline shell execution (`!`...`\``) is disabled (`if (loadedFrom !== 'mcp')`)

File-based and bundled skills can execute shell commands in their prompt body. MCP skills cannot.

### `disableModelInvocation` flag

Present on several bundled skills (e.g., `/skillify`, `/batch`). Effect: the skill's `getPromptForCommand()` result goes directly to the model as a user message without additional model invocation overhead. Contrast with regular skills where the skill prompt is injected and the model is called anew.

Looked at from the other direction: most skills return a prompt that the model then acts on. `disableModelInvocation: true` means the skill IS the next model turn's instructions — the prompt itself is the full context injection.

---

## 7. Mapping to Adoptable Patterns

### Pattern 1: Skill as prompt document

Every bundled skill is a TypeScript file that registers a `getPromptForCommand()` returning markdown. The markdown IS the agent's instructions for that invocation.

**Adoptable:** Our `handoff`, `reflect`, `pomo` skills already follow this. The production pattern adds: `whenToUse` for auto-invocation, `context: 'fork'` for isolated sub-agents, `isEnabled()` for conditional availability.

### Pattern 2: Multi-phase skill with mandatory structured output

`/batch` workers must end with `PR: <url>`. `/simplify` agents must report findings in a specific format. `/loop` skips to usage if prompt is empty.

**Adoptable:** Any skill that spawns background agents should define a machine-readable output contract. Our `/grant` and `/apply` skills need this.

### Pattern 3: Lazy content loading + language detection

`/claudeApi` reads the directory listing, detects language, loads only the relevant docs subset. The 247KB total is never fully loaded.

**Adoptable:** Our `study` skill could detect the course language/framework and load only the relevant portion of the style guide.

### Pattern 4: Feature-flagged require() for optional modules

Use `bun:bundle` feature flags to gate expensive imports. Code for disabled features is compiled out entirely.

**Applicable to us:** Less relevant since we don't ship a binary, but the pattern applies to any conditional-capability system.

### Pattern 5: Session memory extraction for meta-skills

`/skillify` calls `getSessionMemoryContent()` + `getMessagesAfterCompactBoundary(context.messages)`. This gives the skill the compressed session summary AND the raw user messages.

**Adoptable directly:** Our `handoff` skill should extract session memory + user messages in the same way. The session memory is the "what happened" summary; the user messages show "how the user steered the process."

### Pattern 6: Hook construction with pipe-test verification

The `/update-config` hook verification flow (6 steps, includes pipe-test before writing) is a production SOP for hook setup.

**Adoptable:** When our `update-config` skill adds hooks, it should follow this flow: construct → pipe-test → write → validate JSON → prove it fires in-turn.

### Pattern 7: Dependency cycle via write-once registry

When module A needs a function from module B, but B imports A (directly or transitively), create module C that:
- Imports nothing
- Exposes `register()` and `get()`
- B calls `register()` at init time
- A calls `get()` when it needs the function

**Adoptable:** Our agent registry pattern in the main loop could use this if circular deps appear.

---

## 8. File Inventory

```
commands/           ~26,400 lines TS/TSX
  ├── compact/      287 lines — 3-path compaction
  ├── plan/         121 lines — mode toggle
  ├── init.ts       256 lines — 7-phase onboarding
  ├── context/      325 lines (noninteractive) — token count mirror
  ├── insights.ts   3,200 lines — usage analytics
  ├── plugin/       ~5,000 lines — full marketplace UI
  └── ... ~130 other commands

skills/             ~4,066 lines TS
  ├── loadSkillsDir.ts      1,086 — core loader
  ├── bundledSkills.ts      220   — bundled registry + file security
  ├── mcpSkillBuilders.ts   44    — cycle breaker
  └── bundled/
      ├── index.ts          79    — startup registration
      ├── updateConfig.ts   475   — hooks SOP + settings schema
      ├── scheduleRemoteAgents.ts 447
      ├── keybindings.ts    339
      ├── batch.ts          124   — parallel work orchestration
      ├── skillify.ts       197   — session → skill
      ├── simplify.ts       69    — 3-agent parallel review
      ├── loop.ts           92    — cron scheduling
      ├── remember.ts       82    — memory audit
      ├── claudeApi.ts      196   — lazy SDK docs
      ├── stuck.ts          79    — ANT-only diagnostics
      └── ...

plugins/            ~182 lines TS
  ├── builtinPlugins.ts     159   — user-toggleable plugin registry
  └── bundled/index.ts      23    — empty scaffolding

utils/bash/specs/   ~213 lines TS
  ├── pyright.ts    91    — full option spec
  ├── srun.ts       31    — SLURM
  ├── timeout.ts    20    — timeout wrapper
  └── alias/nohup/sleep/time/index  — simple specs
```

---

## 9. What Tutorials Don't Teach

1. **Skills are not just prompt templates.** They are `Command` objects with permission scope, model overrides, path filters, lifecycle hooks, execution context (inline vs fork), and conditional availability. The markdown body is loaded lazily and preprocessed (arg substitution, shell execution, dir injection) at invocation time.

2. **The gap between UI and model context.** The REPL keeps snipped messages for scrollback. The compact command strips them before summarization. The `/context` command mirrors the exact pre-API transforms. "What the user sees" and "what the model processes" diverge by design.

3. **Hook verification is a 6-step protocol.** You don't just write hook JSON. You pipe-test it, validate with jq, and prove it fires in-turn. A silently non-firing hook is worse than no hook.

4. **Bundled vs builtin vs plugin is a 3-way distinction.** Bundled = always-on, invisible. Builtin = in /plugin UI, user-toggleable. Plugin = from marketplace, installed. All ultimately produce `Command` objects with `source: 'bundled'`.

5. **`isCommand: true` in bash specs enables recursive autocompletion.** `timeout <cmd>` can then suggest `<cmd>`'s own arguments. The spec registry knows about shell commands structurally, not just textually.

6. **MCP skills are second-class.** They can't execute inline shell commands. `${CLAUDE_SKILL_DIR}` is meaningless for them. The trust boundary is `loadedFrom !== 'mcp'`.

7. **`/batch` commits to a progress table contract.** Workers must emit `PR: <url>`. The coordinator parses this. Background agent output is treated as structured data, not prose.
