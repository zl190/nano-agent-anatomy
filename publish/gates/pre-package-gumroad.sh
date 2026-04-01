#!/usr/bin/env bash
# Pre-package gate for Gumroad ZIP.
# Exit 0 = pass, exit 1 = fail. Run before zip creation.
set -euo pipefail

PKG_DIR="${1:-gumroad-package/agent-anatomy-course}"
FAIL=0

err() { echo "FAIL: $1"; FAIL=1; }
warn() { echo "WARN: $1"; }

echo "=== Pre-package gate: ${PKG_DIR} ==="

# 1. Marker scan — no draft/TODO/checkbox/WIP in shipping content
echo ""
echo "--- Marker scan ---"
MARKERS=$(grep -rn '\[ \]\|^TODO\|FIXME\|HACK\|^WIP\|placeholder' "$PKG_DIR" --include="*.md" \
  | grep -vi "provides.*TODO\|unlike.*TODO\|CS336.*TODO\|NOT cross" || true)
if [ -n "$MARKERS" ]; then
  err "Unchecked markers found:"
  echo "$MARKERS"
fi

DRAFT=$(grep -rn '^status: draft\|^## Status: Draft' "$PKG_DIR" --include="*.md" || true)
if [ -n "$DRAFT" ]; then
  err "Draft status markers found:"
  echo "$DRAFT"
fi

# 2. Local path scan — no /Users/ paths
echo ""
echo "--- Local path scan ---"
PATHS=$(grep -rn '/Users/' "$PKG_DIR" --include="*.md" || true)
if [ -n "$PATHS" ]; then
  err "Local paths found:"
  echo "$PATHS"
fi

# 3. Reference integrity — all referenced .md files exist in package
echo ""
echo "--- Reference integrity ---"
REFS=$(grep -roh 'publish/[a-zA-Z0-9_-]*\.md\|ROADMAP\.md' "$PKG_DIR" --include="*.md" 2>/dev/null | sort -u || true)
for ref in $REFS; do
  err "Reference to file outside package: $ref"
done

# 4. File count verification — README claims match reality
echo ""
echo "--- File count verification ---"
ACTUAL_NOTES=$(find "$PKG_DIR/notes" -name "*.md" -type f | wc -l | tr -d ' ')
README_CLAIM=$(grep -o '[0-9]* files' "$PKG_DIR/README.md" | head -1 | grep -o '[0-9]*')
if [ -n "$README_CLAIM" ] && [ "$README_CLAIM" != "$ACTUAL_NOTES" ]; then
  err "README claims $README_CLAIM notes files, actual count is $ACTUAL_NOTES"
fi

# 5. Minimum density — no file under 20 lines (likely stub)
echo ""
echo "--- Density check ---"
find "$PKG_DIR" -name "*.md" -type f | while read -r f; do
  LINES=$(wc -l < "$f" | tr -d ' ')
  if [ "$LINES" -lt 20 ]; then
    err "Thin file ($LINES lines): $f"
  fi
done

# 6. Stale label scan — known bad labels from audit
echo ""
echo "--- Stale label scan ---"
# Exclude the audit file — it documents the rename itself
STALE=$(grep -rn 'Anthropic Academy\|Agent SDK/CCA' "$PKG_DIR" --include="*.md" \
  | grep -v 'source-validation-audit\|pedagogical-research' || true)
if [ -n "$STALE" ]; then
  err "Stale labels found (should be 'Anthropic Docs & Eng Blog' / 'Agent SDK'):"
  echo "$STALE"
fi

echo ""
if [ "$FAIL" -ne 0 ]; then
  echo "=== GATE FAILED — do not package ==="
  exit 1
else
  echo "=== GATE PASSED — safe to package ==="
  exit 0
fi
