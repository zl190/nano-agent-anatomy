# Unit 5 Exercises: Production Prompt Engineering

## Exercise 1: Find the Pattern (15 min)
Read 3 tool prompt files from the code progression:
- `context_v3.py` — find `NO_TOOLS_PREAMBLE`
- `coordinator_v3.py` — find the anti-patterns in `COORDINATOR_SYSTEM`
- `memory_v2.py` — find the JSON schema enforcement in `consolidate()`

For each:
1. What behavior does the prompt PREVENT (not just what it asks for)?
2. Is the language positive ("do X") or negative ("don't do X")?
3. Why might negative framing work better for some rules?

## Exercise 2: Scratchpad Design (15 min)
Read `context_v2.py`'s `_build_compaction_prompt()`.
1. The LLM outputs `<analysis>` then `<summary>`. Why this order?
2. What if you reversed it (summary first, then analysis)? Would quality change?
3. Design a scratchpad pattern for a different task: code review. What tags would you use?

## Exercise 3: Cache Economics (15 min)
Read `notes/05-prompt-engineering.md` — the "System prompt architecture" section.
1. If the system prompt is 10,000 tokens and the dynamic section is 2,000 tokens, what % is cached?
2. At $3/1M input tokens and $0.30/1M cached tokens, how much do you save per 1000 API calls?
3. Why does CC put the agent list as an attachment instead of in tool descriptions?

## Exercise 4: Write a Tool Prompt (20 min)
Design a prompt for a new tool: `search_codebase(query, file_pattern)`.
Using CC's patterns, your prompt must include:
1. A clear description of what the tool does
2. At least 2 anti-patterns ("Do NOT...")
3. An example showing expected input/output
4. A scope limitation

Compare your prompt to any tool description in `loop_v0.py`. How many of CC's patterns does the v0 version miss?

## Exercise 5: Cross-Validate (20 min)
Read `notes/05-prompt-engineering.md` cross-validation table.
1. Pick one discrepancy between Academy and CC source. Why does this gap exist?
2. If you were writing a certification exam, would you test CC's approach or Academy's? Why?
3. The note says "zero coverage in Chinese or English markets." Verify: search for articles about CC's prompt architecture. What did you find?
