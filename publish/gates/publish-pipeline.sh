#!/usr/bin/env bash
# publish-pipeline.sh — Unified marketing pipeline gate
# Runs platform-specific style gate + shared fact-check gate for each platform.
# CC enforcement pattern: exit 0 = all pass, exit 2 = any fail.
#
# Usage:
#   publish-pipeline.sh --platform xhs --post <file> --images <dir>
#   publish-pipeline.sh --platform substack --post <file>
#   publish-pipeline.sh --platform blog --post <file>
#   publish-pipeline.sh --platform gumroad
#   publish-pipeline.sh --all
#
# Pipeline per platform:
#   1. Persona assignment (who reviews)
#   2. Platform-specific style gate
#   3. verify-claims.sh (shared)
#   4. verify-exercises.sh (gumroad only)
#   5. Verdict: READY TO PUBLISH or BLOCKED

set -uo pipefail

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ── Paths ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJ="$(cd "$SCRIPT_DIR/../.." && pwd)"
PUBLISH_DIR="$PROJ/publish"
GATES_DIR="$SCRIPT_DIR"
GUMROAD_DIR="$PROJ/gumroad-package"

# ── State ──
PLATFORM=""
POST_FILE=""
IMAGES_DIR=""
RUN_ALL=0
TOTAL_GATES=0
PASSED_GATES=0
FAILED_GATES=0
FAILED_PLATFORMS=()

# ── Helpers ──
header() {
  echo ""
  echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${CYAN}${BOLD}  $1${NC}"
  echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
}

section() {
  echo -e "  ${BOLD}$1${NC}"
}

pass() {
  echo -e "  ${GREEN}PASS${NC}  $1"
  PASSED_GATES=$((PASSED_GATES + 1))
  TOTAL_GATES=$((TOTAL_GATES + 1))
}

fail() {
  echo -e "  ${RED}FAIL${NC}  $1"
  FAILED_GATES=$((FAILED_GATES + 1))
  TOTAL_GATES=$((TOTAL_GATES + 1))
}

skip() {
  echo -e "  ${DIM}SKIP${NC}  $1"
}

persona_for() {
  case "$1" in
    xhs)      echo "XiaohongshuReviewer" ;;
    substack)  echo "SubstackReviewer" ;;
    blog)      echo "BlogReviewer" ;;
    gumroad)   echo "GumroadReviewer" ;;
    *)         echo "UnknownReviewer" ;;
  esac
}

# ── Usage ──
usage() {
  echo -e "${BOLD}Usage:${NC}"
  echo "  $(basename "$0") --platform xhs --post <file> --images <dir>"
  echo "  $(basename "$0") --platform substack --post <file>"
  echo "  $(basename "$0") --platform blog --post <file>"
  echo "  $(basename "$0") --platform gumroad"
  echo "  $(basename "$0") --all"
  exit 2
}

# ── Parse args ──
while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform) PLATFORM="$2"; shift 2 ;;
    --post)     POST_FILE="$2"; shift 2 ;;
    --images)   IMAGES_DIR="$2"; shift 2 ;;
    --all)      RUN_ALL=1; shift ;;
    -h|--help)  usage ;;
    *)          echo -e "${RED}Unknown argument: $1${NC}"; usage ;;
  esac
done

if [[ "$RUN_ALL" -eq 0 && -z "$PLATFORM" ]]; then
  echo -e "${RED}Error: --platform or --all required.${NC}"
  usage
fi

# ── Run one platform's pipeline ──
run_platform() {
  local platform="$1"
  local post="$2"
  local images="$3"
  local persona
  persona=$(persona_for "$platform")
  local platform_failed=0

  header "$platform — reviewed by $persona"

  # ── Step 1: Platform-specific style gate ──
  section "[1] Platform style gate"

  case "$platform" in
    xhs)
      if [[ -z "$post" || -z "$images" ]]; then
        fail "XHS requires --post and --images"
        platform_failed=1
      elif [[ ! -f "$post" ]]; then
        fail "Post file not found: $post"
        platform_failed=1
      elif [[ ! -d "$images" ]]; then
        fail "Images directory not found: $images"
        platform_failed=1
      else
        if "$GATES_DIR/pre-publish-xhs.sh" "$post" "$images"; then
          pass "pre-publish-xhs.sh"
        else
          fail "pre-publish-xhs.sh"
          platform_failed=1
        fi
      fi
      ;;

    substack)
      if [[ -z "$post" ]]; then
        fail "Substack requires --post"
        platform_failed=1
      elif [[ ! -f "$post" ]]; then
        fail "Post file not found: $post"
        platform_failed=1
      else
        if "$GATES_DIR/pre-publish-substack.sh" "$post"; then
          pass "pre-publish-substack.sh"
        else
          fail "pre-publish-substack.sh"
          platform_failed=1
        fi
      fi
      ;;

    gumroad)
      local zip="$GUMROAD_DIR/agent-anatomy-course.zip"
      if [[ ! -f "$zip" ]]; then
        fail "Gumroad ZIP not found: $zip"
        platform_failed=1
      else
        pass "ZIP exists: $(basename "$zip") ($(du -h "$zip" | cut -f1 | xargs))"
      fi
      ;;

    blog)
      if [[ -z "$post" ]]; then
        fail "Blog requires --post"
        platform_failed=1
      elif [[ ! -f "$post" ]]; then
        fail "Post file not found: $post"
        platform_failed=1
      else
        # No platform-specific gate for blog yet — existence check only
        skip "No blog style gate yet (existence verified: $(basename "$post"))"
      fi
      ;;

    *)
      fail "Unknown platform: $platform"
      platform_failed=1
      ;;
  esac

  # ── Step 2: Shared fact-check gate ──
  echo ""
  section "[2] Fact-check gate (verify-claims.sh)"

  if "$GATES_DIR/verify-claims.sh"; then
    pass "verify-claims.sh"
  else
    fail "verify-claims.sh"
    platform_failed=1
  fi

  # ── Step 3: Exercise verification (gumroad only) ──
  if [[ "$platform" == "gumroad" ]]; then
    echo ""
    section "[3] Exercise verification (verify-exercises.sh)"

    if "$GATES_DIR/verify-exercises.sh"; then
      pass "verify-exercises.sh"
    else
      fail "verify-exercises.sh"
      platform_failed=1
    fi
  fi

  # ── Platform verdict ──
  echo ""
  if [[ "$platform_failed" -gt 0 ]]; then
    echo -e "  ${RED}${BOLD}$platform verdict: BLOCKED${NC}"
    FAILED_PLATFORMS+=("$platform")
  else
    echo -e "  ${GREEN}${BOLD}$platform verdict: READY TO PUBLISH${NC}"
  fi
}

