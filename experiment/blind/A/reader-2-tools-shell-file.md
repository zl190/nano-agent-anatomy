# Reader 2: Tools - Shell & File

## Source Reading Report: Tool Layer (BashTool, FileReadTool, FileEditTool, FileWriteTool, GlobTool, GrepTool, PowerShellTool)

---

### BashTool (src/tools/BashTool/)

**Line count:** 12,411 total across 18 files. Core dispatch file (BashTool.tsx) is 1,143 lines. Security subsystems (bashPermissions.ts, bashSecurity.ts, readOnlyValidation.ts) each exceed 1,900-2,600 lines -- they dwarf the tool itself.

**Core functions/classes:**

- `isSearchOrReadBashCommand(command)` -- Classifies compound shell pipelines as read/search/list by walking every segment through semantic sets; `echo`/`printf`/`true` are "semantic neutral" and are skipped so `ls && echo "---" && ls` still classifies as a list.
- `isSilentBashCommand(command)` -- Returns true for commands like `mv`, `cp`, `rm` that produce no stdout on success; used to show "Done" in UI rather than "(No output)".
- `detectBlockedSleepPattern(command)` -- Blocks bare `sleep N` (N >= 2s) calls and redirects agent toward Monitor tool; float seconds and `sleep` inside pipelines are allowed.
- `isAutobackgroundingAllowed(command)` -- Prevents `sleep` from being auto-backgrounded by the assistant.
- `applySedEdit(simulatedEdit, toolUseContext)` -- Applies a pre-verified sed substitution directly without spawning a shell process; ensures the file written matches exactly what the user approved in the diff preview.
- `BashTool` (exported object via `buildTool`) -- The main tool definition; implements `checkPermissions`, `validateInput`, `call`, `mapToolResultToToolResultBlockParam`, and `preparePermissionMatcher`.

**commandSemantics.ts** (140 lines):
- `interpretCommandResult(command, exitCode, stdout, stderr)` -- Implements per-command exit code semantics. `grep` exit 1 = "No matches found" (not error); `find` exit 1 = partial success; `diff` exit 1 = "Files differ". Tutorials teach "nonzero = error"; this file teaches that exit codes are command-specific vocabulary.

**modeValidation.ts** (115 lines):
- `checkPermissionMode(input, toolPermissionContext)` -- Handles `acceptEdits` mode which auto-allows `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed` without asking. Permission decisions return `allow`, `ask`, or `passthrough` -- a three-way enum, not a boolean.

**destructiveCommandWarning.ts** (102 lines):
- `getDestructiveCommandWarning(command)` -- Regex-based scan returning a human-readable warning shown in the permission dialog. Purely informational; does not block. Covers `git reset --hard`, `git push --force`, `git stash drop`, `rm -rf`, `kubectl delete`, `terraform destroy`, SQL `TRUNCATE/DROP`.

**shouldUseSandbox.ts** (153 lines):
- `shouldUseSandbox(input)` -- Determines whether to wrap execution in sandbox. Applies fixed-point stripping of env-var prefixes and wrapper commands (`timeout 300 npm ...` -> `npm ...`) so sandbox exclusions work even through layers of wrapping.

**sedEditParser.ts** (322 lines):
- `parseSedEditCommand(command)` -- Detects `sed -i 's/pattern/replacement/flags' file` patterns and extracts the edit info. When detected, BashTool renders the result as a FileEdit diff rather than raw shell output.

**pathValidation.ts** (1,303 lines):
- Enumerates ~30 path-carrying commands (`rm`, `git`, `sed`, `cp`, `mv`, etc.) with per-command path extractors that correctly handle the POSIX `--` end-of-options delimiter. Without `--` awareness, `rm -- -/../.claude/settings.local.json` bypasses path validation.

**readOnlyValidation.ts** (1,990 lines):
- `checkReadOnlyConstraints(input, compoundCommandHasCd)` -- Per-command flag allowlists determine if a command is safe to run read-only. Security-sensitive flags like `fd`'s `-x/--exec` and `-l/--list-details` (the latter internally runs `ls` as a subprocess -- PATH hijack risk) are explicitly excluded.

**bashPermissions.ts** (2,621 lines) / **bashSecurity.ts** (2,592 lines):
- The permission/security engines. `preparePermissionMatcher` uses AST parsing (not regex) to decompose compound commands into subcommands before matching rules, so `ls && git push` can't evade a `Bash(git *)` security hook.

