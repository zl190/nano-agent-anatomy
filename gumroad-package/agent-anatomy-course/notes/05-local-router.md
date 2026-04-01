# Layer 0: Local Router

## Status: Planned

## The problem

API calls cost money and have latency. Local models are free but weaker.
A smart agent routes to the right model for each task.

## Routing strategy

```
User request → classify complexity
  → Simple (summarize, format, short Q&A) → local model (Ollama)
  → Complex (tool use, reasoning, code gen) → API (Claude/GPT)
  → Ambiguous → try local first, escalate on failure
```

## Implementation plan

Add `router.py`:
- ModelRouter class with local and API backends
- Complexity classifier (can be rule-based or LLM-based)
- Fallback chain: local → API on failure
- Cost tracking: how much did routing save?

## References

- Production CC uses single model per session but has model override per agent type (`model` parameter in Agent tool) — confirmed from CC TS source
- "Claude Code Auto Mode" eng blog (Mar 2026) — two-stage classifier (fast filter → CoT) is a production routing pattern worth studying for local/API routing design
- **Note on lecture attribution:** Early draft referenced "MOOC L3: System Design (Yangqing Jia, NVIDIA)" — this speaker/topic is not found in any Berkeley LLM Agents course (F24, S25, F25). Removed as unverified reference.

## TODO

- [ ] Set up Ollama with a good local model (Qwen 2.5 7B or similar)
- [ ] Implement basic router with hardcoded rules
- [ ] Add cost comparison logging
- [ ] Study how production handles model selection per-agent
