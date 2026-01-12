# Code-Derived Design Doc (Behavioral Overview)

## Purpose
Summarize runtime behavior based solely on code execution paths. This describes what the system does when processing input and how subsystems interact.

## Inputs
- User input text via CLI (interactive or single-message).
- Optional configuration (Config) and system prompt content.
- Optional LLM callable with signature `llm(system: str, messages: list, prompt: str) -> str`.

## Outputs
- `LoopResult` containing response, stance, altitude, bootstrap status, gate transitions, and health.
- Persisted conversation history (`conversation.json`).
- Optional note files (`notes/developer.md`, `notes/personal.md`).

## Core Behavioral Flow (Single Turn)
1. **Note shortcut**
   - `LockedLoop.process` calls `_check_note_intent`.
   - If note intent is detected, it writes a note and returns a short confirmation response without executing the slow/fast loop phases.

2. **Perception sensing**
   - `_sense` builds a `PerceptionContext` and runs `PerceptionSensor.sense` to infer emotional state, urgency, intent, and context cues.

3. **Bootstrap handling**
   - If bootstrap is active, `_handle_bootstrap` runs staged prompts and returns a response early.
   - When bootstrap completes, it can call a completion hook and generates a completion acknowledgment.

4. **Slow loop tick**
   - Checks commitment expiry and adds a gate proposal if expired.
   - Decrements commitment turns.
   - Processes proposals via `GateController.process_proposals` and applies any stance transitions.

5. **Fast loop execution**
   - HRM determines altitude using heuristics (horizon, risk, moment).
   - `Executor` builds a system prompt using stance + altitude + commitment constraints and calls the LLM.

6. **Continuous evaluation**
   - `ContinuousEvaluator.evaluate` scores response quality and may submit gate proposals.
   - `ContrastDetector.detect` evaluates mismatch between inferred need and observed behavior and adds contrast reports.

7. **Persistence**
   - Conversation history is appended and persisted to `conversation.json` (last 100 messages retained).

## Key Components and Responsibilities
- **LockedLoop**: Orchestrates all phases, owns conversation history, and manages hooks.
- **Slow loop (gates/stance/commitment)**: Controls stance transitions and commitment lifecycle.
- **Fast loop (HRM/executor/eval)**: Chooses response depth, generates response, assesses quality.
- **Sensing (perception/contrast)**: Produces non-authoritative observations and gap reports.
- **Memory**: Slow memory is authoritative; fast memory is continuous; history/bridge are audit/index.

## Persistence and Side Effects
- Conversation history and commitment state are saved to disk in configured memory directories.
- Notes are appended to markdown files when note intent is detected.
- Gate transitions and decisions are logged in history/slow memory files.