**Production insights:**

1. **Three-tier permission result, not boolean.** `allow` / `ask` / `passthrough` -- passthrough means "I don't handle this, try the next layer." Tutorials show boolean permission checks; this is a chain-of-responsibility.
2. **Command semantics are a first-class layer.** Exit code meaning is not uniform. A separate module maps each command to its own interpretation function. This prevents grep exit 1 from being treated as a hard error.
3. **Sed is intercepted and simulated.** When a `sed -i` edit is recognized, the user-approved diff is applied directly without running sed. The `_simulatedSedEdit` field is deliberately stripped from the model-facing schema (comment: "exposing it would let the model bypass permission checks").
4. **Sandbox exclusion uses fixed-point stripping.** The algorithm iteratively strips env-var prefixes and wrapper commands until stable. Single-pass composition fails on `timeout 300 FOO=bar bazel run` -- the fixed-point loop handles interleaved patterns.
5. **Read-only classification is pipeline-level.** ALL parts of a pipe must be read/search commands for the whole pipeline to be classified as collapsible/read-only. One non-read command in the chain defeats read-only status.
6. **cd+git cross-segment detection.** The permission system detects `cd sub && echo | git status` as dangerous because cd and git span pipe segments. Each segment is checked independently for the cd/git pair regardless of where in the pipeline they appear -- this prevents a bare-repo fsmonitor bypass.
7. **POSIX `--` delimiter matters for path extraction.** `rm -- -/../secret` would bypass naive path validation. The path extractor is aware of `--` and treats everything after it as a positional argument, not a flag.

**Patterns we can adopt:**

- Command-specific exit code semantics map (grep/diff/find are the most important cases).
- Three-way permission result type: `allow` / `deny` / `passthrough` instead of a boolean.
- Silent command detection to show "Done" instead of "(No output)".
- Destructive pattern warnings as a purely informational layer separate from the permission layer.

---

### FileReadTool (src/tools/FileReadTool/)

**Line count:** 1,613 total. Main file 1,183 lines; limits.ts 92 lines; imageProcessor.ts 94 lines.

**Core functions:**

- `FileReadTool` (exported via `buildTool`) -- Unified reader for text, images (PNG/JPG/GIF/WebP), PDFs, Jupyter notebooks. Dispatches to different handlers and returns discriminated union output typed as `text | image | notebook | pdf | parts | file_unchanged`.
- `getDefaultFileReadingLimits()` -- Memoized function returning `maxTokens` (default 25,000) and `maxSizeBytes` (default 256 KB). Precedence: env var > GrowthBook feature flag > hardcoded default. Memoized so the cap doesn't change mid-session as GrowthBook refreshes.
- `registerFileReadListener(listener)` -- Hook for other services to be notified of file reads; returns an unsubscribe function.
- `MaxFileReadTokenExceededError` -- Error class that includes the actual token count and limit, so the model's error message tells it to use `offset`/`limit`.
- `isBlockedDevicePath(filePath)` -- Path-only check (no I/O) that blocks `/dev/random`, `/dev/stdin`, `/dev/tty`, `/proc/self/fd/0-2`, etc. -- files that would produce infinite output or block waiting for input.
- `getAlternateScreenshotPath(filePath)` -- Handles macOS screenshot filenames that use a thin space (U+202F) vs regular space before AM/PM, varying by macOS version.

**Read deduplication (lines 524-573):** If the model requests the same file at the same offset/limit and the mtime hasn't changed, the tool returns a `file_unchanged` stub (~100 bytes) instead of re-sending up to 25,000 tokens. The comment documents the measurement: ~18% of Read calls are same-file collisions, up to 2.64% of fleet cache_creation tokens wasted without dedup. The dedup only applies when offset is set (meaning the entry came from a Read, not from a prior Edit/Write that set mtime but not offset).

**imageProcessor.ts** -- Dynamic import of either `image-processor-napi` (bundled native module) or `sharp` as fallback. ESM vs CJS interop is handled by an `unwrapDefault` helper since import shape varies by module interop mode.

