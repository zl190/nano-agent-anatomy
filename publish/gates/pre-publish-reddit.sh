#!/usr/bin/env bash
# Pre-publish gate for Reddit posts.
# Usage: bash pre-publish-reddit.sh <post-file.md> <subreddit>
set -euo pipefail

POST_FILE="${1:?Usage: pre-publish-reddit.sh <file> <subreddit>}"
SUBREDDIT="${2:?Usage: pre-publish-reddit.sh <file> <subreddit>}"
FAIL=0

err() { echo "FAIL: $1"; FAIL=1; }
warn() { echo "WARN: $1"; }

echo "=== Reddit pre-publish gate: ${POST_FILE} → r/${SUBREDDIT} ==="

# Extract title (first # heading or first line)
TITLE=$(grep -m1 '^## ' "$POST_FILE" | sed 's/^## //' || head -1 "$POST_FILE")
TITLE_LEN=${#TITLE}

# Extract body (everything after the first heading)
BODY=$(tail -n +2 "$POST_FILE")
BODY_LEN=${#BODY}

echo ""
echo "--- Format checks ---"
echo "Title ($TITLE_LEN chars): $TITLE"

if [ "$TITLE_LEN" -lt 5 ]; then err "Title too short (<5 chars)"; fi
if [ "$TITLE_LEN" -gt 300 ]; then err "Title too long (>300 chars)"; fi
if [ "$BODY_LEN" -lt 50 ]; then err "Body too short (<50 chars)"; fi
if [ "$BODY_LEN" -gt 40000 ]; then err "Body too long (>40000 chars)"; fi

echo ""
echo "--- Content checks ---"

# No local paths
if grep -q '/Users/' "$POST_FILE"; then err "Local file paths found"; fi

# Has a repo link
if ! grep -q 'github.com/zl190/nano-agent-anatomy' "$POST_FILE"; then
  warn "No repo link found"
fi

# No research-institute/research-lab names
if grep -qi 'research-institute\|research-lab' "$POST_FILE"; then err "Work project names found in public content"; fi

# AI smell check — common AI-generated phrases
AI_SMELL=$(grep -ci "it.s worth noting\|in conclusion\|comprehensive\|delve\|tapestry\|landscape" "$POST_FILE" || true)
if [ "$AI_SMELL" -gt 2 ]; then err "AI smell score too high ($AI_SMELL matches)"; fi

# Specific numbers should have context
NUM_COUNT=$(grep -co '[0-9]\{3,\}' "$POST_FILE" || true)
if [ "$NUM_COUNT" -gt 10 ]; then warn "Many bare numbers ($NUM_COUNT) — ensure each is sourced"; fi

echo ""
if [ "$FAIL" -ne 0 ]; then
  echo "=== GATE FAILED ==="
  exit 1
else
  echo "=== GATE PASSED — ready to post to r/${SUBREDDIT} ==="
  exit 0
fi
