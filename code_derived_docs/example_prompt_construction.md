# Example: Prompt Construction for a Normal Turn

## Purpose
This document provides a concrete, annotated example of how the Locked System constructs prompts and message lists for LLM calls, based on code inspection of the executor path.

## Inputs
- `ExecutionContext` with user input: "How should I approach this project?"
- Current stance: `Stance.SENSEMAKING`
- HRM assessment: `Altitude.L3_CONSIDERED` with reasoning "User seeking guidance on approach"
- Active commitment: `CommitmentLease(frame="Complete project planning", success_criteria=["Define scope", "Set timeline"])`
- Conversation history: 3 previous exchanges

## Outputs
- System prompt string with behavioral constraints
- Message list for multi-turn conversation
- LLM response constrained by altitude and stance

## Annotated Example Construction

### Step 1: Altitude Guidance Lookup
```python
# From Executor.ALTITUDE_GUIDANCE[Altitude.L3_CONSIDERED]
altitude_guide = {
    "max_length": 300,
    "style": "thoughtful, balanced",
    "structure": "structured response"
}
```

### Step 2: Stance Behavior Lookup
```python
# From Executor.STANCE_BEHAVIORS[Stance.SENSEMAKING]
stance_behavior = {
    "emphasis": "understanding, clarifying",
    "actions": ["ask clarifying questions", "reframe", "explore context"],
    "avoid": ["premature solutions", "rushing to action"]
}
```

### Step 3: System Prompt Construction (`_build_system_prompt()`)
```
## Behavioral Constraints

Response style: thoughtful, balanced
Structure: structured response
Target length: up to 300 words

Current mode emphasis: understanding, clarifying
Recommended actions: ask clarifying questions, reframe, explore context
Avoid: premature solutions, rushing to action

Active commitment: Complete project planning
Success criteria: Define scope, Set timeline

Additional constraints: [from HRM assessment]
```

### Step 4: Message List Construction (`_generate_response()`)
```python
# Build messages from conversation history + current input
messages = [
    {"role": "user", "content": "I'm starting a new project"},
    {"role": "assistant", "content": "What kind of project is it?"},
    {"role": "user", "content": "It's a software development project"},
    {"role": "assistant", "content": "Got it. What are your main goals?"},
    {"role": "user", "content": "How should I approach this project?"}  # Current input
]
```

### Step 5: LLM Call Signature
```python
# Call pattern from executor.py line 203
response = self._llm(system=system_prompt, messages=messages)
```

### Step 6: Response Processing
- Generate response using Claude API
- Apply length constraints (truncate to 300 words if exceeded)
- Record interaction signals to fast memory
- Return `ExecutionResult` with altitude and stance metadata

## Key Code Evidence
- **File**: `locked_system/fast_loop/executor.py`
- **Function**: `execute()` (lines 108-149)
- **Prompt Building**: `_build_system_prompt()` (lines 151-185)
- **Message Construction**: `_generate_response()` (lines 187-203)
- **Constraint Application**: `_apply_constraints()` (lines 205-215)

## Behavioral Impact
- **Altitude L3**: Forces thoughtful, structured responses up to 300 words
- **Sensemaking Stance**: Emphasizes understanding over action, avoids premature solutions
- **Commitment Context**: Constrains responses to align with "Complete project planning" frame
- **Multi-turn History**: Provides conversation context for coherent responses</content>
<parameter name="filePath">/Users/raymondbruni/AI_ARCH/code_derived_docs/example_prompt_construction.md