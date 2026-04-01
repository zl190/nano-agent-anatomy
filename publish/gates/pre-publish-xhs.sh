#!/bin/bash
# Pre-publish gate for 小红书 (Xiaohongshu) — platform-specific checks
# CC pattern: physical enforcement > prompts. Exit 2 = block.
#
# Checks:
#   1. Image count: 6-10 images (carousel format)
#   2. Image ratio: 3:5 vertical (e.g., 1440x2400)
#   3. Text word count: 50-150 Chinese characters
#   4. No banned words
#   5. Has emoji: at least 2 emoji in text
#   6. Has CTA (call to action)
#
# Usage: pre-publish-xhs.sh <post-markdown-file> <images-directory>

set -euo pipefail

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

ERRORS=()
WARNINGS=()

# ── Usage ──
if [ $# -lt 2 ]; then
    echo -e "${RED}Usage: $0 <post-markdown-file> <images-directory>${RESET}" >&2
    echo "  post-markdown-file : Markdown file containing the post text" >&2
    echo "  images-directory   : Directory containing carousel images (PNG)" >&2
    exit 2
fi

POST_FILE="$1"
IMAGES_DIR="$2"

if [ ! -f "$POST_FILE" ]; then
    echo -e "${RED}Error: Post file '$POST_FILE' does not exist.${RESET}" >&2
    exit 2
fi

if [ ! -d "$IMAGES_DIR" ]; then
    echo -e "${RED}Error: Images directory '$IMAGES_DIR' does not exist.${RESET}" >&2
    exit 2
fi

# Read post text (strip markdown frontmatter if present)
POST_TEXT=$(sed '/^---$/,/^---$/d' "$POST_FILE")

echo -e "${CYAN}${BOLD}═══ 小红书 Pre-Publish Gate ═══${RESET}"
echo -e "${CYAN}Post:   ${POST_FILE}${RESET}"
echo -e "${CYAN}Images: ${IMAGES_DIR}${RESET}"
echo ""

# ── Gate 1: Image count (6-10 for carousel) ──
echo -e "${BOLD}[1/6] Image count...${RESET}"
# Count PNG and JPG images
IMAGE_FILES=()
while IFS= read -r -d '' img; do
    IMAGE_FILES+=("$img")
done < <(find "$IMAGES_DIR" -maxdepth 1 \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) -print0 | sort -z)