**limits.ts** -- Two-cap design documented in a table comment: `maxSizeBytes` gates on total file size before reading (1 stat call); `maxTokens` gates on actual output tokens after reading (1 API call). A deliberate note documents a tested alternative (truncate instead of throw) that was reverted because truncation yielded ~25K tokens of content at the cap, worse than the 100-byte error path.

**Production insights:**

1. **Dedup via readFileState + mtime, not content hash.** Comparing content hashes would be expensive; mtime is a single stat call. The dedup only fires for entries with `offset !== undefined` -- this is a subtle invariant: Edit/Write set mtime but leave offset undefined, distinguishing post-edit entries.
2. **Two-cap system with different cost profiles.** The byte cap avoids reading giant files; the token cap avoids sending long files to the model. They are not the same check and fire at different points.
3. **Discriminated union output.** The output type is a discriminated union (`type: 'text' | 'image' | 'notebook' | 'pdf' | 'parts' | 'file_unchanged'`). This is architecturally important: one tool, six output shapes, type-safe dispatch in both the call site and the API mapping function.
4. **Device file blocklist is path-only, no I/O.** The blocklist check happens before any filesystem operations. Safe special files like `/dev/null` are intentionally omitted.
5. **Skills discovery is fire-and-forget.** When a file is read, the tool discovers any associated skill directories non-blockingly (`addSkillDirectories(newSkillDirs).catch(() => {})`) so skill loading doesn't delay the tool response.

**Patterns we can adopt:**

- Read deduplication keyed on (path, offset, limit, mtime).
- Discriminated union for tool output when a single tool handles multiple content types.
- Separate byte cap (pre-read) from token cap (post-read) so you pay only the cost appropriate to what you need to know.

---

### FileEditTool (src/tools/FileEditTool/)

**Line count:** 1,727 total. Main file 625 lines; utils.ts 775 lines; types.ts 85 lines.

**Core functions:**

- `FileEditTool` (via `buildTool`) -- String-replacement editor. Input: `file_path`, `old_string`, `new_string`, optional `replace_all`. Output: diff patch, original content, whether user modified the proposed change.
- `findActualString(fileContent, searchString)` -- Tries exact match first, then normalizes curly quotes to straight quotes in both the file and the search string, returning the actual string in the file that matched. This is the entry point for tolerant matching.
- `normalizeQuotes(str)` -- Converts curly quotes to straight equivalents. Claude's tokenizer can output curly quotes; files may have curly quotes; the search must be robust to both.
- `preserveQuoteStyle(oldString, actualOldString, newString)` -- When a match was found via quote normalization, applies the file's curly quote style to the replacement so the edit preserves typography.
- `getPatchForEdit(...)` -- Generates a structured diff patch (array of hunks) alongside the updated file content.
- `areFileEditsInputsEquivalent(input1, input2)` -- Used for deduplication of identical edit requests.

**Validation pipeline (validateInput):** Runs in order:
1. Team memory secret check
2. `old_string === new_string` (no-op guard)
3. Deny rule check (path-based permission)
4. UNC path bypass (NTLM credential leak prevention)
5. File size cap (1 GiB OOM guard)
6. Encoding detection and file content read
7. File existence check (empty `old_string` on nonexistent file = new file creation)
8. `.ipynb` redirect to NotebookEditTool
9. `readFileState` staleness check (must have been read first)
10. Mtime comparison (file modified since read?)
11. `findActualString` (does old_string exist in file, accounting for quote normalization?)
12. Multiple-match check (matches > 1 and replace_all = false -> error with count)
13. Settings file validation

**call() atomicity comment:** The code explicitly marks a "critical section" between the staleness check and `writeTextContent`. No async operations are allowed in between -- concurrent edits could interleave and corrupt the file. The backup (file history) is taken before the critical section since it is idempotent.

**Production insights:**

1. **Read-before-write is enforced, not advisory.** The tool rejects edits if `readFileState` has no entry for the file, or if the file's mtime is newer than the last read timestamp. This catches concurrent tool calls and external edits (linters, cloud sync).
2. **Quote normalization is two-phase.** First: find the actual string in the file via normalized search. Second: when applying the replacement, mirror the file's quote style back onto `new_string`. Without the second phase, edits would silently change file typography.
3. **Multiple-match detection with count.** When `old_string` appears multiple times and `replace_all` is false, the error message includes the count and explicitly tells the model to either provide more context (to uniquify) or set `replace_all`.
4. **LSP integration after write.** After writing, the tool fires `clearDeliveredDiagnosticsForFile` and LSP `didChange`/`didSave` notifications so language servers update their diagnostics. This is invisible to the model but critical for IDE integration.
5. **Skill discovery is triggered on file write.** Writing to a new path can activate project-specific skills. The skill discovery is non-blocking and fire-and-forget.