# ── Main ──
header "PUBLISH PIPELINE"
echo -e "  ${DIM}Project: $PROJ${NC}"
echo -e "  ${DIM}Date:    $(date '+%Y-%m-%d %H:%M')${NC}"

if [[ "$RUN_ALL" -eq 1 ]]; then
  # ── --all mode: check each platform that has content ──

  # XHS
  XHS_POST="$PUBLISH_DIR/xiaohongshu-post-0-v2.md"
  XHS_IMAGES="$PUBLISH_DIR/images/xhs-carousel"
  if [[ -f "$XHS_POST" && -d "$XHS_IMAGES" ]]; then
    run_platform "xhs" "$XHS_POST" "$XHS_IMAGES"
  else
    echo ""
    echo -e "  ${DIM}Skipping XHS: content not found${NC}"
    [[ ! -f "$XHS_POST" ]] && echo -e "    ${DIM}Missing: $XHS_POST${NC}"
    [[ ! -d "$XHS_IMAGES" ]] && echo -e "    ${DIM}Missing: $XHS_IMAGES${NC}"
  fi

  # Substack
  SUBSTACK_POST="$PUBLISH_DIR/substack-issue-0.md"
  if [[ -f "$SUBSTACK_POST" ]]; then
    run_platform "substack" "$SUBSTACK_POST" ""
  else
    echo ""
    echo -e "  ${DIM}Skipping Substack: $SUBSTACK_POST not found${NC}"
  fi

  # Gumroad
  GUMROAD_ZIP="$GUMROAD_DIR/agent-anatomy-course.zip"
  if [[ -f "$GUMROAD_ZIP" ]]; then
    run_platform "gumroad" "" ""
  else
    echo ""
    echo -e "  ${DIM}Skipping Gumroad: $GUMROAD_ZIP not found${NC}"
  fi

  # Blog posts (existence check — no platform gate yet)
  BLOG_POSTS=()
  while IFS= read -r -d '' bp; do
    BLOG_POSTS+=("$bp")
  done < <(find "$PUBLISH_DIR" -maxdepth 1 -name "blog-*.md" -print0 | sort -z)

  if [[ ${#BLOG_POSTS[@]} -gt 0 ]]; then
    echo ""
    section "Blog posts found (${#BLOG_POSTS[@]}):"
    for bp in "${BLOG_POSTS[@]}"; do
      echo -e "    ${GREEN}exists${NC}  $(basename "$bp")"
    done
    echo -e "  ${DIM}No blog style gate yet — existence check only.${NC}"
  else
    echo ""
    echo -e "  ${DIM}Skipping Blog: no blog-*.md files found in $PUBLISH_DIR${NC}"
  fi

else
  # ── Single platform mode ──
  run_platform "$PLATFORM" "$POST_FILE" "$IMAGES_DIR"
fi

# ── Final Report ──
header "FINAL REPORT"

echo -e "  Gates run:    ${BOLD}$TOTAL_GATES${NC}"
echo -e "  Passed:       ${GREEN}${BOLD}$PASSED_GATES${NC}"
echo -e "  Failed:       ${RED}${BOLD}$FAILED_GATES${NC}"
echo ""

if [[ ${#FAILED_PLATFORMS[@]} -gt 0 ]]; then
  echo -e "${RED}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${RED}${BOLD}║  PIPELINE VERDICT: BLOCKED                               ║${NC}"
  echo -e "${RED}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "  ${RED}Blocked platforms: ${FAILED_PLATFORMS[*]}${NC}"
  echo -e "  ${YELLOW}Fix all failures above, then re-run.${NC}"
  echo ""
  exit 2
elif [[ "$TOTAL_GATES" -eq 0 ]]; then
  echo -e "${YELLOW}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${YELLOW}${BOLD}║  PIPELINE VERDICT: NO CONTENT FOUND                      ║${NC}"
  echo -e "${YELLOW}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "  ${YELLOW}No publishable content detected. Create content first.${NC}"
  echo ""
  exit 2
else
  echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}${BOLD}║  PIPELINE VERDICT: READY TO PUBLISH                      ║${NC}"
  echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
  echo ""
  exit 0
fi
