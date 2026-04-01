#!/bin/bash
# Source Reading SOP Experiment: v1 vs v2 Blind Comparison
# Each reader is a separate claude -p call for reliability.
# Usage: ./run-experiment.sh

set -euo pipefail
cd "$(dirname "$0")/.."
EXPERIMENT_DIR="$(pwd)/experiment"
REPO="/Users/zl190/Developer/personal/cc-ts-source"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       Source Reading SOP Experiment (v1 vs v2)          ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Step 1: v1 baseline — 6 readers (serial) + synthesis   ║"
echo "║  Step 2: anonymize (instant)                            ║"
echo "║  Step 3: blind eval                                     ║"
echo "║  Step 4: compile report                                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo "Start: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

mkdir -p "$EXPERIMENT_DIR/v1"

# ============================================================
# File assignments (same as v2, controlled variable)
# ============================================================
declare -a READER_NAMES=(
    "core-runtime"
    "tools-shell-file"
    "ai-mcp-integration"
    "ui-terminal"
    "state-persistence"
    "commands-skills"
)
declare -a READER_FILES=(
    "src/Tool.ts src/QueryEngine.ts src/query.ts src/commands.ts src/history.ts src/setup.ts src/bootstrap/ src/bridge/ src/remote/ src/tasks/ src/state/"
    "src/tools/BashTool/ src/tools/FileReadTool/ src/tools/FileEditTool/ src/tools/FileWriteTool/ src/tools/GlobTool/ src/tools/GrepTool/ src/tools/PowerShellTool/"
    "src/tools/MCPTool/ src/tools/WebFetchTool/ src/tools/WebSearchTool/ src/tools/LSPTool/ src/tools/AgentTool/ src/tools/SkillTool/ src/services/api/ src/services/mcp/"
    "src/components/ src/ink/ src/cli/"
    "src/utils/ src/services/plugins/ src/memdir/ src/state/ src/hooks/"
    "src/commands/ src/skills/ src/plugins/ src/utils/bash/specs/"
)

# ============================================================
# STEP 1: Run v1 Baseline — one claude -p per reader
# ============================================================
echo "━━━ Step 1/4: v1 Baseline Readers ━━━"

for i in 0 1 2 3 4 5; do
    READER_NUM=$((i + 1))
    READER_NAME="${READER_NAMES[$i]}"
    FILES="${READER_FILES[$i]}"
    OUTFILE="$EXPERIMENT_DIR/v1/reader-${READER_NUM}-${READER_NAME}.md"

    if [ -f "$OUTFILE" ] && [ -s "$OUTFILE" ]; then
        echo "  [${READER_NUM}/6] ${READER_NAME} — already exists ($(wc -c < "$OUTFILE" | tr -d ' ') bytes). Skip."
        continue
    fi

    echo -n "  [${READER_NUM}/6] ${READER_NAME} — $(date '+%H:%M:%S') running..."

    # Build file list with full paths
    FILE_LIST=""
    for f in $FILES; do
        FILE_LIST="$FILE_LIST\n- ${REPO}/${f}"
    done

    # v1 SOP prompt — NO JSON, NO persona, NO gate
    PROMPT="You are reading source code. Report on the files assigned to you.

Your assigned files:
$(echo -e "$FILE_LIST")

The codebase is Claude Code (TypeScript, 513K lines).