**Patterns we can adopt:**

- Multi-step ordered validation that short-circuits at the first failure.
- Read-before-write enforcement via a shared state map (path -> {content, timestamp}).
- Quote normalization to handle the gap between what a model produces and what files contain.

---

### FileWriteTool (src/tools/FileWriteTool/)

**Line count:** 856 total. Main file 434 lines.

**Core functions:**

- `FileWriteTool` (via `buildTool`) -- Full-file writer. Input: `file_path`, `content`. Output: discriminated `create | update`, diff patch, original content, git diff. Unlike FileEditTool, no `old_string` required -- writes the full file.
- Shares `hunkSchema` and `gitDiffSchema` with FileEditTool (imported from FileEditTool/types.ts).

**Validation differences from FileEditTool:** FileWriteTool skips the quote normalization and multiple-match checks (irrelevant for full writes), but still enforces read-before-write for existing files. New files (ENOENT) skip the staleness check.

**Git diff in output:** Both FileEditTool and FileWriteTool fetch a git diff after writing (`fetchSingleFileGitDiff`) and include it in the tool result. This gives the model visibility into exactly what changed in the git index.

**Production insights:**

1. **Read-before-write applies to writes too.** Even a full-file overwrite requires a prior read. This prevents the model from overwriting a file modified externally between its last read and the write.
2. **Output type discriminates create vs update.** The model can tell from the output whether it created a new file or overwrote an existing one, which matters for the surrounding narrative.

---

### GlobTool (src/tools/GlobTool/)

**Line count:** 267 total. Main file 198 lines.

**Core functions:**

- `GlobTool` (via `buildTool`) -- Pattern-based file finder. Input: `pattern`, optional `path`. Output: file list sorted by modification time (the sort is in the underlying `glob` utility), with a `truncated` boolean when results hit the 100-file limit.
- Results are relativized to cwd via `toRelativePath` before returning, saving tokens.

**Production insights:**

1. **Result truncation is surfaced in the tool result.** When truncated, the model receives an explicit message: "Results are truncated. Consider using a more specific path or pattern." This is better than silently capping -- the model knows to narrow its search.
2. **Default limit is 100 files.** Override via `globLimits.maxResults` from context, allowing callers to tune the limit without changing the schema.
3. **`isConcurrencySafe` is true.** Glob is declared safe for concurrent use -- the scheduler can run multiple Glob calls in parallel without coordination.

**Patterns we can adopt:**

- Expose a `truncated` flag in output; never silently cap results.
- Relativize all paths to cwd in output to save tokens.

---

### GrepTool (src/tools/GrepTool/)

**Line count:** 795 total. Main file 577 lines.

**Core functions:**

- `GrepTool` (via `buildTool`) -- ripgrep wrapper. Input: `pattern`, optional `path`, `glob`, `type`, `output_mode` (content/files_with_matches/count), `-A/-B/-C` context, `-n`, `-i`, `head_limit`, `offset`, `multiline`. Output: structured result object with mode, file count, filenames, content string.
- `applyHeadLimit(items, limit, offset)` -- Slices results with offset/limit pagination. Returns `appliedLimit` only when truncation actually occurred (so the model knows to paginate), not on every call.
- `formatLimitInfo(appliedLimit, appliedOffset)` -- Produces human-readable pagination info appended to results: "limit: 250, offset: 50".

**Key grep invocation details (call method):**
- Always passes `--hidden` (search hidden files by default).
- Excludes VCS directories (`.git`, `.svn`, `.hg`, `.bzr`, `.jj`, `.sl`) via `--glob !dir`.
- Applies `--max-columns 500` to prevent base64/minified content from flooding output.
- If pattern starts with `-`, uses `-e pattern` to prevent ripgrep from interpreting it as a flag.
- Plugin cache directories are excluded via `getGlobExclusionsForPluginCache`.

**Production insights:**

