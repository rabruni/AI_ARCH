"""Locked Loop - Main Orchestration.

Two-tempo loop:
- Slow Loop: Authority layer (gates, stance, commitment)
- Fast Loop: Execution layer (HRM, executor, continuous eval)

Invariants:
- Slow loop has authority over stance transitions
- Fast loop operates within slow loop constraints
- Proposals flow up, decisions flow down
"""
from typing import Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
import json

from locked_system.config import Config

# Memory
from locked_system.memory.slow import SlowMemory
from locked_system.memory.fast import FastMemory, ProgressState
from locked_system.memory.bridge import BridgeMemory
from locked_system.memory.history import History

# Proposals
from locked_system.proposals.buffer import ProposalBuffer

# Slow Loop
from locked_system.slow_loop.stance import StanceMachine, Stance
from locked_system.slow_loop.commitment import CommitmentManager
from locked_system.slow_loop.gates import GateController
from locked_system.slow_loop.bootstrap import Bootstrap, BootstrapStage

# Fast Loop
from locked_system.fast_loop.hrm import HRM
from locked_system.fast_loop.executor import Executor, ExecutionContext
from locked_system.fast_loop.continuous_eval import ContinuousEvaluator

# Sensing
from locked_system.sensing.perception import PerceptionSensor, PerceptionContext
from locked_system.sensing.contrast import ContrastDetector, ContrastContext

# Features
from locked_system.notes import Notes, NoteType


@dataclass
class LoopResult:
    """Result of a single loop iteration."""
    response: str
    stance: str
    altitude: str
    bootstrap_active: bool
    gate_transitions: list[str]
    quality_health: str
    turn_number: int


