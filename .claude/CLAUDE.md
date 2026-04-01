# nano-agent-anatomy — Project Rules

## What This Project Is

A study journal: read production agent source code + Berkeley MOOC → rebuild each layer → commit learning notes. Not a framework. Not a product.

## QC Gate (Enforcement)

**No code gets pushed without passing QC.** This is a hard gate, not a suggestion.

Before any `git push`:

1. **Does the code run?** `python main.py` must not crash on import.
2. **Is there a learning note?** Every code change must have a corresponding entry in `notes/`. Code without explanation is not learning — it's copying.
3. **Source attribution?** If the code is inspired by production source, the inline comment must say which file/concept it maps to. If it's our original design, say so.
4. **One concept per commit.** Each commit teaches exactly one thing. No "misc fixes" or "various improvements."

## Commit Format

```
learn: <what we discovered>

Source: <which production file/concept this maps to>
MOOC: <which lecture this relates to, if any>
```

Examples:
- `learn: tool loop needs max iterations to prevent runaway`
- `learn: autoDream prune phase removes entries >30 days with no references`
- `learn: coordinator uses natural language, not API calls, for task decomposition`

## Code Standards

- Each .py file ≤ 150 lines. If it's longer, you don't understand the concept well enough to simplify it.
- Every file starts with a docstring explaining what production concept it implements.
- Comments explain WHY (the production insight), not WHAT (the code is readable).
- No dependencies beyond `anthropic` (or `openai`). The point is zero-framework understanding.

## Study Process

For each layer:
1. Read the production source (claw-code or analysis)
2. Watch the corresponding MOOC lecture
3. Write the learning note (`notes/0N-topic.md`)
4. Write or rewrite the code
5. QC gate → commit → push

## Anti-Patterns

- **Don't write code you can't explain.** If you copied a pattern but don't know why, write the note first.
- **Don't optimize.** Clarity > performance. Always.
- **Don't add features.** This is a textbook. Features go in real projects.
- **Don't skip the note.** Code without learning context is worthless in 2 weeks.