1. **Default head_limit of 250 is intentional.** The comment documents the measurement: unbounded content-mode greps can fill up to the 20KB persistence threshold, producing 6-24K tokens per grep in a heavy session. 250 is "generous enough for exploratory searches while preventing context bloat." Pass `head_limit=0` to disable.
2. **Patterns starting with `-` need `-e` flag.** The schema and call code handle this edge case explicitly. A naive ripgrep invocation would fail or produce wrong results for patterns like `-foo`.
3. **Three output modes with different semantics.** `files_with_matches` is the default (lowest cost, just paths); `content` shows matching lines with context; `count` shows occurrence counts per file. Each mode has different head_limit behavior and different tool result formatting.
4. **VCS directories are excluded at the ripgrep level, not post-filtered.** This is more efficient -- ripgrep never enters those directories.

**Patterns we can adopt:**

- `head_limit` + `offset` as first-class pagination parameters.
- Always exclude VCS dirs and cap line length in ripgrep invocations.
- Three output modes as a first-class enum -- don't return everything by default.

---

### PowerShellTool (src/tools/PowerShellTool/)

**Line count:** 8,819 total across 14 files. Core file 1,000 lines; permission/security/readOnly subsystems together ~4,700 lines.

**Core functions:**

- `PowerShellTool` (via `buildTool`) -- Windows PowerShell execution tool. Structurally mirrors BashTool almost exactly: same schema shape, same background task support, same 15s assistant blocking budget, same sandbox adapter.
- `isSearchOrReadPowerShellCommand(command)` -- PS-specific classifier using canonical cmdlet name resolution (so `gci` resolves to `get-childitem`, `gc` resolves to `get-content`, etc.).
- `detectBlockedSleepPattern(command)` -- PS port of BashTool's sleep pattern detector. Catches `Start-Sleep N`, `Start-Sleep -Seconds N`, and `sleep N` (built-in alias); allows `-Milliseconds`.
- `isWindowsSandboxPolicyViolation()` -- Guards against running PowerShell when enterprise policy requires sandboxing but sandboxing is unavailable on native Windows (bwrap/sandbox-exec are POSIX-only).

**gitSafety.ts** (176 lines) -- The most architecturally distinctive file in this group:
- `isGitInternalPathPS(arg)` and `isDotGitPathPS(arg)` -- Detects whether a PowerShell argument resolves to a git-internal path (HEAD, objects/, refs/, hooks/, .git/). This guards against the "bare-repo attack" where a compound PS command creates git-internal files in cwd, then runs git, which executes the freshly-created hooks.
- `normalizeGitPathArg(arg)` -- A multi-layer normalizer: strips parameter prefixes (PS 5.1 allows `/Path:value`), strips quotes, strips backtick escapes, handles PS `FileSystem::` provider prefixes, handles drive-relative paths, applies Win32 per-component trailing-space/dot stripping, then posix.normalize.
- `resolveEscapingPathToCwdRelative(n)` -- Resolves paths that escape cwd (leading `../` or absolute) back against actual cwd to catch `../project/hooks` that resolves to `./hooks`.

**clmTypes.ts** (211 lines) -- PowerShell Constrained Language Mode (CLM) allowed types allowlist. The security approach is inverted: instead of enumerating dangerous types, they permit only Microsoft's CLM-allowed types and block everything else. Notable removals: `adsi`/`adsisearcher` (LDAP network binds when cast), `cimsession` (WMI remote execution), `System.Net.WebClient`, `System.Reflection.*`.

**commandSemantics.ts** (142 lines) -- Same pattern as BashTool's but with PS-specific commands. Notably, `Test-Path` semantics: exit 0 = path exists (true), exit 1 = path doesn't exist (false) -- same as bash's `test` builtin.

**Production insights:**

