# Problem — Attention Modules (SPEC-005)

LLM assistants often fail attention management in predictable ways:

- Over-explain and amplify stress under uncertainty.
- Drift into rabbit holes while “being helpful”.
- Lose continuity across interruptions and days.
- Present too many options, increasing cognitive load.
- Conflate “what matters” with “what is being discussed”.

We need a library of **simple attention control primitives** that can be composed
into different stacks (personas and subagents) without rewriting the system or
conflating roles (DoPeJar vs Control Plane).
