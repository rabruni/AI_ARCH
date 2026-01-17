# Example: Prompt Construction for a Normal Turn

## Purpose
Provide a concrete, annotated example of how a standard turn builds the system prompt and message list when using the `Executor` path in the fast loop.

## Inputs (Example Scenario)
- **Conversation history** (last messages in `LockedLoop._conversation_history`):
  1. `{role: "user", content: "I want to plan a weekly study schedule."}`
  2. `{role: "assistant", content: "Sure — what subjects are you prioritizing?"}`
- **Current user input**: `"Mostly math and writing, and I have exams in two months."`
- **Stance**: `Stance.SENSEMAKING` (from `StanceMachine.current`).
- **HRM assessment**: `Altitude.L3_CONSIDERED` with constraints derived from commitment (if any).
- **Commitment**: none (for this example).
- **Base system prompt**: read by CLI from `Config.system_prompt` or `--system-prompt` (content not shown here because only code is inspected).

## Output
- **LLM call** with `system` string (constructed constraints) and `messages` list (history + current input).
- **ExecutionResult** and then `LoopResult` containing the response and metadata.

## Construction Walkthrough
### Step 1: Build the executor system prompt
`Executor._build_system_prompt` constructs a constraints prompt based on altitude and stance:

```text
## Behavioral Constraints

Response style: thoughtful, balanced
Structure: structured response
Target length: up to 300 words

Current mode emphasis: understanding, clarifying
Recommended actions: ask clarifying questions, reframe, explore context
Avoid: premature solutions, rushing to action
```

If a commitment existed, this block would append:
- `Active commitment: ...`
- `Success criteria: ...`
- `Non-goals (avoid): ...`

If HRM constraints exist (e.g., from non-goals), those lines are appended as `Additional constraints: ...`.

### Step 2: Merge base system prompt (LLM callable)
The Claude-backed LLM callable merges `base_system_prompt` with the executor’s constraints:

```text
<base system prompt from Config.system_prompt or CLI --system-prompt>

## Behavioral Constraints
... (constraints from Step 1)
```

If no base prompt is available, the system string is only the constraints block.

### Step 3: Build the messages list
`Executor._generate_response` assembles messages from the last ~20 conversation turns and appends the new user message:

```json
[
  {"role": "user", "content": "I want to plan a weekly study schedule."},
  {"role": "assistant", "content": "Sure — what subjects are you prioritizing?"},
  {"role": "user", "content": "Mostly math and writing, and I have exams in two months."}
]
```

### Step 4: Call the LLM
`Executor._generate_response` invokes:

```python
llm(system=system_prompt, messages=messages)
```

The resulting response is then constrained to the altitude word limit and recorded into `FastMemory` as interaction signals.
