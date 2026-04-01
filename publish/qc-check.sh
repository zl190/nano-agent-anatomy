#!/bin/bash
# Publishing QC gate. Run before publishing to any channel.
# Usage: ./publish/qc-check.sh <channel> <file>
# Channels: substack, xiaohongshu, gumroad

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

CHANNEL=$1
FILE=$2
FAIL=0

if [ -z "$CHANNEL" ] || [ -z "$FILE" ]; then
    echo "Usage: ./publish/qc-check.sh <channel> <file>"
    echo "Channels: substack, xiaohongshu, gumroad"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo -e "${RED}FAIL:${NC} File not found: $FILE"
    exit 1
fi

WORDS=$(wc -w < "$FILE" | tr -d ' ')
echo "Channel: $CHANNEL | File: $FILE | Words: $WORDS"
echo "---"

# === Universal checks ===

# AI smell patterns
AI_SMELL=$(grep -ciE "(it.s worth noting|moreover|in conclusion|furthermore|it.s important to|that said|comprehensive|game.changing|revolutionary|unlock|unleash)" "$FILE")
if [ "$AI_SMELL" -gt 0 ]; then
    echo -e "${RED}FAIL:${NC} $AI_SMELL AI smell pattern(s) detected"
    grep -niE "(it.s worth noting|moreover|in conclusion|furthermore|it.s important to|that said|comprehensive|game.changing|revolutionary|unlock|unleash)" "$FILE"
    FAIL=1
else
    echo -e "${GREEN}PASS:${NC} No AI smell"
fi

# Source citations (links or file paths)
CITATIONS=$(grep -cE "(http|\.ts|\.rs|\.py|L[0-9]|lecture|ccleaks|Alex Kim)" "$FILE")
if [ "$CITATIONS" -eq 0 ]; then
    echo -e "${RED}FAIL:${NC} No source citations found"
    FAIL=1
else
    echo -e "${GREEN}PASS:${NC} $CITATIONS citation(s) found"
fi

# CTA check (repo link or subscribe)
CTA=$(grep -cE "(github\.com|subscribe|链接|repo)" "$FILE")
if [ "$CTA" -eq 0 ]; then
    echo -e "${YELLOW}WARN:${NC} No CTA (repo link, subscribe prompt) found"
fi

# === Channel-specific checks ===

case $CHANNEL in
    substack)
        if [ "$WORDS" -lt 800 ]; then
            echo -e "${RED}FAIL:${NC} Too short ($WORDS words, min 800)"
            FAIL=1
        elif [ "$WORDS" -gt 1200 ]; then
            echo -e "${YELLOW}WARN:${NC} Long ($WORDS words, target 800-1200)"
        else
            echo -e "${GREEN}PASS:${NC} Word count OK ($WORDS)"
        fi
        ;;
    xiaohongshu)
        # Chinese character count (rough: chars / 1.5 for mixed content)
        CHARS=$(wc -m < "$FILE" | tr -d ' ')
        if [ "$CHARS" -gt 1500 ]; then
            echo -e "${RED}FAIL:${NC} Too long ($CHARS chars, target ≤1500 for ~300 Chinese words)"
            FAIL=1
        else
            echo -e "${GREEN}PASS:${NC} Length OK ($CHARS chars)"
        fi
        # First real line after title should be a fact
        FIRST_LINE=$(grep -v "^#\|^$\|^##" "$FILE" | head -1)
        echo -e "${YELLOW}CHECK MANUALLY:${NC} First line is fact? → '$FIRST_LINE'"
        ;;
    gumroad)
        # Check for specific deliverable counts
        SPECIFICS=$(grep -cE "[0-9]+ (layer|note|file|line|week)" "$FILE")
        if [ "$SPECIFICS" -eq 0 ]; then
            echo -e "${RED}FAIL:${NC} No specific deliverable counts found"
            FAIL=1
        else
            echo -e "${GREEN}PASS:${NC} $SPECIFICS specific deliverable(s) mentioned"
        fi
        ;;
esac

echo "---"
if [ "$FAIL" -eq 1 ]; then
    echo -e "${RED}QC FAILED. Fix issues before publishing.${NC}"
    exit 1
else
    echo -e "${GREEN}QC PASSED. Ready to publish.${NC}"
    exit 0
fi
