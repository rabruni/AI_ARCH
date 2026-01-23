"""Signal Display - Formats signals for terminal UI.

Provides:
- Compact status strip for message metadata
- Detailed signal panels for inspection
- Color coding for signal states
"""

from locked_system.signals.state import SignalState, Trend, Sentiment, HealthStatus


class Colors:
    """ANSI color codes."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Status colors
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    CYAN = '\033[36m'
    MAGENTA = '\033[35m'
    BLUE = '\033[34m'
    WHITE = '\033[37m'

    # Bright variants
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_CYAN = '\033[96m'


class SignalDisplay:
    """Formats signals for display."""

    # Altitude visual indicators
    ALTITUDE_BARS = {
        'L1': '▁',
        'L2': '▂',
        'L3': '▃',
        'L4': '▄',
    }

    # Trust level indicators
    TRUST_DOTS = {
        'high': '●',      # > 0.7
        'medium': '◐',    # 0.4 - 0.7
        'low': '○',       # < 0.4
    }

    # Trend arrows
    TREND_ARROWS = {
        Trend.UP: '↑',
        Trend.FLAT: '→',
        Trend.DOWN: '↓',
    }

    # Learning indicators
    LEARNING_DOTS = {
        'active': '◉',    # Currently writing
        'recent': '◐',    # Wrote recently
        'idle': '·',      # No activity
    }

    # Sentiment indicators
    SENTIMENT_SYMBOLS = {
        Sentiment.POSITIVE: '+',
        Sentiment.NEUTRAL: '~',
        Sentiment.NEGATIVE: '-',
    }

    # Alignment indicators
    ALIGNMENT_SYMBOLS = {
        'aligned': '◈',    # On frame
        'drifting': '◇',   # Drifting
    }

    def format_status_strip(self, state: SignalState, compact: bool = True) -> str:
        """
        Format compact status strip for display after messages.

        Compact: eval · L3▃ · ●↑ · ◉ · #63
        Full:    eval · L3▃ · trust:●↑ · learn:◉ · prog:↑ · #63
        """
        parts = []

        # Stance (abbreviated)
        stance_abbrev = {
            'sensemaking': 'sense',
            'discovery': 'disc',
            'execution': 'exec',
            'evaluation': 'eval',
        }
        stance = stance_abbrev.get(state.stance, state.stance[:4])
        stance_color = self._stance_color(state.stance)
        parts.append(f"{stance_color}{stance}{Colors.RESET}")

        # Altitude with bar
        alt_bar = self.ALTITUDE_BARS.get(state.altitude, '▂')
        alt_color = self._altitude_color(state.altitude)
        parts.append(f"{alt_color}{state.altitude}{alt_bar}{Colors.RESET}")

        if compact:
            # Compact: combined indicators
            indicators = self._format_compact_indicators(state)
            parts.append(indicators)
        else:
            # Full: labeled indicators
            parts.append(self._format_trust_indicator(state))
            parts.append(self._format_learning_indicator(state))
            parts.append(self._format_progress_indicator(state))

        # Turn number
        parts.append(f"{Colors.DIM}#{state.turn}{Colors.RESET}")

        return ' · '.join(parts)

    def _format_compact_indicators(self, state: SignalState) -> str:
        """Format compact indicator cluster: ●↑◉"""
        parts = []

        # Trust dot with color
        trust_level = 'high' if state.trust > 0.7 else ('medium' if state.trust > 0.4 else 'low')
        trust_dot = self.TRUST_DOTS[trust_level]
        trust_color = self._trust_color(state.trust)

        # Trust trend arrow
        trust_arrow = self.TREND_ARROWS[state.trust_trend]

        parts.append(f"{trust_color}{trust_dot}{trust_arrow}{Colors.RESET}")

        # Learning indicator
        if state.learning_active:
            parts.append(f"{Colors.BRIGHT_CYAN}{self.LEARNING_DOTS['active']}{Colors.RESET}")
        elif state.writes_this_session > 0:
            parts.append(f"{Colors.CYAN}{self.LEARNING_DOTS['recent']}{Colors.RESET}")

        # Progress arrow (if not flat)
        if state.progress != Trend.FLAT:
            prog_arrow = self.TREND_ARROWS[state.progress]
            prog_color = Colors.GREEN if state.progress == Trend.UP else Colors.RED
            parts.append(f"{prog_color}{prog_arrow}{Colors.RESET}")

        # Alignment warning (only if drifting)
        if state.alignment_drift:
            parts.append(f"{Colors.YELLOW}{self.ALIGNMENT_SYMBOLS['drifting']}{Colors.RESET}")

        return ''.join(parts)

    def _format_trust_indicator(self, state: SignalState) -> str:
        """Format labeled trust indicator."""
        trust_level = 'high' if state.trust > 0.7 else ('medium' if state.trust > 0.4 else 'low')
        trust_dot = self.TRUST_DOTS[trust_level]
        trust_arrow = self.TREND_ARROWS[state.trust_trend]
        trust_color = self._trust_color(state.trust)
        return f"trust:{trust_color}{trust_dot}{trust_arrow}{Colors.RESET}"

    def _format_learning_indicator(self, state: SignalState) -> str:
        """Format labeled learning indicator."""
        if state.learning_active:
            return f"learn:{Colors.BRIGHT_CYAN}{self.LEARNING_DOTS['active']}{Colors.RESET}"
        elif state.writes_this_session > 0:
            return f"learn:{Colors.CYAN}{self.LEARNING_DOTS['recent']}({state.writes_this_session}){Colors.RESET}"
        return f"learn:{Colors.DIM}{self.LEARNING_DOTS['idle']}{Colors.RESET}"

    def _format_progress_indicator(self, state: SignalState) -> str:
        """Format labeled progress indicator."""
        arrow = self.TREND_ARROWS[state.progress]
        color = Colors.GREEN if state.progress == Trend.UP else (
            Colors.RED if state.progress == Trend.DOWN else Colors.DIM
        )
        return f"prog:{color}{arrow}{Colors.RESET}"

    def format_trust_panel(self, state: SignalState, events: list = None) -> str:
        """Format detailed trust panel for :trust command."""
        lines = []

        # Header
        lines.append(f"{Colors.BOLD}TRUST STATUS{Colors.RESET}")
        lines.append("")

        # Current score with visual bar
        bar_width = 20
        filled = int(state.trust * bar_width)
        empty = bar_width - filled
        trust_color = self._trust_color(state.trust)
        bar = f"{trust_color}{'█' * filled}{Colors.DIM}{'░' * empty}{Colors.RESET}"

        lines.append(f"  Score: {bar} {trust_color}{state.trust:.2f}{Colors.RESET}")

        # Trend
        trend_arrow = self.TREND_ARROWS[state.trust_trend]
        trend_word = state.trust_trend.value
        lines.append(f"  Trend: {trend_arrow} {trend_word}")

        # Event count
        lines.append(f"  Events: {state.trust_events} recorded")

        # Recent events
        if events:
            lines.append("")
            lines.append(f"  {Colors.DIM}Recent events:{Colors.RESET}")
            for event in events[-5:]:
                weight = event['weight']
                symbol = '+' if weight > 0 else ''
                color = Colors.GREEN if weight > 0 else Colors.RED
                lines.append(f"    {color}{symbol}{weight:.2f}{Colors.RESET} {event['event']}")

        return '\n'.join(lines)

    def format_learning_panel(self, state: SignalState) -> str:
        """Format detailed learning panel for :learn command."""
        lines = []

        # Header
        lines.append(f"{Colors.BOLD}LEARNING STATUS{Colors.RESET}")
        lines.append("")

        # Current activity
        if state.learning_active:
            lines.append(f"  Status: {Colors.BRIGHT_CYAN}ACTIVE{Colors.RESET}")
            lines.append(f"  Target: {state.learning_target}")
        else:
            lines.append(f"  Status: {Colors.DIM}idle{Colors.RESET}")

        # Session writes
        lines.append(f"  Writes this session: {state.writes_this_session}")

        return '\n'.join(lines)

    def format_full_panel(self, state: SignalState) -> str:
        """Format complete signal panel for debug/inspection."""
        lines = []

        lines.append(f"{Colors.BOLD}SIGNAL STATE{Colors.RESET}")
        lines.append("")

        # Altitude
        alt_bar = self.ALTITUDE_BARS.get(state.altitude, '▂')
        lines.append(f"  Altitude: {state.altitude} {alt_bar}")
        if state.altitude_reason:
            lines.append(f"            {Colors.DIM}{state.altitude_reason}{Colors.RESET}")

        # Trust
        trust_color = self._trust_color(state.trust)
        lines.append(f"  Trust:    {trust_color}{state.trust:.2f}{Colors.RESET} {self.TREND_ARROWS[state.trust_trend]}")

        # Learning
        learn_status = "active" if state.learning_active else f"{state.writes_this_session} writes"
        lines.append(f"  Learning: {learn_status}")

        # Progress
        prog_color = Colors.GREEN if state.progress == Trend.UP else (
            Colors.RED if state.progress == Trend.DOWN else Colors.DIM
        )
        lines.append(f"  Progress: {prog_color}{self.TREND_ARROWS[state.progress]} ({state.progress_score:.2f}){Colors.RESET}")

        # Sentiment
        sent_symbol = self.SENTIMENT_SYMBOLS[state.sentiment]
        lines.append(f"  Sentiment: {sent_symbol} {state.sentiment.value} ({state.sentiment_confidence:.0%} conf)")

        # Alignment
        align_symbol = self.ALIGNMENT_SYMBOLS['drifting' if state.alignment_drift else 'aligned']
        lines.append(f"  Alignment: {align_symbol} {state.alignment:.2f}")

        # Health
        health_color = self._health_color(state.health)
        lines.append(f"  Health:   {health_color}{state.health.value}{Colors.RESET}")

        return '\n'.join(lines)

    def _stance_color(self, stance: str) -> str:
        """Get color for stance."""
        colors = {
            'sensemaking': Colors.MAGENTA,
            'discovery': Colors.CYAN,
            'execution': Colors.GREEN,
            'evaluation': Colors.YELLOW,
        }
        return colors.get(stance.lower(), Colors.WHITE)

    def _altitude_color(self, altitude: str) -> str:
        """Get color for altitude."""
        colors = {
            'L1': Colors.DIM,
            'L2': Colors.WHITE,
            'L3': Colors.CYAN,
            'L4': Colors.BRIGHT_CYAN,
        }
        return colors.get(altitude, Colors.WHITE)

    def _trust_color(self, trust: float) -> str:
        """Get color for trust level."""
        if trust > 0.7:
            return Colors.GREEN
        elif trust > 0.4:
            return Colors.YELLOW
        return Colors.RED

    def _health_color(self, health: HealthStatus) -> str:
        """Get color for health status."""
        colors = {
            HealthStatus.HEALTHY: Colors.GREEN,
            HealthStatus.CONCERNING: Colors.YELLOW,
            HealthStatus.CRITICAL: Colors.RED,
        }
        return colors.get(health, Colors.DIM)
