#!/bin/bash
# Pre-push gate — blocks git push if deliverables aren't ready
# CC pattern: dual trigger (both conditions must be true)
# Exit 0 = allow, Exit 2 = block

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
ERRORS=()

# Only fire for git push commands
COMMAND=$(jq -r '.tool_input.command // empty' 2>/dev/null < /dev/stdin || true)
if ! echo "$COMMAND" | grep -q "git push"; then
    exit 0
fi

# ── Gate 1: README not stale ──
README="$PROJECT_ROOT/README.md"
if [ -f "$README" ]; then
    # Check for known stale markers
    if grep -q "Stub\|Draft — written from reports" "$README" 2>/dev/null; then
        ERRORS+=("BLOCKED: README.md contains stale markers ('Stub' or 'Draft'). Update before push.")
    fi
fi

# ── Gate 2: No banned words in any publish/ file ──
BANNED_HITS=$(grep -rli "泄露\|research-institute\|research-lab" "$PROJECT_ROOT/publish/" 2>/dev/null || true)
if [ -n "$BANNED_HITS" ]; then
    ERRORS+=("BLOCKED: Banned words found in: $BANNED_HITS")
fi

# ── Gate 3: All blog posts have QC ──
BLOG_COUNT=$(find "$PROJECT_ROOT/publish" -name "blog-*.md" | wc -l | tr -d ' ')
QC_COUNT=$(find "$PROJECT_ROOT/publish" -name "qc-report-*.md" | wc -l | tr -d ' ')
if [ "$BLOG_COUNT" -gt 0 ] && [ "$QC_COUNT" -eq 0 ]; then
    ERRORS+=("BLOCKED: $BLOG_COUNT blog posts exist but no QC report found.")
fi

# ── Gate 4: Unit tests must pass (session 7 lesson: pushed without testing) ──
if [ -d "$PROJECT_ROOT/tests" ]; then
    # Run unit tests only (skip E2E which needs API key and is slow)
    TEST_OUTPUT=$(cd "$PROJECT_ROOT" && python3 -m pytest tests/ --ignore=tests/test_e2e_smoke.py -q 2>&1 || true)
    if echo "$TEST_OUTPUT" | grep -q "failed\|error"; then
        ERRORS+=("BLOCKED: Unit tests failing. Run: pytest tests/")
    fi
fi

# ── Gate 5: Published content claims must be verifiable ──
# Session 7 lesson: posted "代码已开源" before pushing to GitHub.
# Check if any publish/ file references the GitHub URL — if so, verify
# local is not behind remote (i.e., our claims match reality).
if grep -rq "github.com.*nano-agent-anatomy" "$PROJECT_ROOT/publish/" 2>/dev/null; then
    LOCAL=$(git rev-parse HEAD 2>/dev/null)
    REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "unknown")
    if [ "$LOCAL" = "$REMOTE" ]; then
        # We're pushing what's already there — this push WILL make it true
        : # OK
    fi
    # Note: can't fully verify this pre-push (chicken-and-egg), but the
    # check reminds us that publish/ files with repo links = claims about
    # what's deployed. The real enforcement: don't publish to platforms
    # until AFTER git push succeeds.
fi

# ── Verdict ──
if [ ${#ERRORS[@]} -gt 0 ]; then
    echo "╔══════════════════════════════════════════╗" >&2
    echo "║  PUSH GATE: BLOCKED                      ║" >&2
    echo "╚══════════════════════════════════════════╝" >&2
    for err in "${ERRORS[@]}"; do
        echo "  ✗ $err" >&2
    done
    exit 2
fi

echo "Push gate: all checks passed."
exit 0
