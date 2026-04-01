# Unit 3 Exercises: Context Compression

## Exercise 1: LLM vs Deterministic (10 min)
Read `context_v0.py` and `context_v1.py` side by side.
1. Which one requires an Anthropic client? Why?
2. Which one is testable without an API key?
3. List 3 advantages of deterministic extraction over LLM summarization.

## Exercise 2: Dual Trigger (10 min)
Read `context_v1.py` `should_compress()`.
Construct a message list that:
1. Has 20 messages but only 500 tokens total → should NOT trigger compression
2. Has 3 messages but 50,000 tokens total → should NOT trigger compression
3. Has 20 messages AND 50,000 tokens → SHOULD trigger compression
Verify each by calling `should_compress()` in a Python REPL.

## Exercise 3: Analysis Scratchpad (15 min)
Read `context_v2.py` and find `strip_analysis_tags()`.
1. Why does the LLM output `<analysis>` if it gets stripped?
2. What's the parallel to "extended thinking" in the Claude API?
3. Read `context_v3.py` — what does `NO_TOOLS_PREAMBLE` prevent? Why is blunt language necessary?

## Exercise 4: Integration Checkpoint (20 min)
Build a 20-message conversation list manually (alternating user/assistant, including tool_results).
1. Run it through `context_v1.py`'s `summarize_messages()`. What does the summary contain?
2. Does it preserve the pending tasks? The file paths?
3. Compare: what would `context_v0.py` produce for the same input? (predict, don't run)

## Exercise 5: Cross-Validation (20 min)
Read `notes/03-context.md` including the "Correction: CC TS uses LLM-based compaction" section.
1. claw-code = deterministic, CC TS = LLM-based. Both ship in production. Why the difference?
2. Our v1 is claw-code's approach, v2 is CC TS's approach. What's the tradeoff?
3. Read the "What Production Does" section. What is `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` and why does it matter for cost?
