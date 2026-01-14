# Interface & Prompt Construction (Code-Derived)

## Purpose
This document describes how the Locked System constructs prompts and interfaces with language models, based on code inspection of the executor and configuration systems.

## Inputs
- `ExecutionContext` containing:
  - User input string
  - Current stance (Stance enum)
  - HRM assessment (altitude + reasoning)
  - Current commitment (CommitmentLease or None)
  - Conversation history (list of message dicts)

## Outputs
- LLM response string
- Altitude used (L1-L4 enum value)

## Key Call Paths

### Executor Execution (`Executor.execute()`)
1. **Build system prompt** from config + context
2. **Construct message list** from conversation history
3. **Add altitude-specific instructions** based on HRM assessment
4. **Call LLM** with system prompt, messages, and max tokens
5. **Return response** with altitude metadata

### System Prompt Construction (`Config.get_system_prompt_content()`)
- Load from file path if configured (`system_prompt: Path`)
- Return string directly if configured (`system_prompt: str`)
- Return None for generic behavior

### LLM Interface (`create_llm()` in cli/main.py)
- **Claude Integration**: Uses Anthropic client with messages API
- **Fallback Mode**: Placeholder responses when API unavailable
- **Signature**: `llm(system: str, messages: list, prompt: str) -> str`
- **Message Format**: `[{"role": "user/assistant", "content": "..."}]`

## Prompt Construction Details

### Base System Prompt
```python
# From Config.get_system_prompt_content()
full_system = base_system_prompt
if system:
    full_system = f"{base_system_prompt}\n\n{system}" if base_system_prompt else system
```

### Message List Construction
```python
# From claude_llm() in cli/main.py
msgs = list(messages) if messages else []
if prompt:
    msgs.append({"role": "user", "content": prompt})
if not msgs:
    msgs = [{"role": "user", "content": "Hello"}]
```

### Altitude Integration
- HRM assessment provides altitude level (L1-L4)
- Altitude affects response constraints and focus
- Altitude reasoning tracked for signal monitoring

## Interface Characteristics
- **Stateless Execution**: Each call is independent with full context
- **Multi-turn Support**: Conversation history passed in messages
- **Configurable Models**: Support for different Claude models via config
- **Token Limits**: Enforced via max_tokens configuration
- **Error Handling**: Graceful fallback to placeholder when API unavailable
- **Extension Points**: LLM callable can be replaced for testing/customization</content>
<parameter name="filePath">/Users/raymondbruni/AI_ARCH/code_derived_docs/interface_prompt_construction.md