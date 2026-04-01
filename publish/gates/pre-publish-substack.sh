#!/bin/bash
# Pre-publish gate for Substack newsletter posts
# CC enforcement pattern: exit 2 = block, exit 0 = allow
#
# Usage: pre-publish-substack.sh <post-markdown-file>
#
# Checks:
#   1. Has a title (first line starts with #)
#   2. Word count: 800-3000 (Substack sweet spot)
#   3. Has at least one section heading (## or ###)
#   4. No banned words
#   5. Has a CTA / subscription hook
#   6. No raw code blocks longer than 20 lines
#   7. All links are absolute URLs

set -euo pipefail

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ── Usage ──
if [ $# -lt 1 ]; then
    echo -e "${RED}${BOLD}Usage:${NC} pre-publish-substack.sh <post-markdown-file>"
    exit 2
fi

FILE="$1"

if [ ! -f "$FILE" ]; then
    echo -e "${RED}${BOLD}ERROR:${NC} File not found: $FILE"
    exit 2
fi

ERRORS=()
WARNINGS=()

# ── Gate 1: Has a title (first line starts with #) ──
FIRST_LINE=$(head -n 1 "$FILE")
if ! echo "$FIRST_LINE" | grep -qE '^# '; then
    ERRORS+=("${RED}[TITLE]${NC} First line must start with '# ' (H1 title). Got: '${FIRST_LINE:0:60}'")
fi

# ── Gate 2: Word count 800-3000 ──
# Strip markdown formatting for accurate word count
WORD_COUNT=$(sed 's/```[^`]*```//g; s/`[^`]*`//g; s/!\[.*\](.*)//' "$FILE" | wc -w | tr -d ' ')
if [ "$WORD_COUNT" -lt 800 ]; then
    ERRORS+=("${RED}[WORD COUNT]${NC} Too short: ${WORD_COUNT} words (minimum 800). Substack readers expect substance.")
elif [ "$WORD_COUNT" -gt 3000 ]; then
    ERRORS+=("${RED}[WORD COUNT]${NC} Too long: ${WORD_COUNT} words (maximum 3000). Substack readers drop off after 3000.")
else
    WARNINGS+=("${GREEN}[WORD COUNT]${NC} ${WORD_COUNT} words — within Substack sweet spot (800-3000)")
fi

# ── Gate 3: Has at least one section heading (## or ###) ──
HEADING_COUNT=$(grep -cE '^#{2,3} ' "$FILE" || true)
if [ "$HEADING_COUNT" -eq 0 ]; then
    ERRORS+=("${RED}[STRUCTURE]${NC} No section headings found. Add at least one ## or ### heading for scannability.")
fi

# ── Gate 4: Banned words ──
BANNED_WORDS=("research-institute" "research-lab" "Hong Lab")
CONTENT=$(cat "$FILE")
for word in "${BANNED_WORDS[@]}"; do
    if echo "$CONTENT" | grep -qi "$word"; then
        LINE_NUM=$(grep -ni "$word" "$FILE" | head -1 | cut -d: -f1)
        ERRORS+=("${RED}[BANNED]${NC} Found '${word}' at line ${LINE_NUM}. Remove before publishing.")
    fi
done

# ── Gate 5: CTA / subscription hook ──
CTA_PATTERNS="subscribe|订阅|next issue|下一期"
if ! echo "$CONTENT" | grep -qiE "$CTA_PATTERNS"; then
    ERRORS+=("${RED}[CTA]${NC} No subscription hook found. Include one of: 'subscribe', '订阅', 'next issue', '下一期'.")
fi

# ── Gate 6: No code blocks longer than 20 lines ──
# Parse code fences and count lines between them
IN_CODE=0
CODE_LINE_COUNT=0
CODE_BLOCK_START=0
LINE_NUM=0
while IFS= read -r line; do
    LINE_NUM=$((LINE_NUM + 1))
    if echo "$line" | grep -qE '^```'; then
        if [ "$IN_CODE" -eq 0 ]; then
            IN_CODE=1
            CODE_LINE_COUNT=0
            CODE_BLOCK_START=$LINE_NUM
        else
            IN_CODE=0
            if [ "$CODE_LINE_COUNT" -gt 20 ]; then
                ERRORS+=("${RED}[CODE BLOCK]${NC} Code block at line ${CODE_BLOCK_START} is ${CODE_LINE_COUNT} lines (max 20). Substack renders code poorly — trim or use a gist link.")
            fi
        fi
    elif [ "$IN_CODE" -eq 1 ]; then
        CODE_LINE_COUNT=$((CODE_LINE_COUNT + 1))
    fi
done < "$FILE"

# ── Gate 7: All links are absolute URLs ──
# Match markdown links [text](url) where url doesn't start with http://, https://, or mailto:
# Exclude anchor links (#section) and image alt texts
RELATIVE_LINKS=$(grep -noE '\[([^]]*)\]\(([^)]+)\)' "$FILE" | grep -vE '\]\((https?://|mailto:|#)' || true)
if [ -n "$RELATIVE_LINKS" ]; then
    FIRST_OFFENDER=$(echo "$RELATIVE_LINKS" | head -1)
    OFFENDER_LINE=$(echo "$FIRST_OFFENDER" | cut -d: -f1)
    OFFENDER_COUNT=$(echo "$RELATIVE_LINKS" | wc -l | tr -d ' ')
    ERRORS+=("${RED}[LINKS]${NC} ${OFFENDER_COUNT} relative link(s) found (first at line ${OFFENDER_LINE}). All links must be absolute URLs for Substack.")
fi

# ── Verdict ──
echo ""
echo -e "${CYAN}${BOLD}━━━ Substack Pre-Publish Gate ━━━${NC}"
echo -e "${CYAN}File:${NC} $FILE"
echo ""

# Print passing checks
if [ ${#WARNINGS[@]} -gt 0 ]; then
    for warn in "${WARNINGS[@]}"; do
        echo -e "  $warn"
    done
fi

if [ ${#ERRORS[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}${BOLD}╔══════════════════════════════════════════╗${NC}"
    echo -e "${RED}${BOLD}║  SUBSTACK GATE: BLOCKED (${#ERRORS[@]} issue(s))     ║${NC}"
    echo -e "${RED}${BOLD}╚══════════════════════════════════════════╝${NC}"
    echo ""
    for err in "${ERRORS[@]}"; do
        echo -e "  ✗ $err"
    done
    echo ""
    echo -e "${YELLOW}Fix all issues above, then retry.${NC}"
    exit 2
fi

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║  SUBSTACK GATE: ALL CHECKS PASSED        ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""
exit 0
