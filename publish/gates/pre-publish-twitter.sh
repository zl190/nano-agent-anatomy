#!/usr/bin/env bash
# Pre-publish gate for Twitter/X threads.
# Usage: bash pre-publish-twitter.sh <thread-file.md>
set -euo pipefail

THREAD_FILE="${1:?Usage: pre-publish-twitter.sh <thread-file.md>}"
FAIL=0

err() { echo "FAIL: $1"; FAIL=1; }
warn() { echo "WARN: $1"; }

echo "=== Twitter pre-publish gate: ${THREAD_FILE} ==="

# Split tweets by "**Tweet N" markers
TWEET_COUNT=$(grep -c '^\*\*Tweet' "$THREAD_FILE" || true)

echo ""
echo "--- Thread structure ---"
echo "Tweets in thread: $TWEET_COUNT"

if [ "$TWEET_COUNT" -lt 2 ]; then err "Thread needs at least 2 tweets"; fi
if [ "$TWEET_COUNT" -gt 15 ]; then warn "Thread is long ($TWEET_COUNT tweets) — engagement drops after 8"; fi

echo ""
echo "--- Per-tweet length check ---"

# Extract each tweet and check length
CURRENT_TWEET=""
TWEET_NUM=0
OVER_LIMIT=0

while IFS= read -r line; do
  if echo "$line" | grep -q '^\*\*Tweet'; then
    # Check previous tweet
    if [ -n "$CURRENT_TWEET" ] && [ "$TWEET_NUM" -gt 0 ]; then
      LEN=${#CURRENT_TWEET}
      if [ "$LEN" -gt 280 ]; then
        err "Tweet $TWEET_NUM is $LEN chars (max 280)"
        OVER_LIMIT=$((OVER_LIMIT + 1))
      else
        echo "  Tweet $TWEET_NUM: $LEN/280 chars"
      fi
    fi
    TWEET_NUM=$((TWEET_NUM + 1))
    CURRENT_TWEET=""
  else
    # Skip empty lines at start of tweet
    if [ -n "$line" ] || [ -n "$CURRENT_TWEET" ]; then
      CURRENT_TWEET="${CURRENT_TWEET}${line}"
    fi
  fi
done < "$THREAD_FILE"

# Check last tweet
if [ -n "$CURRENT_TWEET" ] && [ "$TWEET_NUM" -gt 0 ]; then
  LEN=${#CURRENT_TWEET}
  if [ "$LEN" -gt 280 ]; then
    err "Tweet $TWEET_NUM is $LEN chars (max 280)"
  else
    echo "  Tweet $TWEET_NUM: $LEN/280 chars"
  fi
fi

echo ""
echo "--- Content checks ---"

# No local paths
if grep -q '/Users/' "$THREAD_FILE"; then err "Local file paths found"; fi

# No research-institute/research-lab
if grep -qi 'research-institute\|research-lab' "$THREAD_FILE"; then err "Work project names in public content"; fi

# Has CTA (link)
if ! grep -q 'github.com\|gumroad.com\|buymeacoffee.com' "$THREAD_FILE"; then
  warn "No link/CTA found in thread"
fi

# Hashtag count
HASHTAG_COUNT=$(grep -co '#[A-Za-z]' "$THREAD_FILE" || true)
if [ "$HASHTAG_COUNT" -gt 10 ]; then warn "Too many hashtags ($HASHTAG_COUNT) — looks spammy"; fi

echo ""
if [ "$FAIL" -ne 0 ]; then
  echo "=== GATE FAILED ==="
  exit 1
else
  echo "=== GATE PASSED — ready to post ==="
  exit 0
fi
