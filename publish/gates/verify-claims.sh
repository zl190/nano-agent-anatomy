#!/usr/bin/env bash
# verify-claims.sh — Fact-check gate for model.md claims
#
# Reads claim registry below, verifies for each claim:
#   1. Source file exists
#   2. Key evidence terms are grep-able in the source
#
# Inspired by research-institute 事实确认表 pattern:
#   每条 claim → 状态(已验证/待审核/需修正) → 来源 → 说明
#   Gate condition: 需修正=0
#
# Exit 0 = pass, Exit 2 = fail (CC enforcement pattern)
# Usage: verify-claims.sh [model.md path]

set -uo pipefail

PROJ="$(cd "$(dirname "$0")/../.." && pwd)"
NOTES_DIR="$PROJ/gumroad-package/agent-anatomy-course/notes"
if [ ! -d "$NOTES_DIR" ]; then
  NOTES_DIR="$HOME/Developer/personal/nano-agent-anatomy-notes-full/notes"
fi

red()   { printf '\033[1;31m%s\033[0m\n' "$1"; }
green() { printf '\033[1;32m%s\033[0m\n' "$1"; }
yellow(){ printf '\033[1;33m%s\033[0m\n' "$1"; }

VERIFIED=0
NEEDS_FIX=0
PENDING=0
TOTAL=0

# ── verify_claim: check one claim ──
# Args: claim_id, claim_label, source_file, evidence_terms (comma-separated)
verify_claim() {
  local cid="$1"
  local label="$2"
  local src="$3"
  local evidence="$4"
  local status="已验证"
  local note=""

  TOTAL=$((TOTAL + 1))

  # Step 1: Find source file
  local src_path=""
  if [ -f "$PROJ/$src" ]; then
    src_path="$PROJ/$src"
  elif [ -f "$NOTES_DIR/$(basename "$src")" ]; then
    src_path="$NOTES_DIR/$(basename "$src")"
  else
    status="需修正"
    note="source missing: $src"
  fi

  # Step 2: Grep evidence terms
  if [ "$status" = "已验证" ] && [ -n "$src_path" ]; then
    local missing=""
    IFS=',' read -ra terms <<< "$evidence"
    for term in "${terms[@]}"; do
      term=$(echo "$term" | xargs)
      if ! grep -qiE "$term" "$src_path" 2>/dev/null; then
        missing="$missing $term"
      fi
    done
    if [ -n "$missing" ]; then
      status="待审核"
      note="missing:${missing}"
    else
      note="${#terms[@]} terms OK"
    fi
  fi

  # Step 3: Print and tally
  case "$status" in
    已验证) printf "  \033[32m%-4s\033[0m %-40s \033[32m%s\033[0m  %s\n" "$cid" "${label:0:40}" "$status" "$note"
            VERIFIED=$((VERIFIED + 1)) ;;
    待审核) printf "  \033[33m%-4s\033[0m %-40s \033[33m%s\033[0m  %s\n" "$cid" "${label:0:40}" "$status" "$note"
            PENDING=$((PENDING + 1)) ;;
    需修正) printf "  \033[31m%-4s\033[0m %-40s \033[31m%s\033[0m  %s\n" "$cid" "${label:0:40}" "$status" "$note"
            NEEDS_FIX=$((NEEDS_FIX + 1)) ;;
  esac
}

echo ""
echo "═══ 事实确认表 — model.md claims ═══"
echo ""

# ── Claim Registry ──
# Format: verify_claim ID "label" "source_file" "term1,term2,..."

verify_claim C1 "Experiment: free-form wins 6-1" \
  "experiment/report/experiment-report.md" \
  "6-1,v1 preferred,pattern depth,actionability"

verify_claim C2 "Curriculum gap: 45 lectures, 0 compression" \
  "notes/00-source-validation-audit.md" \
  "12 lectures,21 lectures,context compression,Berkeley"

verify_claim C3 "Credence good: 4 Berkeley F25 lectures" \
  "notes/00-source-validation-audit.md" \
  "Bavor,Wang,Jiao,Brown"

verify_claim C4 "Context pollution: novel proposal" \
  "notes/09-context-pollution-rewind.md" \
  "correction,softmax,lost.in.the.middle"

verify_claim C5 "Compaction: LLM vs deterministic" \
  "notes/03-context.md" \
  "compact,LLM,deterministic,claw-code"

verify_claim C6 "Degradation: 3 mechanisms + threshold" \
  "notes/03-context.md" \
  "softmax,lost in the middle,degradation"

verify_claim C7 "Correction-aware microcompact (context_v4)" \
  "context_v4.py" \
  "detect_correction,correction_microcompact"

verify_claim C8 "SOP v3 dual-channel design" \
  "experiment/report/experiment-report.md" \
  "v3,extraction,interpretation,cheaper model"

verify_claim C9 "4-source cross-validation discrepancies" \
  "notes/00-source-validation-audit.md" \
  "compaction,agent spawning,permissions,memory"

echo ""
echo "── Summary: $TOTAL claims  已验证=$VERIFIED  待审核=$PENDING  需修正=$NEEDS_FIX ──"
echo ""

if [ "$NEEDS_FIX" -gt 0 ]; then
  red "GATE FAIL: $NEEDS_FIX claims — source file missing"
  exit 2
elif [ "$PENDING" -gt 0 ]; then
  yellow "GATE WARN: $PENDING claims — evidence terms not found in source (manual review)"
  exit 0
else
  green "GATE PASS: all $TOTAL claims verified"
  exit 0
fi
