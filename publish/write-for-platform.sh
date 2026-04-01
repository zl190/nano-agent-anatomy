#!/usr/bin/env bash
# write-for-platform.sh — 平台写作管线入口
#
# Usage: ./write-for-platform.sh <platform> <model-file> [output-file]
#
# Platforms: xhs, substack, devto
# model-file: source material (notes, findings, data)
# output-file: defaults to publish/<platform>-draft.md
#
# Pipeline: load persona → spawn writer → gate → render (if applicable)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STYLE_DIR="$HOME/.claude/memory/knowledge/output-styles"

# ── Args ──────────────────────────────────────────────────────
PLATFORM="${1:?Usage: $0 <platform> <model-file> [output-file]}"
MODEL_FILE="${2:?Usage: $0 <platform> <model-file> [output-file]}"
OUTPUT_FILE="${3:-$SCRIPT_DIR/${PLATFORM}-draft.md}"

# ── Platform config ───────────────────────────────────────────
case "$PLATFORM" in
  xhs)
    STYLE_GUIDE="$STYLE_DIR/xhs-content.md"
    GATE="$SCRIPT_DIR/gates/pre-publish-xhs.sh"
    RENDERER="$SCRIPT_DIR/render_xhs.py"
    RENDER_CMD="uv run --python 3.12 --with markdown --with pyyaml --with playwright --with pygments python $RENDERER $OUTPUT_FILE -o $SCRIPT_DIR/images/xhs-carousel -t notion-tech"
    ;;
  substack)
    STYLE_GUIDE="$STYLE_DIR/blog-content.md"
    GATE="$SCRIPT_DIR/gates/pre-publish-substack.sh"
    RENDERER=""
    RENDER_CMD=""
    ;;
  devto)
    STYLE_GUIDE="$STYLE_DIR/blog-content.md"
    GATE=""
    RENDERER=""
    RENDER_CMD=""
    ;;
  *)
    echo "Unknown platform: $PLATFORM"
    echo "Supported: xhs, substack, devto"
    exit 1
    ;;
esac

# ── Validate ──────────────────────────────────────────────────
if [ ! -f "$MODEL_FILE" ]; then
  echo "Error: model file not found: $MODEL_FILE"
  exit 1
fi

if [ ! -f "$STYLE_GUIDE" ]; then
  echo "Error: style guide not found: $STYLE_GUIDE"
  exit 1
fi

# ── Build writer prompt ──────────────────────────────────────
STYLE_CONTENT=$(cat "$STYLE_GUIDE")
MODEL_CONTENT=$(cat "$MODEL_FILE")

WRITER_PROMPT="你是一个内容写手。严格按照下面的风格指南写作。

=== 风格指南 ===
$STYLE_CONTENT

=== 源材料 ===
$MODEL_CONTENT

=== 任务 ===
根据源材料，按照风格指南为 $PLATFORM 平台写一篇内容。
输出到: $OUTPUT_FILE

要求：
1. 严格遵守persona和语气规则
2. 不要添加源材料里没有的事实
3. 写完后自己跑一遍QC清单，有不通过的自己改
4. 最终内容写入 $OUTPUT_FILE"

# ── Spawn writer ──────────────────────────────────────────────
echo "=== Platform: $PLATFORM ==="
echo "=== Style guide: $STYLE_GUIDE ==="
echo "=== Model: $MODEL_FILE ==="
echo "=== Output: $OUTPUT_FILE ==="
echo ""
echo "Spawning writer agent..."

claude -p "$WRITER_PROMPT" --allowedTools "Read,Write,Edit,Bash" 2>&1

# ── Gate ──────────────────────────────────────────────────────
if [ -n "${GATE:-}" ] && [ -f "$GATE" ]; then
  echo ""
  echo "=== Running gate: $GATE ==="
  bash "$GATE" "$OUTPUT_FILE" 2>&1
  GATE_EXIT=$?
  if [ $GATE_EXIT -ne 0 ]; then
    echo "GATE FAILED (exit $GATE_EXIT). Fix issues before rendering."
    exit $GATE_EXIT
  fi
  echo "Gate passed."
fi

# ── Render ────────────────────────────────────────────────────
if [ -n "${RENDER_CMD:-}" ]; then
  echo ""
  echo "=== Rendering ==="
  eval "$RENDER_CMD" 2>&1
fi

echo ""
echo "=== Done ==="
echo "Output: $OUTPUT_FILE"