For each file or group of files, report:
1. Line count
2. Core classes/functions (signature + one sentence)
3. Production insight (what tutorials don't teach)
4. Mapping to patterns we could adopt

Read the files and provide a thorough analysis. Focus on what's architecturally important.

IMPORTANT: When done, save your complete analysis to: ${OUTFILE}"

    claude -p "$PROMPT" \
        --allowedTools 'Read,Write,Bash,Glob,Grep' \
        --model sonnet \
        > "$EXPERIMENT_DIR/v1/reader-${READER_NUM}-log.txt" 2>&1

    if [ -f "$OUTFILE" ] && [ -s "$OUTFILE" ]; then
        SIZE=$(wc -c < "$OUTFILE" | tr -d ' ')
        echo " done (${SIZE} bytes)"
    else
        echo " ⚠ no output file. Check reader-${READER_NUM}-log.txt"
    fi
done

# v1 Synthesis
echo ""
echo -n "  [synth] v1 synthesis — $(date '+%H:%M:%S') running..."
SYNTH_OUT="$EXPERIMENT_DIR/v1/synthesis-v1.md"

if [ -f "$SYNTH_OUT" ] && [ -s "$SYNTH_OUT" ]; then
    echo " already exists. Skip."
else
    # Build reader content references
    READER_REFS=""
    for i in 0 1 2 3 4 5; do
        READER_NUM=$((i + 1))
        READER_NAME="${READER_NAMES[$i]}"
        READER_REFS="$READER_REFS\n- $EXPERIMENT_DIR/v1/reader-${READER_NUM}-${READER_NAME}.md"
    done

    SYNTH_PROMPT="You have 6 reader reports from a source code reading exercise on Claude Code (513K lines TypeScript).

Read ALL 6 reports from these files:
$(echo -e "$READER_REFS")

Synthesize:
1. Cross-cutting patterns (appear in 2+ reports)
2. Architecture summary (3-5 paragraphs for a senior engineer)
3. Most surprising findings

Save your complete synthesis to: ${SYNTH_OUT}"

    claude -p "$SYNTH_PROMPT" \
        --allowedTools 'Read,Write,Glob,Grep' \
        --model opus \
        > "$EXPERIMENT_DIR/v1/synthesis-log.txt" 2>&1

    if [ -f "$SYNTH_OUT" ] && [ -s "$SYNTH_OUT" ]; then
        echo " done ($(wc -c < "$SYNTH_OUT" | tr -d ' ') bytes)"
    else
        echo " ⚠ no synthesis output"
    fi
fi

touch "$EXPERIMENT_DIR/v1/DONE"
echo ""
echo "  ✓ Step 1 complete: $(ls "$EXPERIMENT_DIR/v1"/reader-*.md 2>/dev/null | wc -l | tr -d ' ') reader files + synthesis"

# ============================================================
# STEP 2: Anonymize (no LLM, instant)
# ============================================================
echo ""
echo "━━━ Step 2/4: Anonymize ━━━"
mkdir -p "$EXPERIMENT_DIR/blind/A" "$EXPERIMENT_DIR/blind/B"

COIN=$((RANDOM % 2))
if [ $COIN -eq 0 ]; then V1_LABEL="A"; V2_LABEL="B"; else V1_LABEL="B"; V2_LABEL="A"; fi

# Copy v1 (markdown)
for f in "$EXPERIMENT_DIR/v1"/reader-*.md; do
    [ -f "$f" ] && cp "$f" "$EXPERIMENT_DIR/blind/$V1_LABEL/"
done
[ -f "$EXPERIMENT_DIR/v1/synthesis-v1.md" ] && \
    cp "$EXPERIMENT_DIR/v1/synthesis-v1.md" "$EXPERIMENT_DIR/blind/$V1_LABEL/synthesis.md"

# Copy v2 (JSON)
for f in "$EXPERIMENT_DIR"/reader-*.json; do
    [ -f "$f" ] && cp "$f" "$EXPERIMENT_DIR/blind/$V2_LABEL/"
done
[ -f "$EXPERIMENT_DIR/synthesis-v2-run1.md" ] && \
    cp "$EXPERIMENT_DIR/synthesis-v2-run1.md" "$EXPERIMENT_DIR/blind/$V2_LABEL/synthesis.md"

echo "v1 = $V1_LABEL" > "$EXPERIMENT_DIR/blind/UNBLIND_KEY.txt"
echo "v2 = $V2_LABEL" >> "$EXPERIMENT_DIR/blind/UNBLIND_KEY.txt"
echo "  ✓ v1→$V1_LABEL, v2→$V2_LABEL (key saved)"

# ============================================================
# STEP 3: Blind Evaluation
# ============================================================
echo ""
echo "━━━ Step 3/4: Blind Evaluation ━━━"
mkdir -p "$EXPERIMENT_DIR/eval"

if [ -f "$EXPERIMENT_DIR/eval/DONE" ]; then
    echo "  Already complete. Skip."
else
    echo -n "  $(date '+%H:%M:%S') running Opus evaluator..."

    claude -p "$(cat "$EXPERIMENT_DIR/prompts/step3-blind-eval.md")" \
        --allowedTools 'Read,Write,Bash,Glob,Grep' \
        --model opus \
        > "$EXPERIMENT_DIR/eval/session-log.txt" 2>&1

    touch "$EXPERIMENT_DIR/eval/DONE"
    echo " done"
fi
echo "  ✓ Step 3 complete"

# ============================================================
# STEP 4: Compile Report
# ============================================================
echo ""
echo "━━━ Step 4/4: Compile Report ━━━"
mkdir -p "$EXPERIMENT_DIR/report"

if [ -f "$EXPERIMENT_DIR/report/DONE" ]; then
    echo "  Already complete. Skip."
else
    echo -n "  $(date '+%H:%M:%S') running Opus reporter..."

    claude -p "$(cat "$EXPERIMENT_DIR/prompts/step4-compile-report.md")" \
        --allowedTools 'Read,Write,Edit,Bash,Glob,Grep' \
        --model opus \
        > "$EXPERIMENT_DIR/report/session-log.txt" 2>&1

    touch "$EXPERIMENT_DIR/report/DONE"
    echo " done"
fi
echo "  ✓ Step 4 complete"

# ============================================================
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              Experiment Complete!                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo "  v1 readers:  experiment/v1/reader-*.md"
echo "  v2 readers:  experiment/reader-*.json"
echo "  Blind eval:  experiment/eval/"
echo "  Report:      experiment/report/"
echo "  Finished:    $(date '+%H:%M:%S')"
echo ""
echo "Run: cat experiment/report/experiment-report.md"
