# Interface & Prompt Construction (Code-Derived)

## Purpose
Describe the LLM interface contract and how prompts/messages are constructed at runtime.

## Inputs
- `ExecutionContext` (user input, stance, HRM assessment, commitment, history)
- LLM callable with signature `llm(system: str, messages: list, prompt: str) -> str`
- Optional base system prompt configured via CLI or Config

## Outputs
- Generated response string
- `ExecutionResult` with metadata (altitude, stance, notes)

## LLM Interface Contract
The LLM callable is invoked with:
- `system`: system prompt string (dynamic per call)
- `messages`: list of conversation messages (`{"role": "user|assistant", "content": "..."}`)
- `prompt`: optional appended prompt (used for greeting)

## System Prompt Layers
1. **Base system prompt (optional)**
   - Loaded from CLI `--system-prompt` or `Config.system_prompt`.
   - Prepended to any per-call system prompt.

2. **Per-call system prompt (Executor)**
   - Built by `Executor._build_system_prompt` using:
     - Altitude guidance (style/structure/max length)
     - Stance behaviors (emphasis/actions/avoid)
     - Commitment constraints (frame/success/non-goals)
     - HRM constraints (derived from commitment)

3. **Prompt enhancer (optional)**
   - `LockedLoop` can apply a `prompt_enhancer` to modify the system prompt before calling the LLM.

## Message Construction
`Executor._generate_response` constructs `messages` by:
- taking the last 20 entries from `conversation_history`
- appending the current user input as a user message
- sending `system` + `messages` to the LLM

## Special Paths
- **Bootstrap responses**: `_handle_bootstrap` builds stage-specific system prompts and calls the LLM directly, bypassing the normal Executor system prompt.
- **Greeting**: `generate_greeting` builds a greeting system prompt and calls the LLM with `prompt="Generate greeting"`.

## Outputs and Post-Processing
- Response is truncated to the altitude’s max word count.
- Interaction signals are recorded in fast memory.
