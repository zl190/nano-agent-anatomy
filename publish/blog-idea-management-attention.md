# Blog Idea: Bad Management Is Micromanagement — What LLM Context Degradation Teaches About Leading Agents (and People)

## Core Thesis

Human attention during execution degrades the same way LLM context does. Talking to an agent during its execution session is micromanagement — it adds noise, triggers multi-turn degradation (39%, Microsoft 2025), and reduces output quality. Good management is planning + QC, not hovering.

## The Connection Map

| Management pattern | LLM equivalent | Effect |
|---|---|---|
| Micromanagement (constant check-ins) | Multi-turn conversation during execution | 39% quality degradation (Laban 2025) |
| Good planning upfront | Brainstorm session → distilled brief | Clean context, focused execution |
| QC gate at delivery | Independent audit (dual QC) | Catches credence good problem |
| "Let them run" | Execution session, 0 user interrupts | Session 22: 20 min, 6 tasks, 0 blocks |
| No planning, no QC | No handoff brief, no hooks | "实验就跑飞掉了" — experiments diverge |

## Evidence from Our System

- Session 22 (user silent): 20 min, 6 tasks, 0 blocks, 0.3 tasks/min
- Previous sessions with heavy user interaction: more interrupts, direction changes, lower throughput
- Microsoft 2025: 39% multi-turn degradation is empirical, not theoretical
- "Without planning and QC, 实验就跑飞掉了" — user's own observation from prior sessions

## The Management Insight

Good management = **single-round prompt** (clear brief) + **QC at the end** (independent audit)
Bad management = **multi-round chatting** during execution (micromanagement)

This clicks with:
1. TextGrad invariant: analysis ≠ synthesis. Manager analyzes (plans), worker synthesizes (executes). Conflating them degrades both.
2. MASS staging: measure → search → optimize must be staged. Not simultaneous.
3. The attention mechanism itself: human attention is a finite context window too. Adding more check-in tokens dilutes focus on the actual task.

## What This Teaches for System Design

| Lesson | System implementation |
|--------|---------------------|
| Plan before execute | Handoff brief = executable spec |
| Don't hover | Execution session = 0 user interrupts |
| QC at delivery, not during | Dual QC gate (mechanical + persona) |
| Enforce boundaries | Hooks prevent bad output at system level |
| "实验就跑飞掉了" without guardrails | Hooks = the guardrails. Without them, 96.8% of CC users (Galster) |

## Narrative Arc

1. Hook: "I realized I was micromanaging my AI agent."
2. The data: Microsoft 2025 — 39% degradation from multi-turn
3. The experiment: session 22 vs previous sessions
4. The management parallel: planning + QC vs hovering
5. The system design lesson: hooks = guardrails, not micromanagement
6. Takeaway: good management of agents = good management of people = plan, resource, audit. Not chat.

## Connections to Existing Blog Arc

- Clicks with "22/22 is a lie" — QC is the management layer, not the execution layer
- Clicks with harness landscape — harness IS the management infrastructure
- Clicks with credence good thesis — you can't evaluate quality by watching (micromanaging); you need independent audit
- New angle: this is the HUMAN behavior post. Others are about agent behavior.

## Target

Substack, 1500-2000 words. This is the "management lessons from building with AI" post that crosses over to non-technical readers.
