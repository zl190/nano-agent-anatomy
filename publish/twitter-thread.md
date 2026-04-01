**Tweet 1 (hook):**
Claude Code's source leaked 3 days ago. I've been reading all 513K lines. The 4 biggest surprises:

**Tweet 2:**
1/ Context compression in production is NOT deterministic. The Rust port uses zero LLM calls. CC's TypeScript uses a full LLM call with a 9-section prompt + hidden scratchpad. Same feature, completely different architecture.

**Tweet 3:**
2/ The multi-agent coordinator is a prompt, not code. SDK gives you a dataclass. CC's actual implementation says "Never delegate understanding." It manages other AIs by talking to them, not by calling APIs.

**Tweet 4:**
3/ Permission denials don't throw errors — they continue the loop. CC returns deny reasons as is_error=True tool results. The model sees the rejection and recovers. Tutorials just skip the tool.

**Tweet 5:**
4/ Memory isn't a list. It has a garbage collector. autoDream fires after 24h + 5 sessions: orient → gather → consolidate → prune. Plus a 256-token side call for relevance filtering. The SDK exposes a flag. The source has a 2-layer system.

**Tweet 6:**
I rebuilt each layer in ~150 lines of Python. 76 tests. Cross-validated against 5 sources. Repo + sample analysis note: github.com/zl190/nano-agent-anatomy
