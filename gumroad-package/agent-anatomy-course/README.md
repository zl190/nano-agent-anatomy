# Agent Anatomy: Dissecting Production AI Agents

What 513K lines of leaked source code taught me about building AI agents.

## What's in This Package

### notes/ — Learning Notes (14 files, ~2800 lines)

The full study journal. Each note covers what I found in the production source, what it means, how it connects to the Berkeley MOOC, and where the sources disagree.

| File | Topic |
|------|-------|
| `00-pedagogical-research.md` | Design rationale — why progressive code files, Karpathy method |
| `00-source-analysis.md` | Initial source reading summary |
| `00-source-analysis-full.md` | Extended source analysis |
| `00-source-validation-audit.md` | **5-source cross-validation audit** — the core analytical work |
| `01-tool-loop.md` | Unit 1: max_iterations, is_error, permission before execution |
| `02-memory.md` | Unit 2: 2-layer architecture, autoDream consolidation |
| `03-context.md` | Unit 3: LLM vs deterministic compaction, the big discrepancy |
| `04-coordinator.md` | Unit 4: NL orchestration, "never delegate understanding" |
| `05-local-router.md` | Unit 5: local routing patterns |
| `05-prompt-engineering.md` | Unit 5: 44 production prompts analyzed |
| `06-agent-reliability-triad.md` | The reliability pattern: permissions + memory + context |
| `07-integration.md` | Unit 6: all layers running together |
| `08-final-gap.md` | **Gap analysis** — what production does that 150 lines can't |
| `09-context-pollution-rewind.md` | Novel contribution: correction-aware microcompact |

### exercises/ — Comprehension Exercises (5 files)

One per unit. Questions force you to trace through the code with concrete values.

### experiment/ — Blind A/B Reading Experiment

The full experiment report: free-form vs structured-schema source reading. Same model, same file splits, independent evaluator. Free-form wins 6-1. The SOP that came out of this is the methodology recommendation.

### cross-validation/ — Unified Claims Model

`model.md` contains all 9 verified claims with evidence chains, the coverage matrix across all projections, and the gap analysis showing what's still unvalidated.

## How to Use This

1. Clone the [open-source repo](https://github.com/zl190/nano-agent-anatomy) for the code files and tests
2. Read each unit's note alongside its code progression (e.g., `01-tool-loop.md` + `loop_v0.py` through `loop_v3.py`)
3. Do the exercises after reading each unit
4. Read `00-source-validation-audit.md` for the 5-source cross-validation — **where the sources disagree is where the insight is**

## The 4 Key Discrepancies (the gold)

1. **Compaction**: claw-code = deterministic extraction; CC TypeScript = LLM with 9-section prompt + scratchpad
2. **Agent spawning**: SDK = `AgentDefinition` dataclass; CC source = "Never delegate understanding" + fork-vs-fresh cache strategy
3. **Permissions**: Docs teach 3-tier auto-mode; CC source has fail-secure (unknown -> highest) + deny reason as `is_error`
4. **Memory**: SDK exposes a `memory` flag; CC source has 2-layer architecture + autoDream + semantic search via 256-token side call

## License

The code in the open-source repo is MIT. This course material (notes, exercises, cross-validation analysis) is for personal use only. Do not redistribute.
