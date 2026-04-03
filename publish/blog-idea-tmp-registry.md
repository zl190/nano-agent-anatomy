# Blog Idea: /tmp Is Already Right — Why We Built a Registry Instead of Copying 72MB

## Core Thesis

The instinct to "persist everything" is wrong. /tmp files already persist across sessions until reboot. The real problem is discoverability, not durability. A 132KB index beats a 72MB copy — 500x lighter, same value.

## The Story

1. Session 22: spawned 9 agents, all outputs in /tmp (72MB)
2. First instinct: copy everything to persistent storage. Did it. Worked.
3. User challenged: "if they're alive until reboot in /tmp, maybe it's already a good design"
4. Realized: /tmp IS the right abstraction for temp files. The OS already solved this.
5. Built a JSONL registry (132KB) pointing to /tmp paths instead
6. Selective persist (--persist flag) only when it matters: before reboot, important research

## The Deeper Pattern

This is the same pattern as:
- **Meta-Harness [2603.28052]**: filesystem of raw traces as feedback channel — the traces already exist, you need a proposer that knows how to find them
- **Unix philosophy**: don't duplicate what the OS already provides. Index, don't copy.
- **Database indexing**: the data stays where it is, the index makes it findable
- **Git**: objects in .git/objects are content-addressed blobs. Git doesn't copy your files — it indexes them.

## The Management/Engineering Lesson

| Instinct | Reality | Fix |
|----------|---------|-----|
| "Save everything" | Storage is cheap but duplication creates maintenance debt | Index the originals |
| "Move to permanent storage" | /tmp IS persistent (until reboot) | Add discoverability, not durability |
| "72MB is fine" | 132KB serves the same purpose | Ask: what's the actual problem? |

The actual problem was never "files might disappear." It was "nobody knows which agent produced what." The registry solves the real problem.

## Connection to Credence Good Thesis

Agent outputs are credence goods — you can't tell quality by looking at them. The registry doesn't solve quality (that's QC's job), but it solves attribution: which agent, which session, which task, what size. Attribution is the prerequisite for audit.

## For the Blog Arc

This fits as a short TIL-style post (500-800 words). Julia Evans format: "I was wrong about X, here's what I learned."

Hook: "I copied 72MB of agent transcripts to permanent storage. Then my user asked why."
