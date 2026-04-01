# Unit 4 Exercises: Multi-Agent Coordination

## Exercise 1: Spot the Anti-Pattern (10 min)
Read `coordinator_v0.py` `coordinate()` function.
1. The decomposition is hardcoded: "Research: X" + "Execute: X". Why is this an anti-pattern?
2. What task would this decomposition be correct for? What task would it be wrong for?
3. Read `coordinator_v1.py` — how does it fix this?

## Exercise 2: Worker Isolation (15 min)
Read `coordinator_v2.py` and find `make_scoped_execute_tool()`.
1. What does "scoped" mean here? What directory constraint does it add?
2. Can worker A read a file that worker B wrote? Why or why not?
3. What happens to scratch directories when coordination finishes? (hint: `finally` block)

## Exercise 3: Prompt Engineering as Enforcement (15 min)
Read `coordinator_v3.py`'s `COORDINATOR_SYSTEM` and `WORKER_SYSTEM` prompts.
1. Find 3 behavioral rules encoded in the coordinator prompt. For each, what failure mode does it prevent?
2. Find 2 scope-limiting rules in the worker prompt. Why are these necessary?
3. Compare to `coordinator_v0.py`'s worker prompt. What's different and why does it matter?

## Exercise 4: Quality Check (15 min)
Read `coordinator_v3.py`'s `quality_check()` function.
1. Why is this a SEPARATE API call instead of adding "check quality" to the synthesis prompt?
2. What does the quality check prompt ask the LLM to evaluate?
3. Without this check, what would the coordinator do with a weak worker result? (hint: "rubber-stamp")

## Exercise 5: Compare to Production (20 min)
Read `notes/04-coordinator.md` and the "What Production Does That We Don't" section.
1. In production, the agent is a tool_use block, not a function call. What's the architectural difference?
2. What is `agentMemorySnapshot` and why is it richer than a return value?
3. Production has SendMessage for bidirectional communication. Design a scenario where this matters.