1. **PowerShellTool is not a thin wrapper around BashTool.** It has its own 8,800-line security subsystem. The security requirements diverge significantly: PS has CLM, provider-qualified paths, PS 5.1 slash-as-flag-prefix, cmdlet aliases, NTFS 8.3 short names, and Windows drive-relative paths -- none of which exist in bash.
2. **The bare-repo attack is the central security concern.** The git safety module has extensive commentary on exactly two attack vectors: (1) bare-repo cwd triggers hooks from cwd if HEAD+objects+refs exist; (2) compound command creates these files then runs git. The guard fires on ANY write to git-internal paths, not just `.git/` subdirectories.
3. **NTFS short name awareness.** The `isDotGitPathPS` function checks for `git~N` patterns -- Windows 8.3 short names for `.git`. A naive `.git` prefix check would miss `git~1/hooks/pre-commit`.
4. **CLM inversion pattern.** Using the allowlist from Microsoft's own CLM specification to guard against dangerous types is more maintainable than maintaining a denylist of dangerous types. The denylist approach requires discovering every dangerous type; the allowlist approach inherits Microsoft's classification.
5. **Sandbox policy conflict detection.** If enterprise policy requires sandboxing but the platform can't sandbox (native Windows), the tool refuses execution rather than silently bypassing the policy. This is a policy-honoring refusal, not a capability limitation.

**Patterns we can adopt:**

- Allowlist-based type checking (inverted from the usual denylist approach).
- Path normalization that is aware of the target OS's path semantics (NTFS short names, drive-relative, UNC).

---

### Cross-Cutting Patterns

**`buildTool` interface (appears in every tool):** Every tool exports a plain object that satisfies the `ToolDef<InputSchema, OutputSchema>` interface. The methods are: `validateInput` (sync pre-flight), `checkPermissions`, `call` (the actual operation), `mapToolResultToToolResultBlockParam` (converts structured output to the Anthropic API format), `renderToolUseMessage` / `renderToolResultMessage` (React components for UI), `isReadOnly`, `isConcurrencySafe`, `isSearchOrReadCommand`, `extractSearchText`, `preparePermissionMatcher`. Tutorials show tool `call` as the only required method; production requires ~15 distinct lifecycle hooks.

**`lazySchema()`:** All input/output schemas are wrapped in `lazySchema(() => z.strictObject(...))`. This defers Zod schema construction to first use, preventing startup cost for schemas that may never be needed. It also enables the `omit()` pattern (e.g., BashTool omits `_simulatedSedEdit` and conditionally omits `run_in_background` from the model-facing schema).

**`semanticNumber` / `semanticBoolean`:** Zod preprocessors that coerce strings to numbers/booleans before validation. The model may emit `"3"` instead of `3` or `"true"` instead of `true`; these preprocessors absorb the variance without changing the downstream type.

**`readFileState` map (shared across FileReadTool, FileEditTool, FileWriteTool):** A session-scoped `Map<path, {content, timestamp, offset, limit}>` that is the enforcement mechanism for read-before-write. Edit/Write tools check it; Read tool populates it. The contract is that the timestamp is the mtime at the time of the last read.

**UNC path bypass (appears in every tool that does filesystem ops):** All tools short-circuit filesystem checks for UNC paths (`\\server\share`). The reason: on Windows, `fs.stat()` on a UNC path triggers SMB authentication, which could leak NTLM credentials to a malicious server. The permission check (which runs separately, in a controlled way) handles these paths.

**Permission result is a three-way enum:** `behavior: 'allow' | 'ask' | 'passthrough'`. Passthrough means "this layer has no opinion; try the next." This enables composable permission chains without any layer needing to know about the others.

---

### Mapping to Our Code

| Production pattern | Our equivalent | Gap |
|---|---|---|
| Command-specific exit code semantics | Not present | Add `interpret_exit_code(cmd, code)` dispatch table |
| Three-way permission result | Boolean `allowed` | Replace with `allow/ask/deny` |
| Read-before-write via timestamp map | Not present | Add `read_state: dict[path, mtime]` to context |
| Silent command detection (`mv` shows "Done") | Not present | Classify commands by expected stdout |
| Semantic neutral commands in pipeline classifier | Not present | Needed if we classify compound commands |
| Truncation surfaced in output | Partial | Add `truncated: bool` to all list outputs |
| Token + byte dual cap for file reads | Single check | Separate pre-read byte check from post-read token check |
| Destructive pattern warnings (informational, non-blocking) | Not present | Regex table -> warning string injected into permission prompt |
| `lazySchema` for deferred Zod construction | Not present | Wrap schemas in lambda to defer |

The most immediately adoptable patterns are: command-specific exit code semantics (small, high-value, well-isolated), read-before-write enforcement via a timestamp map (prevents the stale-write bug class), and surfacing `truncated` in all list outputs so the model knows when to paginate.