IMAGE_COUNT=${#IMAGE_FILES[@]}

if [ "$IMAGE_COUNT" -lt 6 ]; then
    ERRORS+=("Image count: ${IMAGE_COUNT} images found. Minimum 6 required for carousel.")
elif [ "$IMAGE_COUNT" -gt 10 ]; then
    ERRORS+=("Image count: ${IMAGE_COUNT} images found. Maximum 10 allowed.")
else
    echo -e "  ${GREEN}OK${RESET} — ${IMAGE_COUNT} images (6-10 range)"
fi

# ── Gate 2: Image ratio — must be 3:5 vertical ──
echo -e "${BOLD}[2/6] Image ratio (3:5 vertical)...${RESET}"
# Use sips (macOS built-in) to check dimensions
RATIO_TOLERANCE=0.02  # Allow 2% deviation from 0.6 (3/5)
TARGET_RATIO="0.600"

for img in "${IMAGE_FILES[@]}"; do
    BASENAME=$(basename "$img")
    WIDTH=$(sips -g pixelWidth "$img" 2>/dev/null | awk '/pixelWidth/{print $2}')
    HEIGHT=$(sips -g pixelHeight "$img" 2>/dev/null | awk '/pixelHeight/{print $2}')

    if [ -z "$WIDTH" ] || [ -z "$HEIGHT" ]; then
        ERRORS+=("Image ratio: Cannot read dimensions of '${BASENAME}'.")
        continue
    fi

    if [ "$HEIGHT" -eq 0 ]; then
        ERRORS+=("Image ratio: '${BASENAME}' has zero height.")
        continue
    fi

    # Calculate ratio as width/height — should be 3/5 = 0.6
    ACTUAL_RATIO=$(awk "BEGIN {printf \"%.3f\", ${WIDTH}/${HEIGHT}}")
    DEVIATION=$(awk "BEGIN {d = ${ACTUAL_RATIO} - ${TARGET_RATIO}; print (d < 0 ? -d : d)}")

    if awk "BEGIN {exit !(${DEVIATION} > ${RATIO_TOLERANCE})}"; then
        ERRORS+=("Image ratio: '${BASENAME}' is ${WIDTH}x${HEIGHT} (ratio ${ACTUAL_RATIO}). Expected 3:5 vertical (ratio ~0.600).")
    else
        echo -e "  ${GREEN}OK${RESET} — ${BASENAME}: ${WIDTH}x${HEIGHT} (ratio ${ACTUAL_RATIO})"
    fi
done

# ── Gate 3: Chinese character count (50-150) ──
echo -e "${BOLD}[3/6] Chinese character count (50-150)...${RESET}"

# Count CJK characters (Unicode range \u4e00-\u9fff plus common extensions)
# Strip markdown syntax first, then count Chinese chars
CLEAN_TEXT=$(echo "$POST_TEXT" | sed -E 's/[#*_`\[\]()>-]//g')
CHINESE_CHAR_COUNT=$(echo "$CLEAN_TEXT" | perl -CS -ne 'while (/[\x{4e00}-\x{9fff}\x{3400}-\x{4dbf}\x{f900}-\x{faff}]/g) { $c++ } END { print $c // 0 }')

if [ "$CHINESE_CHAR_COUNT" -lt 50 ]; then
    ERRORS+=("Character count: ${CHINESE_CHAR_COUNT} Chinese characters. Minimum 50 required.")
elif [ "$CHINESE_CHAR_COUNT" -gt 150 ]; then
    ERRORS+=("Character count: ${CHINESE_CHAR_COUNT} Chinese characters. Maximum 150 allowed.")
else
    echo -e "  ${GREEN}OK${RESET} — ${CHINESE_CHAR_COUNT} Chinese characters"
fi

# ── Gate 4: Banned words ──
echo -e "${BOLD}[4/6] Banned words scan...${RESET}"

BANNED_WORDS=("泄露" "破解" "leaked" "hacked")
FOUND_BANNED=()

for word in "${BANNED_WORDS[@]}"; do
    if echo "$POST_TEXT" | grep -qi "$word"; then
        FOUND_BANNED+=("$word")
    fi
done

if [ ${#FOUND_BANNED[@]} -gt 0 ]; then
    ERRORS+=("Banned words found: ${FOUND_BANNED[*]}. Remove before publishing.")
else
    echo -e "  ${GREEN}OK${RESET} — no banned words"
fi

# ── Gate 5: Emoji count (at least 2) ──
echo -e "${BOLD}[5/6] Emoji count (>=2)...${RESET}"

# Count emoji using perl — covers most common emoji ranges
EMOJI_COUNT=$(echo "$POST_TEXT" | perl -CS -ne '
    while (/[\x{1F300}-\x{1F9FF}\x{2600}-\x{27BF}\x{FE00}-\x{FE0F}\x{1FA00}-\x{1FA6F}\x{1FA70}-\x{1FAFF}\x{2702}-\x{27B0}\x{231A}-\x{23F3}\x{2934}-\x{2935}\x{25AA}-\x{25FE}\x{2B05}-\x{2B1B}\x{200D}\x{20E3}]/g) { $c++ }
    END { print $c // 0 }
')

if [ "$EMOJI_COUNT" -lt 2 ]; then
    ERRORS+=("Emoji count: ${EMOJI_COUNT} emoji found. At least 2 required for 小红书 engagement.")
else
    echo -e "  ${GREEN}OK${RESET} — ${EMOJI_COUNT} emoji found"
fi

# ── Gate 6: CTA (call to action) ──
echo -e "${BOLD}[6/6] Call to action...${RESET}"

CTA_WORDS=("评论" "关注" "点赞" "收藏" "转发" "留言" "私信" "双击" "分享" "互关")
CTA_FOUND=()

for cta in "${CTA_WORDS[@]}"; do
    if echo "$POST_TEXT" | grep -q "$cta"; then
        CTA_FOUND+=("$cta")
    fi
done

if [ ${#CTA_FOUND[@]} -eq 0 ]; then
    ERRORS+=("No CTA found. Include at least one of: ${CTA_WORDS[*]}")
else
    echo -e "  ${GREEN}OK${RESET} — CTA found: ${CTA_FOUND[*]}"
fi

# ── Verdict ──
echo ""

if [ ${#ERRORS[@]} -gt 0 ]; then
    echo -e "${RED}${BOLD}╔══════════════════════════════════════════════╗${RESET}"
    echo -e "${RED}${BOLD}║  小红书 PRE-PUBLISH GATE: BLOCKED            ║${RESET}"
    echo -e "${RED}${BOLD}╚══════════════════════════════════════════════╝${RESET}"
    for err in "${ERRORS[@]}"; do
        echo -e "  ${RED}✗${RESET} $err"
    done
    echo ""
    echo -e "${YELLOW}Fix all issues above, then retry.${RESET}"
    exit 2
fi

echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║  小红書 PRE-PUBLISH GATE: PASSED             ║${RESET}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════╝${RESET}"
exit 0
