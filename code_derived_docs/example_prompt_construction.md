# Example: Prompt Construction for a Normal Turn

## Purpose
Provide a concrete, annotated example of how the system prompt and message list are built for a normal turn using the Executor path.

## Example Input
User input:
```
I’m anxious about a job decision and need help figuring out next steps.
```

Assumptions for this example:
- Current stance: Sensemaking
- HRM recommended altitude: L3
- Active commitment present with:
  - frame: "Help user make a job decision"
  - success_criteria: ["Clear next steps", "User confirms clarity"]
  - non_goals: ["Long-term career counseling"]

## System Prompt Construction
`Executor._build_system_prompt` composes the system prompt from altitude guidance, stance behaviors, and commitment constraints. The resulting structure is:

```
You are a thoughtful assistant operating within specific behavioral constraints.

Response style: thoughtful, balanced
Structure: structured response
Target length: up to 300 words

Current mode emphasis: understanding, clarifying
Recommended actions: ask clarifying questions, reframe, explore context
Avoid: premature solutions, rushing to action

Active commitment: Help user make a job decision
Success criteria: Clear next steps, User confirms clarity
Non-goals (avoid): Long-term career counseling

Additional constraints: Avoid: Long-term career counseling
```

Notes:
- Altitude guidance comes from the L3 entry in `Executor.ALTITUDE_GUIDANCE`.
- Stance behaviors come from the Sensemaking entry in `Executor.STANCE_BEHAVIORS`.
- Commitment fields are appended when `context.commitment` is present.
- HRM constraints append non-goals as additional constraints.

## Messages List Construction
`Executor._generate_response` builds messages as follows:

1. Take up to the last 20 items from `conversation_history`.
2. Append the current user input as a user message.

Example messages list (simplified):
```
[
  {"role": "assistant", "content": "Hey. What's on your mind today?"},
  {"role": "user", "content": "I’m anxious about a job decision and need help figuring out next steps."}
]
```

## LLM Call
The LLM is called as:
```
llm(system=<constructed system prompt>, messages=<messages list>)
```

## Output Handling
- The response is truncated to 300 words (L3 max).
- Interaction signals are written to fast memory.
