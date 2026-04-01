# Unit 1 Exercises: The Tool Loop

## Exercise 1: Predict the Behavior (5 min)
Read `loop_v0.py` lines 105-135 (the inner while True loop).
**Predict:** What happens if the LLM keeps calling `bash` with the same command that returns "try again"?
**Verify:** Read `loop_v1.py` and note the fix. What is MAX_ITERATIONS set to? Why that number?

## Exercise 2: Trace the Denial Path (10 min)
In `loop_v1.py`, a bash command containing "rm -rf" is denied.
1. Trace what happens: which function detects the denial? What does the tool_result look like?
2. The LLM receives `is_error=True` in its context. What can it do with this information?
3. Compare: in `loop_v0.py`, what would happen with the same command? Why is this worse?

## Exercise 3: Token Budget Stop Condition (15 min)
Read `loop_v2.py` and find the `run_turn()` function.
1. What are the three possible values of `stop_reason`?
2. Why is the budget check AFTER the API call, not before?
3. What happens if `token_budget=0`? Trace the code path.

## Exercise 4: Permission Levels (15 min)
Read `permissions.py` and `loop_v3.py`.
1. What permission level does `read_file` require? `write_file`? `bash`?
2. What permission does an UNKNOWN tool get? Why is this called "fail-secure"?
3. Create a `PermissionPolicy` with READ_ONLY mode. Which tools can it use? Test in Python REPL.

## Exercise 5: Compare to Production (20 min)
Read `notes/01-tool-loop.md` and the "Production → Our code mapping" table.
1. List 3 things production does that loop_v3.py doesn't.
2. For each gap, explain: would adding it help a learner or just add complexity?
3. Read the "What Production Does That We Don't" section. Which gap would you close first? Why?
