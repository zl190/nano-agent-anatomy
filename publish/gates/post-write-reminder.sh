#!/bin/bash
# Post-write reminder — fires after writing to publish/
# Doesn't block (exit 0), but injects reminder into context
# CC pattern: the compactor gets "CRITICAL: Respond with TEXT ONLY"
# We get "CRITICAL: This file needs QC before publishing"

FILE_PATH=$(jq -r '.tool_input.file_path // empty' 2>/dev/null < /dev/stdin || true)

# Only fire for files in publish/
case "$FILE_PATH" in
    */publish/blog-*|*/publish/substack-*|*/publish/xiaohongshu-*|*/publish/gumroad-*)
        echo "⚠️  REMINDER: $FILE_PATH was modified. Before publishing:"
        echo "   1. Does model.md exist? (projection source of truth)"
        echo "   2. Has this been QC'd by the channel-specific persona?"
        echo "   3. Banned word scan passed?"
        echo "   Pattern: Generate → QC (independent context) → Publish"
        ;;
esac

exit 0
