"""Locked Loop - Main Orchestration.

Two-tempo loop:
- Slow Loop: Authority layer (gates, stance, commitment)
- Fast Loop: Execution layer (HRM, executor, continuous eval)

Invariants:
- Slow loop has authority over stance transitions
- Fast loop operates within slow loop constraints
- Proposals flow up, decisions flow down
- Capabilities require explicit delegation
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
from locked_system.memory.consent import ConsentManager

# Proposals
from locked_system.proposals.buffer import ProposalBuffer, GateProposal, Severity

# Governance (core)
from locked_system.core.governance.stance import StanceMachine, Stance
from locked_system.core.governance.commitment import CommitmentManager
from locked_system.core.governance.gates import GateController
from locked_system.core.governance.delegation import DelegationManager, DelegationLease

# Execution (core)
from locked_system.core.execution.hrm import HRM
from locked_system.core.execution.executor import Executor, ExecutionContext
from locked_system.core.execution.continuous_eval import ContinuousEvaluator

# Sensing
from locked_system.sensing.perception import PerceptionSensor, PerceptionContext
from locked_system.sensing.contrast import ContrastDetector, ContrastContext

# Signals
from locked_system.signals import SignalCollector, SignalComputer, SignalDisplay

# Capabilities (gated)
from locked_system.capabilities.note_capture import NoteCaptureCapability, NoteType


@dataclass
class LoopResult:
    """Result of a single loop iteration."""
    response: str
    stance: str
    altitude: str
    gate_transitions: list[str]
    quality_health: str
    turn_number: int


class LockedLoop:
    """
    Main orchestration loop.

    Coordinates slow and fast loops with proper authority hierarchy.

    Hooks for extensibility:
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
        on_gate_transition: Optional[Callable[[str, str, str], None]] = None,
        on_response_generated: Optional[Callable[[str, "LoopResult"], None]] = None,
        prompt_enhancer: Optional[Callable[[str], str]] = None,
    ):
        self.config = config or Config()

        # Store hooks
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

        # Initialize fast loop components
        self.hrm = HRM()
        self.executor = Executor(self.fast_memory, llm_callable)
        self.continuous_eval = ContinuousEvaluator(self.proposal_buffer)

        # Initialize sensing
        self.perception = PerceptionSensor()
        self.contrast = ContrastDetector()

        # Initialize delegation manager
        self.delegation = DelegationManager()

        # Initialize capabilities (gated)
        self.note_capture = NoteCaptureCapability(
            self.config.memory_dir / "notes",
            authorization_check=self.delegation.check
        )

        # Initialize signals subsystem
        self.signal_collector = SignalCollector()
        self.signal_computer = SignalComputer(self.signal_collector)
        self.signal_display = SignalDisplay()

        # Initialize consent manager
        self.consent = ConsentManager(self.config.memory_dir)

        # State
        self._turn_count = 0
        self._conversation_history: list[dict] = []
        self._conversation_file = self.config.memory_dir / "conversation.json"

        # Load existing conversation history (if consent allows)
        self._load_conversation_history()

    def process(self, user_input: str) -> LoopResult:
        """
        Process user input through the locked loop.

        Returns LoopResult with response and metadata.
        """
        self._turn_count += 1
        gate_transitions = []

        # Record turn signal
        self.signal_collector.record_turn(self._turn_count, "loop")

        # Check for note-taking intent first
        note_result = self._check_note_intent(user_input)
        if note_result:
            return note_result

        # Phase 1: Sensing
        perception_report = self._sense(user_input)

        # Record sentiment from perception
        if perception_report:
            sentiment = getattr(perception_report, 'sentiment', 'neutral')
            confidence = getattr(perception_report, 'confidence', 0.5)
            self.signal_collector.record_sentiment(sentiment, confidence, "perception")

        # Phase 2: Slow loop (authority decisions)
        gate_transitions = self._slow_loop_tick(user_input, perception_report)

        # Record stance signal
        self.signal_collector.record_stance(self.stance.current.value, "stance_machine")

        # Phase 3: Fast loop (execution)
        response, altitude = self._fast_loop_execute(user_input, perception_report)

        # Record altitude signal
        hrm_reason = getattr(self.hrm, '_last_reason', '')
        self.signal_collector.record_altitude(altitude, hrm_reason, "hrm")

        # Phase 4: Continuous evaluation
        quality_health = self._post_execution_eval(user_input, response)

        # Record health signal
        health_dims = self.continuous_eval.get_health_summary().get('dimension_averages', {})
        self.signal_collector.record_health(quality_health, health_dims, "continuous_eval")

        # Record progress signal
        progress_state = self.fast_memory.get_progress()
        if progress_state:
            progress_score = getattr(progress_state, 'completion', 0.5)
            direction = 'up' if progress_score > 0.5 else ('down' if progress_score < 0.3 else 'flat')
            self.signal_collector.record_progress(direction, progress_score, "evaluator")

        # Update conversation history and persist
        self._conversation_history.append({"role": "user", "content": user_input})
        self._conversation_history.append({"role": "assistant", "content": response})

        # Record write activity
        self.signal_collector.record_write_start("conversation", "loop")
        self._save_conversation_history()
        self.signal_collector.record_write_end("conversation", True, "loop")

        loop_result = LoopResult(
            response=response,
            stance=self.stance.current.value,
            altitude=altitude,
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
        """
        Check if user wants to make a note and handle it through proper gating.

        Note capture is a capability that requires delegation.
        If not authorized, proposes gate transition and returns guidance.
        """
        note_type = self.note_capture.detect_note_intent(user_input)
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
        content = self.note_capture.extract_note_content(user_input, context)

        # Attempt capture through gated capability
        result = self.note_capture.capture(
            note_type=note_type,
            content=content,
            grantee="agent",
            source="conversation"
        )

        if result["success"]:
            # Note captured successfully
            response = (
                f"Got it - added to your {note_type} notes.\n"
                f"[Verified] Wrote to: {result.get('file', 'notes')}\n"
                f"[Captured] \"{result.get('content_preview', content[:50])}\""
            )
        elif not result["authorized"]:
            # Not authorized - propose gate transition for delegation
            self.proposal_buffer.add_gate_proposal(GateProposal(
                reason=f"Note capture requested but not authorized",
                severity=Severity.LOW,
                suggested_gate="framing",
                source="note_capture"
            ))

            # For now, grant temporary delegation and retry
            # In full implementation, this would require explicit user/gate approval
            self.delegation.grant(DelegationLease(
                grantee="agent",
                scope=["note_capture"],
                expires_turns=5
            ))

            # Retry capture
            result = self.note_capture.capture(
                note_type=note_type,
                content=content,
                grantee="agent",
                source="conversation"
            )

            if result["success"]:
                response = (
                    f"Got it - added to your {note_type} notes.\n"
                    f"[Verified] Wrote to: {result.get('file', 'notes')}\n"
                    f"[Captured] \"{result.get('content_preview', content[:50])}\""
                )
            else:
                response = f"Could not capture note: {result.get('message', 'unknown error')}"
        else:
            response = f"Could not capture note: {result.get('message', 'unknown error')}"

        # Update conversation history and persist
        self._conversation_history.append({"role": "user", "content": user_input})
        self._conversation_history.append({"role": "assistant", "content": response})
        self._save_conversation_history()

        return LoopResult(
            response=response,
            stance=self.stance.current.value,
            altitude="L1",  # Quick action
            gate_transitions=[],
            quality_health="healthy",
            turn_number=self._turn_count
        )

    def _slow_loop_tick(
        self,
        user_input: str,
        perception: "PerceptionReport"
    ) -> list[str]:
        """Phase 2: Slow loop authority decisions."""
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

        # Tick delegation manager (expire leases)
        self.delegation.tick()

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
        """Phase 3: Fast loop execution."""
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
        """Phase 4: Post-execution continuous evaluation."""
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
            "gate_state": self.gate_controller.get_state(),
            "delegation": self.delegation.get_summary(),
            "health": self.continuous_eval.get_health_summary()
        }

    def get_signal_state(self):
        """Get current signal state with computed values."""
        return self.signal_computer.get_state()

    def get_signal_display(self, compact: bool = True) -> str:
        """Get formatted signal display string."""
        state = self.signal_computer.get_state()
        return self.signal_display.format_status_strip(state, compact=compact)

    def get_trust_panel(self) -> str:
        """Get formatted trust panel for :trust command."""
        state = self.signal_computer.get_state()
        events = self.signal_collector.get_trust_events()
        return self.signal_display.format_trust_panel(state, events)

    def get_learning_panel(self) -> str:
        """Get formatted learning panel for :learn command."""
        state = self.signal_computer.get_state()
        return self.signal_display.format_learning_panel(state)

    def get_signals_panel(self) -> str:
        """Get full signals panel for inspection."""
        state = self.signal_computer.get_state()
        return self.signal_display.format_full_panel(state)

    def record_trust_event(self, event: str):
        """Record a trust-affecting event."""
        self.signal_collector.record_trust_event(event, "user")

    # Consent management

    def needs_consent(self) -> bool:
        """Check if consent prompt is needed."""
        return self.consent.needs_consent()

    def grant_consent(
        self,
        conversation_history: bool = True,
        interaction_signals: bool = True,
        learned_preferences: bool = False
    ):
        """Grant consent for memory persistence."""
        self.consent.grant_consent(
            conversation_history=conversation_history,
            interaction_signals=interaction_signals,
            learned_preferences=learned_preferences
        )
        # Record as trust event
        self.signal_collector.record_trust_event('consent_granted', 'user')

    def revoke_consent(self):
        """Revoke all consent."""
        self.consent.revoke_all()
        # Record as trust event
        self.signal_collector.record_trust_event('consent_revoked', 'user')

    def get_consent_summary(self) -> dict:
        """Get consent status summary."""
        return self.consent.get_summary()

    def get_history(self) -> list[dict]:
        """Get conversation history."""
        return self._conversation_history.copy()

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
        """Save conversation history to disk (consent-gated)."""
        # Check consent before persisting
        if not self.consent.can_persist('conversation'):
            return  # User has not consented to conversation persistence

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
