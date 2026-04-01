#!/bin/bash
# Pre-publish gate — CC pattern: physical enforcement > prompts
# Fires before any mcp__xiaohongshu-mcp__publish_content or similar
# Exit 0 = allow, Exit 2 = block
#
# Why exit 2? CC uses maxTurns:1 to make non-compliance self-defeating.
# We use exit 2 to make publishing without QC physically impossible.
# Sonnet was 2.79% non-compliant with prompts. We were 100% non-compliant
# with our own framework. Same disease, same cure.

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
PUBLISH_DIR="$PROJECT_ROOT/publish"
TOOL_INPUT=$(cat -)  # Read stdin (JSON from CC hooks protocol)
ERRORS=()

# ── Gate 1: model.md exists (projection framework) ──
if [ ! -f "$PUBLISH_DIR/model.md" ]; then
    ERRORS+=("BLOCKED: model.md does not exist. Create source of truth before projecting.")
fi

# ── Gate 2: QC report exists for this session ──
QC_REPORTS=$(find "$PUBLISH_DIR" -name "qc-report-*.md" -newer "$PUBLISH_DIR/model.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$QC_REPORTS" -eq 0 ] && [ -f "$PUBLISH_DIR/model.md" ]; then
    ERRORS+=("BLOCKED: No QC report newer than model.md. Run independent QC first.")
fi

# ── Gate 3: Banned words scan ──
# Get content from tool input if available
CONTENT=$(echo "$TOOL_INPUT" | jq -r '.tool_input.content // empty' 2>/dev/null)
TITLE=$(echo "$TOOL_INPUT" | jq -r '.tool_input.title // empty' 2>/dev/null)
CHECK_TEXT="$TITLE $CONTENT"

BANNED_WORDS=("泄露" "泄漏" "leak" "research-institute" "Yinzhou" "research-lab" "honglab")
for word in "${BANNED_WORDS[@]}"; do
    if echo "$CHECK_TEXT" | grep -qi "$word"; then
        ERRORS+=("BLOCKED: Banned word '$word' found in content. Compliance risk.")
    fi
done

# ── Gate 4: Persona QC for this channel ──
# Check if channel-specific review exists
if echo "$TOOL_INPUT" | jq -r '.tool_name // empty' 2>/dev/null | grep -q "xiaohongshu"; then
    if [ ! -f "$PUBLISH_DIR/review-xhs-"*.md ] 2>/dev/null; then
        # Check for any XHS review
        XHS_REVIEWS=$(find "$PUBLISH_DIR" -name "review-xhs-*.md" -o -name "*xhs*review*.md" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$XHS_REVIEWS" -eq 0 ]; then
            ERRORS+=("BLOCKED: No XiaohongshuReviewer QC found. Run persona QC before publishing to 小红书.")
        fi
    fi
fi

# ── Gate 5: Claim verification (session 7 lesson) ──
# If content says "代码已开源" or links to GitHub, verify the repo is pushed.
if echo "$CHECK_TEXT" | grep -qi "开源\|open.source\|github"; then
    # Check if local is ahead of remote
    LOCAL=$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo "local")
    REMOTE=$(git -C "$PROJECT_ROOT" rev-parse origin/main 2>/dev/null || echo "remote")
    if [ "$LOCAL" != "$REMOTE" ]; then
        ERRORS+=("BLOCKED: Content claims code is open-source but local is ahead of remote. Run 'git push' first.")
    fi
fi

# ── Gate 6: Functional tests for new code ──
# If content mentions a feature (e.g. context_v4), verify it has tests
if echo "$CHECK_TEXT" | grep -qi "correction.*compact\|context_v4\|microcompact"; then
    if ! grep -q "TestCorrectionMicrocompact" "$PROJECT_ROOT/tests/test_context.py" 2>/dev/null; then
        ERRORS+=("BLOCKED: Content mentions correction-aware compaction but no tests found.")
    fi
fi

# ── Verdict ──
if [ ${#ERRORS[@]} -gt 0 ]; then
    echo "╔══════════════════════════════════════════╗" >&2
    echo "║  PUBLISH GATE: BLOCKED                   ║" >&2
    echo "╚══════════════════════════════════════════╝" >&2
    for err in "${ERRORS[@]}"; do
        echo "  ✗ $err" >&2
    done
    echo "" >&2
    echo "Fix all issues above, then retry publish." >&2
    exit 2
fi

echo "Publish gate: all checks passed."
exit 0
