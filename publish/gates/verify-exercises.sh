#!/usr/bin/env bash
# Physical gate: verify all exercise references exist in the codebase.
# Exit 2 = gate fail (CC enforcement pattern).
set -uo pipefail

PROJ="$(cd "$(dirname "$0")/../.." && pwd)"
EXERCISES_DIR="${1:-$PROJ/gumroad-package/agent-anatomy-course/exercises}"
ERRORS=0

red()   { printf '\033[1;31m%s\033[0m\n' "$1"; }
green() { printf '\033[1;32m%s\033[0m\n' "$1"; }

# ── Check 1: Verify referenced .py files exist ──
echo "=== Checking file references ==="
for ex in "$EXERCISES_DIR"/*.md; do
    # Extract backtick-quoted .py filenames
    refs=$(grep -oE '`[a-z_]+_v[0-9]+\.py`|`[a-z_]+\.py`' "$ex" | tr -d '`' | sort -u)
    for ref in $refs; do
        if [ ! -f "$PROJ/$ref" ]; then
            red "FAIL: $(basename "$ex") references $ref — file not found"
            ERRORS=$((ERRORS + 1))
        fi
    done
done

# ── Check 2: Verify referenced functions exist ──
echo "=== Checking function references ==="
# Extract patterns like function_name() or `function_name`
for ex in "$EXERCISES_DIR"/*.md; do
    # Get function references: word() patterns and `word()` patterns
    funcs=$(grep -oE '`[a-z_]+\(\)`|[a-z_]+\(\)' "$ex" | tr -d '`()' | sort -u)
    for func in $funcs; do
        # Skip common English words that look like functions
        case "$func" in
            hint|predict|verify|compare|design|find|list|read|test|run|check|name|calculate) continue ;;
        esac
        # Search across all .py files
        if ! grep -rq "def $func\|$func" "$PROJ"/*.py 2>/dev/null; then
            red "FAIL: $(basename "$ex") references $func() — not found in any .py"
            ERRORS=$((ERRORS + 1))
        fi
    done
done

# ── Check 3: Verify referenced constants exist ──
echo "=== Checking constant references ==="
for ex in "$EXERCISES_DIR"/*.md; do
    consts=$(grep -oE '`[A-Z][A-Z_]+`' "$ex" | tr -d '`' | sort -u)
    for const in $consts; do
        # Skip well-known non-code constants
        case "$const" in
            NOT|AND|OR|TRUE|FALSE|REPL|JSON|API|CC|TS) continue ;;
        esac
        if ! grep -rq "$const" "$PROJ"/*.py 2>/dev/null && \
           ! grep -rq "$const" "$EXERCISES_DIR/../notes/" 2>/dev/null; then
            red "FAIL: $(basename "$ex") references $const — not found in code or notes"
            ERRORS=$((ERRORS + 1))
        fi
    done
done

# ── Check 4: Verify referenced notes exist ──
echo "=== Checking note references ==="
for ex in "$EXERCISES_DIR"/*.md; do
    notes=$(grep -oE 'notes/[0-9]+-[a-z-]+\.md' "$ex" | sort -u)
    for note in $notes; do
        # Notes are in the package, not the repo
        pkg_note="$EXERCISES_DIR/../notes/$(basename "$note")"
        if [ ! -f "$pkg_note" ]; then
            red "FAIL: $(basename "$ex") references $note — not in package"
            ERRORS=$((ERRORS + 1))
        fi
    done
done

echo ""
if [ "$ERRORS" -gt 0 ]; then
    red "GATE FAIL: $ERRORS broken references in exercises"
    exit 2
else
    green "GATE PASS: all exercise references verified"
    exit 0
fi
