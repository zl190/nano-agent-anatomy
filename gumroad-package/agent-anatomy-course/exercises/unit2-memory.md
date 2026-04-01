# Unit 2 Exercises: Memory + Consolidation

## Exercise 1: Observe Append-Only Growth (10 min)
Read `memory_v0.py`. Create a MemoryStore and call `save()` 5 times with the same key.
1. How many entries are in `_entries`?
2. What's wrong with this? (hint: load the memory and count duplicates)
3. Read `memory_v1.py` — how does it prevent duplicate index entries?

## Exercise 2: Index Budget (10 min)
Read `memory_v1.py` and find `MAX_INDEX_LINES`.
1. What happens when the index exceeds 50 lines?
2. Which entry gets dropped — oldest or newest? Why?
3. Production uses 200 lines at 150 chars each. Calculate the max index size in bytes.

## Exercise 3: autoDream Phases (15 min)
Read `memory_v2.py` and find the `consolidate()` method.
1. Name the 4 phases. What does each do?
2. What happens if the LLM returns invalid JSON during consolidation?
3. Why does consolidation wipe and rewrite ALL files instead of patching individual ones?

## Exercise 4: Compare to Production (20 min)
Read `notes/02-memory.md` and the "What Production Does That We Don't" section.
1. Production uses a 256-token side call for relevance. What problem does this solve that our `load()` doesn't?
2. Why doesn't our implementation need semantic search? (hint: how big is our memory?)
3. What is a "session DAG with parentUuid chain"? Why would production need it but we don't?
