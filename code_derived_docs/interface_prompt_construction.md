# Interface & Prompt Construction (Code-Derived)

## Purpose
Describe the external interfaces for response generation and how system prompts and message lists are assembled based on code in the CLI and executor.

## Inputs
- **LLM configuration** via `Config` and optional `--system-prompt` CLI argument.
- **Conversation history** stored in `LockedLoop._conversation_history`.
- **Execution context** built from user input, stance, HRM assessment, and commitment.

## Outputs
- **LLM call** with `system` and `messages` arguments (plus optional `prompt` in the LLM signature), returning a response string.
- **ExecutionResult** and `LoopResult` with derived metadata (altitude, stance, health).

## Key Call Paths / Data Flow
### CLI → Loop → LLM
1. **CLI setup**
   - `locked_system.cli.main.main` loads config (`Config.from_yaml` or default `Config`) and reads a system prompt from CLI `--system-prompt` or from `Config.system_prompt` if it points to a file.
   - `create_llm(config, system_prompt)` returns an LLM callable and a status string.
     - If `ANTHROPIC_API_KEY` is set, `claude_llm` is returned. It concatenates the base system prompt and any per-call `system` string (e.g., executor constraints).
     - Otherwise, a placeholder LLM is returned that echoes the last user message.

2. **Execution context assembly**
   - `LockedLoop._fast_loop_execute` creates `ExecutionContext` with:
     - `user_input` (current turn)
     - `stance` (`StanceMachine.current`)
     - `hrm_assessment` (`HRM.assess`)
     - `commitment` (`CommitmentManager.get_current`)
     - `conversation_history` (last messages)

3. **Prompt construction** (`Executor._build_system_prompt`)
   - Builds a *behavioral constraints* string containing:
     - Altitude guidance (style, structure, max length)
     - Stance behaviors (emphasis, actions, avoid list)
     - Commitment frame + success criteria + non-goals (if active)
     - HRM constraints (e.g., avoid non-goals, horizon hints)
   - This constructed string is passed as the per-call `system` value.

4. **Message list construction** (`Executor._generate_response`)
   - Starts with up to the last 20 entries from `context.conversation_history` (10 turns).
   - Appends the current user input as a final `{"role": "user", "content": "..."}` message.

5. **LLM invocation**
   - `Executor._generate_response` calls `self._llm(system=system_prompt, messages=messages)`.
   - For the Claude-backed LLM in CLI, `system` is merged with the base system prompt:
     - If `base_system_prompt` exists and `system` is provided: `full_system = base_system_prompt + "\n\n" + system`.
     - If no base prompt is provided, `system` is used directly.

## Interface Signatures (Code-Derived)
- **LLM callable signature** (as used by `Executor` and returned by `create_llm`):
  - `llm(system: str = None, messages: list = None, prompt: str = None) -> str`
- **Loop entry point**:
  - `LockedLoop.process(user_input: str) -> LoopResult`
- **Executor entry point**:
  - `Executor.execute(context: ExecutionContext) -> ExecutionResult`

## Observed Extension Points
- `LockedLoop` stores optional hooks `on_gate_transition`, `on_response_generated`, and `prompt_enhancer` at initialization. The hook variables are stored but only `on_gate_transition` and `on_response_generated` are invoked in the current code path.
