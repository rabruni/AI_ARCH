#!/usr/bin/env python3
"""Demo chat with the Front-Door Agent."""

import sys
import os
from pathlib import Path

# Add parent directory to path so locked_system can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from locked_system.front_door import FrontDoorAgent
from locked_system.agents import AgentContext

# ANSI colors for agent announcements
COLORS = {
    'front_door': '\033[94m',  # Blue
    'writer': '\033[92m',       # Green
    'editor': '\033[93m',       # Yellow
    'analyst': '\033[95m',      # Magenta
    'monitor': '\033[96m',      # Cyan
    'reset': '\033[0m',
    'dim': '\033[2m',
    'bold': '\033[1m',
}

# LLM setup
def create_llm():
    """Create LLM callable if API key available."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None, "No API key - routing only mode"

    try:
        import anthropic
        client = anthropic.Anthropic()

        def call_llm(system: str, user_msg: str, agent_context: dict = None) -> str:
            """Call Claude with context."""
            full_system = f"""{system}

You are operating as part of a multi-agent system. Current context:
- Active agent: {agent_context.get('agent_id', 'front_door') if agent_context else 'front_door'}
- Signal detected: {agent_context.get('signal', 'none') if agent_context else 'none'}
- Emotional state: {agent_context.get('emotional_signals', {}) if agent_context else {}}

Respond naturally and helpfully. Be concise."""

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                system=full_system,
                messages=[{"role": "user", "content": user_msg}]
            )
            return response.content[0].text

        return call_llm, "Claude (sonnet)"
    except Exception as e:
        return None, f"LLM error: {e}"

def announce_agent(agent_id: str, action: str = "engaged"):
    """Print agent announcement to UI."""
    color = COLORS.get(agent_id, COLORS['reset'])
    reset = COLORS['reset']
    dim = COLORS['dim']
    print(f"\n{dim}[{color}{agent_id}{reset}{dim} {action}]{reset}")

def announce_bundle(bundle):
    """Announce all agents in a bundle."""
    dim = COLORS['dim']
    reset = COLORS['reset']
    bold = COLORS['bold']
    print(f"\n{dim}━━━ Bundle: {bold}{bundle.name}{reset}{dim} ━━━{reset}")
    for agent_id in bundle.agents:
        announce_agent(agent_id, "ready")

def main():
    agent = FrontDoorAgent()
    llm, llm_status = create_llm()

    print("=" * 50)
    print("Front-Door Agent Demo")
    print(f"LLM: {llm_status}")
    print("=" * 50)
    print("Commands: :q quit, :signals set emotional state, :routing toggle routing info")

    # Announce front-door agent on startup
    announce_agent("front_door", "initialized")

    # Default emotional signals
    emotional_signals = {
        "confidence": "high",
        "frustration": "none",
        "cognitive_load": "low",
        "urgency": "none",
        "flow": "false"
    }

    # Conversation history for multi-turn
    history = []
    show_routing = True  # Show routing info by default
    current_agent = "front_door"

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input == ":q":
                announce_agent(current_agent, "shutting down")
                print("Goodbye!")
                break

            if user_input == ":routing":
                show_routing = not show_routing
                print(f"Routing info: {'ON' if show_routing else 'OFF'}")
                continue

            if user_input == ":signals":
                print("\nCurrent signals:", emotional_signals)
                print("\nSet signals (e.g., 'frustration=high' or 'flow=true'):")
                sig_input = input("> ").strip()
                if "=" in sig_input:
                    key, val = sig_input.split("=", 1)
                    if key.strip() in emotional_signals:
                        emotional_signals[key.strip()] = val.strip()
                        print(f"Set {key.strip()} = {val.strip()}")
                continue

            # Announce front-door processing
            announce_agent("front_door", "routing")

            # Process through front-door for routing decisions
            context = AgentContext(
                user_input=user_input,
                emotional_signals=emotional_signals,
                system_context={}
            )

            packet = agent.process(context)

            # Check if a bundle was proposed and announce it
            work_type = agent._signal_detector.detect_work_type(user_input)
            selected_agent = "front_door"
            if work_type:
                bundle = agent.propose_bundle(work_type)
                if bundle:
                    announce_bundle(bundle)
                    # Select primary agent from bundle
                    if bundle.agents:
                        selected_agent = bundle.agents[0]
                        announce_agent(selected_agent, "engaged")
                        current_agent = selected_agent

            # Show routing info if enabled
            if show_routing and packet.proposals:
                dim = COLORS['dim']
                reset = COLORS['reset']
                print(f"{dim}  [Routing]{reset}")
                print(f"{dim}    Signal: {packet.traces.get('signal_detected', 'none')}{reset}")
                for p in packet.proposals:
                    print(f"{dim}    Gate: {p.gate or p.tool_id}{reset}")

            # Generate LLM response
            if llm:
                agent_context = {
                    'agent_id': selected_agent,
                    'signal': packet.traces.get('signal_detected', 'none'),
                    'emotional_signals': emotional_signals,
                }

                system_prompt = f"""You are {selected_agent}, a specialized agent.
Your role: {get_agent_role(selected_agent)}
The front-door router detected: {packet.traces.get('signal_detected', 'general conversation')}
Router suggested: {packet.message}"""

                response = llm(system_prompt, user_input, agent_context)

                # Show response with agent attribution
                color = COLORS.get(selected_agent, COLORS['reset'])
                reset = COLORS['reset']
                print(f"\n{color}{selected_agent}:{reset} {response}")
            else:
                # No LLM - just show routing message
                color = COLORS['front_door']
                reset = COLORS['reset']
                print(f"\n{color}front_door:{reset} {packet.message}")

        except KeyboardInterrupt:
            announce_agent(current_agent, "interrupted")
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def get_agent_role(agent_id: str) -> str:
    """Get role description for agent."""
    roles = {
        'front_door': 'Cognitive router and user interface agent',
        'writer': 'Document creation and content writing specialist',
        'editor': 'Review, refine, and improve written content',
        'analyst': 'Data analysis and research specialist',
        'monitor': 'System monitoring and status reporting',
    }
    return roles.get(agent_id, 'General assistant')

if __name__ == "__main__":
    main()
