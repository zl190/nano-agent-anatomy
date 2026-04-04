You are running a source code reading experiment. Your job is to read a large TypeScript codebase using the v1 SOP methodology.

## SOP v1 (the ONLY methodology you follow)

Pattern: Scout → Reader × N → Synthesizer

### Reader Instructions (from SOP v1 verbatim):
- Split by: subsystem/layer/module (NOT by file — by concept)
- Each agent gets: exact file paths, output schema
- Output schema per reader:
  1. Line count
  2. Core classes/functions (signature + one sentence)
  3. Production insight (what tutorials don't teach)
  4. Mapping to our code (which .py, what to improve)
- Budget: 3-8 files per agent, ~2000 lines max
- Model: sonnet (sufficient for structured extraction)

### Important constraints:
- Do NOT use JSON output format. Free-form text/markdown is expected.
- Do NOT assign personas to readers. They are generic readers.
- Do NOT add validation gates between stages.
- Do NOT add confidence tags or surprise fields.
- Follow the v1 SOP EXACTLY as written above. No enhancements.

## Your task

Read the experiment spec file at:
experiment/experiment-spec.json

Use the SAME 6 file assignments from the spec (controlled variable).

For each of the 6 reader groups, launch a parallel Agent (model: sonnet) with the v1-style prompt:

```
You are reading source code. Report on the files assigned to you.

Your assigned files: [list from spec]

For each file or group of files, report:
1. Line count
2. Core classes/functions (signature + one sentence)
3. Production insight (what tutorials don't teach)
4. Mapping to our code (which patterns we could adopt)

Read the files and provide a thorough analysis. Focus on what's architecturally important.
```

That's the entire reader prompt. No JSON schema. No persona. No validation requirements.

After all 6 readers complete, save each reader's raw output to:
experiment/v1/reader-{N}-{name}.md

Then launch a synthesizer agent (model: opus) with this prompt:

```
You have 6 reader reports from a source code reading exercise on Claude Code (513K lines TypeScript).

Here are the reports: [include all 6 reader outputs]

Synthesize:
1. Cross-cutting patterns (appear in 2+ reports)
2. Architecture summary (3-5 paragraphs for a senior engineer)
3. Most surprising findings
```

Save the synthesis to:
experiment/v1/synthesis-v1.md

Finally, save metrics to:
experiment/v1/metrics-v1.json

Include: tokens consumed per reader, duration, number of symbols/patterns/surprises extracted (count manually from the free-form text).

When done, write a file experiment/v1/DONE to signal completion.