class LockedLoop:
    """
    Main orchestration loop.

    Coordinates slow and fast loops with proper authority hierarchy.

    Hooks for extensibility:
        on_bootstrap_complete: Called when bootstrap finishes (user_name: str)
        on_gate_transition: Called on gate transitions (gate: str, from_stance: str, to_stance: str)
        on_response_generated: Called after response generation (response: str, result: LoopResult)
        prompt_enhancer: Callable to modify/enhance prompts before LLM call (prompt: str) -> str
    """

    # Proposal source priority
    PROPOSAL_PRIORITY = [
        "user_signal",
        "commitment_expiry",
        "perception",
        "continuous_eval",
        "contrast",
    ]

    def __init__(
        self,
        config: Optional[Config] = None,
        llm_callable: Optional[Callable[[str], str]] = None,
        # Extension hooks
        on_bootstrap_complete: Optional[Callable[[str], None]] = None,
        on_gate_transition: Optional[Callable[[str, str, str], None]] = None,
        on_response_generated: Optional[Callable[[str, "LoopResult"], None]] = None,
        prompt_enhancer: Optional[Callable[[str], str]] = None,
    ):
        self.config = config or Config()

        # Store hooks
        self._on_bootstrap_complete = on_bootstrap_complete
        self._on_gate_transition = on_gate_transition
        self._on_response_generated = on_response_generated
        self._prompt_enhancer = prompt_enhancer

        # Initialize memory layers with proper subdirectories
        self.slow_memory = SlowMemory(self.config.memory_dir / "slow")
        self.fast_memory = FastMemory(self.config.memory_dir / "fast")
        self.bridge_memory = BridgeMemory(self.config.memory_dir / "bridge")
        self.history = History(self.config.memory_dir / "history")

        # Initialize proposal buffer
        self.proposal_buffer = ProposalBuffer()

        # Initialize slow loop components
        self.stance = StanceMachine()
        self.commitment = CommitmentManager(self.slow_memory)
        self.gate_controller = GateController(
            self.stance,
            self.commitment,
            self.slow_memory,
            self.history
        )
        self.bootstrap = Bootstrap(
            self.slow_memory,
            intro_greeting=self.config.bootstrap_greeting,
            connect_prompt=self.config.bootstrap_connect_prompt
        )

        # Initialize fast loop components
        self.hrm = HRM()
        self.executor = Executor(self.fast_memory, llm_callable)
        self.continuous_eval = ContinuousEvaluator(self.proposal_buffer)

        # Initialize sensing
        self.perception = PerceptionSensor()
        self.contrast = ContrastDetector()

        # Initialize features
        self.notes = Notes(self.config.memory_dir / "notes")

        # State
        self._turn_count = 0
        self._conversation_history: list[dict] = []
        self._conversation_file = self.config.memory_dir / "conversation.json"

        # Load existing conversation history
        self._load_conversation_history()

    def process(self, user_input: str) -> LoopResult:
        """
        Process user input through the locked loop.

        Returns LoopResult with response and metadata.
        """
        self._turn_count += 1
        gate_transitions = []

        # Check for note-taking intent first
        note_result = self._check_note_intent(user_input)
        if note_result:
            return note_result

        # Phase 1: Sensing
        perception_report = self._sense(user_input)

        # Phase 2: Bootstrap check
        if self.bootstrap.is_active:
            result = self._handle_bootstrap(user_input, perception_report)
            if result:
                return result

        # Phase 3: Slow loop (authority decisions)
        gate_transitions = self._slow_loop_tick(user_input, perception_report)

        # Phase 4: Fast loop (execution)
        response, altitude = self._fast_loop_execute(user_input, perception_report)

        # Phase 5: Continuous evaluation
        quality_health = self._post_execution_eval(user_input, response)

        # Update conversation history and persist
        self._conversation_history.append({"role": "user", "content": user_input})
        self._conversation_history.append({"role": "assistant", "content": response})
        self._save_conversation_history()

        loop_result = LoopResult(
            response=response,
            stance=self.stance.current.value,
            altitude=altitude,
            bootstrap_active=False,
            gate_transitions=gate_transitions,
            quality_health=quality_health,
            turn_number=self._turn_count
        )

        # Call response generated hook if set
        if self._on_response_generated:
            self._on_response_generated(response, loop_result)

        return loop_result

    def _sense(self, user_input: str) -> "PerceptionReport":
        """Phase 1: Perception sensing."""
        context = PerceptionContext(
            user_input=user_input,
            conversation_history=self._conversation_history,
            session_duration=self._turn_count * 60  # Rough estimate
        )
        return self.perception.sense(context)

    def _check_note_intent(self, user_input: str) -> Optional[LoopResult]:
        """Check if user wants to make a note and handle it."""
        note_type = self.notes.detect_note_intent(user_input)
        if not note_type:
            return None

        # Get context from last assistant message
        context = ""
        if self._conversation_history:
            for msg in reversed(self._conversation_history):
                if msg["role"] == "assistant":
                    context = msg["content"]
                    break

        # Extract note content
        content = self.notes.extract_note_content(user_input, context)

        # Add the note
        confirmation = self.notes.add_note(note_type, content)

        # Update conversation history and persist
        self._conversation_history.append({"role": "user", "content": user_input})
        self._conversation_history.append({"role": "assistant", "content": confirmation})
        self._save_conversation_history()

        return LoopResult(
            response=confirmation,
            stance=self.stance.current.value,
            altitude="L1",  # Quick action
            bootstrap_active=self.bootstrap.is_active,
            gate_transitions=[],
            quality_health="healthy",
            turn_number=self._turn_count
        )

    def _handle_bootstrap(
        self,
        user_input: str,
        perception: "PerceptionReport"
    ) -> Optional[LoopResult]:
        """Handle bootstrap mode interaction."""
        result = self.bootstrap.process_input(user_input)

        if result.get("transition_proposal"):
            # Bootstrap complete, transition to normal operation
            user_name = self.bootstrap.get_user_name()

            # Call bootstrap complete hook if set
            if self._on_bootstrap_complete:
                self._on_bootstrap_complete(user_name)

            # Build messages with current input
            messages = list(self._conversation_history)
            messages.append({"role": "user", "content": user_input})

            # Generate completion using proper multi-turn
            system = f"""Bootstrap complete. User's name is: {user_name}
Give a brief, warm acknowledgment (1-2 sentences) that:
1. Thanks them for sharing
2. Shows you're ready to be their cognitive partner
3. Asks what they'd like to work on or talk about
Be genuine and direct, not effusive."""

            # Apply prompt enhancer if set
            if self._prompt_enhancer:
                system = self._prompt_enhancer(system)

            response = self.executor._llm(system=system, messages=messages)

            # Update conversation history and persist
            self._conversation_history.append({"role": "user", "content": user_input})
            self._conversation_history.append({"role": "assistant", "content": response})
            self._save_conversation_history()

            return LoopResult(
                response=response,
                stance="sensemaking",
                altitude="L3",
                bootstrap_active=False,
                gate_transitions=["Bootstrap complete"],
                quality_health="healthy",
                turn_number=self._turn_count
            )

        # Still in bootstrap - generate response for current stage
        next_prompt = result.get("next_prompt", "")
        user_name = result.get("user_name", "")
        stage = self.bootstrap.current_stage.value

        # Build messages with current input
        messages = list(self._conversation_history)
        messages.append({"role": "user", "content": user_input})

        # System prompt for this bootstrap stage
        system = f"""You are introducing yourself to a new user. Stage: {stage}
{f"User's name is: {user_name}" if user_name else ""}
{f'Lead into this question naturally: "{next_prompt}"' if next_prompt else ''}

Respond naturally in 2-3 sentences:
- Acknowledge what they shared warmly but briefly
- Be genuine and direct"""

        # Apply prompt enhancer if set
        if self._prompt_enhancer:
            system = self._prompt_enhancer(system)

        response = self.executor._llm(system=system, messages=messages)

        # Update conversation history and persist
        self._conversation_history.append({"role": "user", "content": user_input})
        self._conversation_history.append({"role": "assistant", "content": response})
        self._save_conversation_history()

        return LoopResult(
            response=response,
            stance="sensemaking",
            altitude="L3",
            bootstrap_active=True,
            gate_transitions=[],
            quality_health="healthy",
            turn_number=self._turn_count
        )

    def _slow_loop_tick(
        self,
        user_input: str,
        perception: "PerceptionReport"
    ) -> list[str]:
        """Phase 3: Slow loop authority decisions."""
        transitions = []

        # Check commitment expiry
        expiry_proposal = self.commitment.check_expiry()
        if expiry_proposal:
            self.proposal_buffer.add_gate_proposal(expiry_proposal)

        # Decrement commitment turn counter
        if self.commitment.has_active_commitment():
            self.commitment.decrement_turn()

        # Tick gate controller (update cooldowns)
        self.gate_controller.tick()

        # Process proposals
        if self.proposal_buffer.has_proposals():
            results = self.gate_controller.process_proposals(
                self.proposal_buffer,
                self.PROPOSAL_PRIORITY
            )
            for result in results:
                if result.success:
                    transitions.append(
                        f"{result.gate}: {result.from_stance.value} -> {result.to_stance.value}"
                    )
                    # Call gate transition hook if set
                    if self._on_gate_transition:
                        self._on_gate_transition(
                            result.gate,
                            result.from_stance.value,
                            result.to_stance.value
                        )

            # Clear processed proposals
            self.proposal_buffer.clear()

        # Update HRM with current commitment
        self.hrm.set_commitment(self.commitment.get_current())

        return transitions

    def _fast_loop_execute(
        self,
        user_input: str,
        perception: "PerceptionReport"
    ) -> tuple[str, str]:
        """Phase 4: Fast loop execution."""
        # Get progress state
        progress = self.fast_memory.get_progress()

        # HRM assessment
        hrm_assessment = self.hrm.assess(user_input, perception, progress)

        # Build execution context
        context = ExecutionContext(
            user_input=user_input,
            stance=self.stance.current,
            hrm_assessment=hrm_assessment,
            commitment=self.commitment.get_current(),
            conversation_history=self._conversation_history
        )

        # Execute
        result = self.executor.execute(context)

        return result.response, result.altitude_used.value

    def _post_execution_eval(
        self,
        user_input: str,
        response: str
    ) -> str:
        """Phase 5: Post-execution continuous evaluation."""
        execution_result = self.executor.get_last_result()
        if not execution_result:
            return "unknown"

        eval_result = self.continuous_eval.evaluate(
            execution_result,
            user_input,
            self.commitment.get_current(),
            self.fast_memory.get_progress()
        )

        # Run contrast detection
        perception_report = self.perception.get_last_report()
        if perception_report:
            contrast_context = ContrastContext(
                perception=perception_report,
                execution=execution_result,
                commitment=self.commitment.get_current(),
                user_input=user_input
            )
            contrast_report = self.contrast.detect(contrast_context)
            if contrast_report:
                self.proposal_buffer.add_contrast_report(contrast_report)

        return eval_result.overall_health

    # Public API for commitment creation

    def create_commitment(
        self,
        frame: str,
        success_criteria: list[str] = None,
        non_goals: list[str] = None,
        turns: int = 20
    ) -> bool:
        """Create a new commitment (requires appropriate stance)."""
        if self.stance.current not in [Stance.SENSEMAKING, Stance.DISCOVERY]:
            return False

        # Attempt commitment gate
        result = self.gate_controller.attempt_gate(
            "commitment",
            f"Committing to: {frame}"
        )

        if result.success:
            self.commitment.create(
                frame=frame,
                success_criteria=success_criteria or [],
                non_goals=non_goals or [],
                turns=turns
            )
            return True

        return False

    def request_evaluation(self, reason: str) -> bool:
        """Request evaluation gate transition."""
        result = self.gate_controller.attempt_gate("evaluation", reason)
        return result.success

    def trigger_emergency(self, reason: str) -> bool:
        """Trigger emergency gate (costly)."""
        result = self.gate_controller.attempt_emergency(reason)
        return result.success

    # State inspection

    def get_state(self) -> dict:
        """Get current loop state."""
        return {
            "turn": self._turn_count,
            "stance": self.stance.current.value,
            "commitment": self.commitment.get_summary(),
            "bootstrap_active": self.bootstrap.is_active,
            "gate_state": self.gate_controller.get_state(),
            "health": self.continuous_eval.get_health_summary()
        }

    def get_history(self) -> list[dict]:
        """Get conversation history."""
        return self._conversation_history.copy()

    def generate_greeting(self) -> str:
        """
        Generate a natural greeting for session start.

        Uses the LLM to create a context-aware welcome message
        based on current state (Bootstrap, returning user, etc.).
        """
        # Build context for greeting generation
        if self.bootstrap.is_active:
            # For bootstrap, use the intro greeting directly
            greeting = self.bootstrap.INTRO_GREETING
        else:
            # Check if returning user with existing commitment
            commitment = self.commitment.get_current()
            if commitment:
                system = f"""You are resuming a conversation.
Active commitment: {commitment.frame}
Turns remaining: {commitment.turns_remaining}

Generate a warm, natural welcome (2-3 sentences) that:
1. Acknowledges you're picking up where you left off
2. Briefly references the ongoing work
3. Invites them to continue"""
            else:
                system = """Generate a warm, natural welcome (1-2 sentences) that:
1. Greets the user genuinely
2. Opens space for them to share what's on their mind
3. Feels conversational, not corporate

Do not use phrases like "I'm here to help" or "How can I assist you today"."""

            # Use proper LLM call with system prompt
            greeting = self.executor._llm(system=system, prompt="Generate greeting")

        # Store as assistant turn in history
        self._conversation_history.append({
            "role": "assistant",
            "content": greeting
        })
        self._save_conversation_history()

        return greeting

    def _load_conversation_history(self):
        """Load conversation history from disk."""
        if self._conversation_file.exists():
            try:
                data = json.loads(self._conversation_file.read_text())
                self._conversation_history = data.get("messages", [])
                self._turn_count = data.get("turn_count", 0)
            except (json.JSONDecodeError, TypeError):
                self._conversation_history = []
                self._turn_count = 0

    def _save_conversation_history(self):
        """Save conversation history to disk."""
        # Keep last 100 messages to avoid unbounded growth
        recent = self._conversation_history[-100:]
        data = {
            "messages": recent,
            "turn_count": self._turn_count,
            "last_saved": datetime.now().isoformat()
        }
        self._conversation_file.write_text(json.dumps(data, indent=2))

    def clear_conversation(self):
        """Clear conversation history (start fresh)."""
        self._conversation_history = []
        self._turn_count = 0
        if self._conversation_file.exists():
            self._conversation_file.unlink()
        # Also clear bootstrap to start fresh
        self.slow_memory.clear_bootstrap()
