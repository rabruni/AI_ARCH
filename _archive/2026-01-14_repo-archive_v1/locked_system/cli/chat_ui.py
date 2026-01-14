"""Chat UI - iMessage-style terminal interface with readline support.

Features:
- Arrow keys and line editing (readline)
- Command history (up/down arrows)
- Clean chat bubble display
- Color-coded messages
- Compact metadata display
"""
import readline
import os
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Optional

# ANSI color codes
class Colors:
    # Reset
    RESET = '\033[0m'

    # Regular colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_WHITE = '\033[47m'
    BG_BRIGHT_BLACK = '\033[100m'

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'


class ChatUI:
    """iMessage-style chat interface."""

    def __init__(self, history_file: Optional[Path] = None, terminal_width: int = None):
        self.history_file = history_file or Path.home() / ".locked_system_history"
        self.terminal_width = terminal_width or self._get_terminal_width()
        self.max_bubble_width = min(70, self.terminal_width - 10)

        # Setup readline
        self._setup_readline()

    def _get_terminal_width(self) -> int:
        """Get terminal width, default to 80 if can't determine."""
        try:
            return os.get_terminal_size().columns
        except OSError:
            return 80

    def _setup_readline(self):
        """Configure readline for better line editing."""
        # Enable tab completion
        readline.parse_and_bind('tab: complete')

        # Enable arrow keys and emacs-style editing
        readline.parse_and_bind('set editing-mode emacs')

        # Enable bracketed paste mode (prevents newlines from submitting on paste)
        readline.parse_and_bind('set enable-bracketed-paste on')

        # Load history
        if self.history_file.exists():
            try:
                readline.read_history_file(str(self.history_file))
            except Exception:
                pass

        # Set history length
        readline.set_history_length(1000)

        # Enable bracketed paste in terminal (fallback for older readline)
        # This tells the terminal to wrap pastes in escape sequences
        print('\033[?2004h', end='', flush=True)

    def save_history(self):
        """Save command history."""
        try:
            readline.write_history_file(str(self.history_file))
        except Exception:
            pass

    def cleanup(self):
        """Clean up terminal state on exit."""
        # Disable bracketed paste mode
        print('\033[?2004l', end='', flush=True)
        self.save_history()

    def clear_screen(self):
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title: str = "Locked System", subtitle: str = None):
        """Print chat header."""
        width = self.terminal_width

        print()
        print(f"{Colors.BOLD}{Colors.CYAN}{'─' * width}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.WHITE}  {title}{Colors.RESET}")
        if subtitle:
            print(f"{Colors.DIM}  {subtitle}{Colors.RESET}")
        print(f"{Colors.CYAN}{'─' * width}{Colors.RESET}")
        print()

    def print_help(self):
        """Print help text."""
        help_text = f"""
{Colors.DIM}Commands (vim-style, prefix with {Colors.CYAN}:{Colors.DIM}):{Colors.RESET}
  {Colors.CYAN}:s{Colors.RESET}  {Colors.DIM}:state{Colors.RESET}        Show current system state
  {Colors.CYAN}:t{Colors.RESET}  {Colors.DIM}:trust{Colors.RESET}        Show trust score and events
  {Colors.CYAN}:l{Colors.RESET}  {Colors.DIM}:learn{Colors.RESET}        Show learning activity
  {Colors.CYAN}:sig{Colors.RESET} {Colors.DIM}:signals{Colors.RESET}     Show all signals
  {Colors.CYAN}:m{Colors.RESET}  {Colors.DIM}:memory{Colors.RESET}       Show memory consent status
  {Colors.CYAN}:n{Colors.RESET}  {Colors.DIM}:notes{Colors.RESET}        Show all recent notes
  {Colors.CYAN}:nd{Colors.RESET} {Colors.DIM}:notes dev{Colors.RESET}    Show developer notes
  {Colors.CYAN}:np{Colors.RESET} {Colors.DIM}:notes personal{Colors.RESET} Show personal notes
  {Colors.CYAN}:c{Colors.RESET}  {Colors.DIM}:clear{Colors.RESET}        Clear the screen
  {Colors.CYAN}:h{Colors.RESET}  {Colors.DIM}:help{Colors.RESET}         Show this help
  {Colors.CYAN}:q{Colors.RESET}  {Colors.DIM}:quit{Colors.RESET}         Quit
  {Colors.CYAN}:commit <goal>{Colors.RESET}    Create a commitment
  {Colors.CYAN}:e <reason>{Colors.RESET}       Trigger emergency gate

{Colors.DIM}Signals legend:{Colors.RESET}
  {Colors.GREEN}●{Colors.RESET}/{Colors.YELLOW}◐{Colors.RESET}/{Colors.RED}○{Colors.RESET}  Trust (high/medium/low)
  {Colors.CYAN}◉{Colors.RESET}/{Colors.DIM}·{Colors.RESET}   Learning (active/idle)
  ↑/→/↓   Progress (up/flat/down)
  L1-L4   Altitude (reactive→reflective)

{Colors.DIM}Keys:{Colors.RESET}
  ↑/↓            Browse command history
  ←/→            Move cursor in line
  Ctrl+A/E       Jump to start/end of line
  Ctrl+W         Delete word before cursor
  Ctrl+U         Clear line
"""
        print(help_text)

    def print_user_message(self, message: str):
        """Print user message (left-aligned, simple style)."""
        # Move cursor up to overwrite the "You: message" input line
        print(f"\033[A\033[K", end="")  # Move up, clear line

        lines = self._wrap_text(message, bg_color=Colors.BG_BRIGHT_BLACK)

        # Calculate bubble width based on visible text length
        max_line_len = max(self._visible_len(line) for line in lines) if lines else 0
        bubble_width = min(max_line_len + 4, self.max_bubble_width)

        # Left-aligned (user on left)
        print()
        for line in lines:
            visible_len = self._visible_len(line)
            pad_needed = bubble_width - 4 - visible_len
            padded_line = line + (' ' * max(0, pad_needed))
            bubble = f"  {padded_line}  "
            print(f"  {Colors.BG_BRIGHT_BLACK}{Colors.WHITE}{bubble}{Colors.RESET}")

        # Timestamp on left
        timestamp = datetime.now().strftime("%H:%M")
        print(f"  {Colors.DIM}{timestamp}{Colors.RESET}")

    def print_assistant_message(self, message: str, metadata: dict = None, signal_strip: str = None):
        """Print assistant message (right-aligned, blue bubble)."""
        lines = self._wrap_text(message, bg_color=Colors.BG_BLUE)

        # Calculate bubble width for consistent appearance
        max_line_len = max(self._visible_len(line) for line in lines) if lines else 0
        bubble_width = min(max_line_len + 4, self.max_bubble_width)

        # Right-align (agent on right)
        padding = max(0, self.terminal_width - bubble_width - 2)

        print()
        for line in lines:
            # Pad line to bubble width for consistent background
            visible_len = self._visible_len(line)
            pad_needed = bubble_width - 4 - visible_len
            padded_line = line + (' ' * max(0, pad_needed))
            bubble = f"  {padded_line}  "
            print(f"{' ' * padding}{Colors.BG_BLUE}{Colors.WHITE}{bubble}{Colors.RESET}")

        # Signal strip (new format) or legacy metadata
        if signal_strip:
            # Signal strip is pre-formatted with ANSI codes
            # Estimate visible length for padding
            strip_visible_len = self._visible_len(signal_strip)
            strip_padding = max(0, self.terminal_width - strip_visible_len - 2)
            print(f"{' ' * strip_padding}{signal_strip}")
        elif metadata:
            meta_parts = []
            if metadata.get('stance'):
                stance_color = self._stance_color(metadata['stance'])
                meta_parts.append(f"{stance_color}{metadata['stance']}{Colors.RESET}")
            if metadata.get('altitude'):
                meta_parts.append(f"{Colors.CYAN}{metadata['altitude']}{Colors.RESET}")
            if metadata.get('health'):
                health_color = self._health_color(metadata['health'])
                meta_parts.append(f"{health_color}●{Colors.RESET}")
            if metadata.get('turn'):
                meta_parts.append(f"{Colors.DIM}#{metadata['turn']}{Colors.RESET}")

            if meta_parts:
                meta_text = f"{' · '.join(meta_parts)}"
                # Estimate visible length (rough)
                meta_visible_len = len(metadata.get('stance', '')) + len(metadata.get('altitude', '')) + 10
                meta_padding = max(0, self.terminal_width - meta_visible_len - 4)
                print(f"{' ' * meta_padding}{Colors.DIM}{meta_text}{Colors.RESET}")
        else:
            timestamp = datetime.now().strftime("%H:%M")
            ts_padding = max(0, self.terminal_width - 7)
            print(f"{' ' * ts_padding}{Colors.DIM}{timestamp}{Colors.RESET}")

    def print_system_message(self, message: str):
        """Print system message (centered, dim)."""
        print()
        print(f"{Colors.DIM}  ── {message} ──{Colors.RESET}")

    def print_gate_transition(self, transitions: list):
        """Print gate transition notification."""
        if transitions:
            for t in transitions:
                print(f"  {Colors.YELLOW}⚡ {t}{Colors.RESET}")

    def print_error(self, message: str):
        """Print error message."""
        print(f"\n  {Colors.RED}✗ {message}{Colors.RESET}")

    def print_success(self, message: str):
        """Print success message."""
        print(f"\n  {Colors.GREEN}✓ {message}{Colors.RESET}")

    def print_notes(self, notes: list, title: str = "Notes"):
        """Print notes in a readable format."""
        width = self.terminal_width

        print()
        print(f"{Colors.DIM}{'─' * width}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}  {title}{Colors.RESET}")
        print(f"{Colors.DIM}{'─' * width}{Colors.RESET}")

        if not notes:
            print(f"  {Colors.DIM}No notes found{Colors.RESET}")
            print(f"{Colors.DIM}{'─' * width}{Colors.RESET}")
            return

        for i, note in enumerate(notes):
            timestamp = note.get('timestamp', 'Unknown time')
            content = note.get('content', '')
            note_type = note.get('type', 'unknown')

            # Type indicator
            if note_type == 'developer':
                type_badge = f"{Colors.YELLOW}DEV{Colors.RESET}"
            else:
                type_badge = f"{Colors.MAGENTA}PERSONAL{Colors.RESET}"

            # Format datetime nicely
            dt = note.get('datetime')
            if dt:
                # Show relative time for recent notes
                from datetime import datetime as dt_module
                now = dt_module.now()
                diff = now - dt
                if diff.days == 0:
                    if diff.seconds < 3600:
                        time_str = f"{diff.seconds // 60}m ago"
                    else:
                        time_str = f"{diff.seconds // 3600}h ago"
                elif diff.days == 1:
                    time_str = "yesterday"
                elif diff.days < 7:
                    time_str = f"{diff.days}d ago"
                else:
                    time_str = dt.strftime("%b %d")
            else:
                time_str = timestamp

            # Print note header
            print()
            print(f"  {type_badge} {Colors.DIM}{time_str}{Colors.RESET}")

            # Print content (wrapped)
            content_lines = content.split('\n')
            for line in content_lines[:5]:  # Limit to 5 lines per note
                if len(line) > width - 6:
                    line = line[:width - 9] + "..."
                print(f"  {Colors.WHITE}{line}{Colors.RESET}")

            if len(content_lines) > 5:
                print(f"  {Colors.DIM}... ({len(content_lines) - 5} more lines){Colors.RESET}")

        print()
        print(f"{Colors.DIM}{'─' * width}{Colors.RESET}")

    def print_debug_panel(self, state: dict):
        """Print debug panel showing full system state."""
        width = self.terminal_width

        print()
        print(f"{Colors.DIM}{'─' * width}{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}  DEBUG STATE{Colors.RESET}")
        print(f"{Colors.DIM}{'─' * width}{Colors.RESET}")

        # Turn counter
        turn = state.get('turn', 0)
        print(f"  {Colors.DIM}Turn:{Colors.RESET} {Colors.WHITE}{turn}{Colors.RESET}")
        print()

        # Stance
        stance = state.get('stance', 'unknown')
        stance_color = self._stance_color(stance)
        print(f"  {Colors.BOLD}STANCE{Colors.RESET}")
        print(f"  {Colors.DIM}├─{Colors.RESET} Current: {stance_color}{stance.upper()}{Colors.RESET}")

        # Gate state
        gate_state = state.get('gate_state', {})
        emergency_available = gate_state.get('emergency_available', False)
        turns_since_emergency = gate_state.get('turns_since_emergency', 0)
        emergency_status = f"{Colors.GREEN}available{Colors.RESET}" if emergency_available else f"{Colors.RED}cooldown ({turns_since_emergency}){Colors.RESET}"
        print(f"  {Colors.DIM}└─{Colors.RESET} Emergency: {emergency_status}")
        print()

        # Commitment
        commitment = state.get('commitment', {})
        print(f"  {Colors.BOLD}COMMITMENT{Colors.RESET}")
        if commitment.get('active'):
            frame = commitment.get('frame', 'none')
            horizon = commitment.get('horizon', 'mid')
            turns_remaining = commitment.get('turns_remaining', 0)
            success_criteria = commitment.get('success_criteria', [])
            non_goals = commitment.get('non_goals', [])

            print(f"  {Colors.DIM}├─{Colors.RESET} Frame: {Colors.CYAN}{frame}{Colors.RESET}")
            print(f"  {Colors.DIM}├─{Colors.RESET} Horizon: {Colors.WHITE}{horizon}{Colors.RESET}")
            print(f"  {Colors.DIM}├─{Colors.RESET} Turns left: {Colors.WHITE}{turns_remaining}{Colors.RESET}")
            if success_criteria:
                print(f"  {Colors.DIM}├─{Colors.RESET} Success: {Colors.GREEN}{', '.join(success_criteria[:2])}{Colors.RESET}")
            if non_goals:
                print(f"  {Colors.DIM}└─{Colors.RESET} Non-goals: {Colors.RED}{', '.join(non_goals[:2])}{Colors.RESET}")
            else:
                print(f"  {Colors.DIM}└─{Colors.RESET} Non-goals: {Colors.DIM}none{Colors.RESET}")
        else:
            print(f"  {Colors.DIM}└─{Colors.RESET} {Colors.DIM}No active commitment{Colors.RESET}")
        print()

        # Delegation
        delegation = state.get('delegation', {})
        print(f"  {Colors.BOLD}DELEGATION{Colors.RESET}")
        active_leases = delegation.get('active_leases', 0)
        grantees = delegation.get('grantees', [])
        capabilities = delegation.get('capabilities_delegated', [])

        if active_leases > 0:
            print(f"  {Colors.DIM}├─{Colors.RESET} Active leases: {Colors.WHITE}{active_leases}{Colors.RESET}")
            if grantees:
                print(f"  {Colors.DIM}├─{Colors.RESET} Grantees: {Colors.CYAN}{', '.join(grantees)}{Colors.RESET}")
            if capabilities:
                print(f"  {Colors.DIM}└─{Colors.RESET} Capabilities: {Colors.GREEN}{', '.join(capabilities)}{Colors.RESET}")
            else:
                print(f"  {Colors.DIM}└─{Colors.RESET} Capabilities: {Colors.DIM}none{Colors.RESET}")
        else:
            print(f"  {Colors.DIM}└─{Colors.RESET} {Colors.DIM}No active delegations{Colors.RESET}")
        print()

        # Health
        health = state.get('health', {})
        print(f"  {Colors.BOLD}HEALTH{Colors.RESET}")
        health_status = health.get('status', 'unknown')
        dimension_averages = health.get('dimension_averages', {})
        signal_count = health.get('signal_count', 0)

        print(f"  {Colors.DIM}├─{Colors.RESET} Status: {Colors.WHITE}{health_status}{Colors.RESET}")
        print(f"  {Colors.DIM}├─{Colors.RESET} Signals: {Colors.WHITE}{signal_count}{Colors.RESET}")

        if dimension_averages:
            dims = []
            for dim, avg in dimension_averages.items():
                color = Colors.GREEN if avg > 0.6 else (Colors.YELLOW if avg > 0.4 else Colors.RED)
                dims.append(f"{dim}:{color}{avg:.1f}{Colors.RESET}")
            print(f"  {Colors.DIM}└─{Colors.RESET} Dims: {' '.join(dims)}")
        else:
            print(f"  {Colors.DIM}└─{Colors.RESET} Dims: {Colors.DIM}no data{Colors.RESET}")

        print(f"{Colors.DIM}{'─' * width}{Colors.RESET}")

    def get_input(self, prompt: str = "You") -> str:
        """Get user input with readline support and proper paste handling."""
        try:
            # Use a simple prompt that works well with readline
            user_input = input(f"\n{Colors.BRIGHT_BLUE}{prompt}:{Colors.RESET} ")

            # Check if this looks like the start of a bracketed paste
            # The start marker \033[200~ often shows as partial (200~ or 00~)
            # because the escape sequence gets partially interpreted
            if '200~' in user_input or '00~' in user_input:
                # We're in a paste - accumulate lines until we see end marker
                lines = [self._clean_paste_markers(user_input)]

                while True:
                    try:
                        # Read next line without prompt (we're mid-paste)
                        next_line = input()

                        # Check for end marker
                        if '201~' in next_line or '01~' in next_line:
                            # Clean and add final line, then break
                            cleaned = self._clean_paste_markers(next_line)
                            if cleaned:
                                lines.append(cleaned)
                            break
                        else:
                            lines.append(next_line)
                    except EOFError:
                        break

                # Join all pasted lines
                user_input = '\n'.join(lines)

            return user_input.strip()
        except EOFError:
            return "quit"

    def _clean_paste_markers(self, text: str) -> str:
        """Remove bracketed paste marker artifacts from text."""
        import re
        # Remove various forms of paste markers that might appear
        # \033[200~ (start) and \033[201~ (end) can show as:
        # - Full escape sequence (usually invisible)
        # - Partial: 200~, 00~, 201~, 01~
        # - With brackets: ^[[200~, ^[[201~
        patterns = [
            r'\x1b\[200~',  # Actual escape sequence start
            r'\x1b\[201~',  # Actual escape sequence end
            r'\^\[\[200~',  # Caret notation start
            r'\^\[\[201~',  # Caret notation end
            r'200~',        # Partial start marker
            r'201~',        # Partial end marker
            r'00~',         # Truncated start marker
            r'01~',         # Truncated end marker
        ]
        result = text
        for pattern in patterns:
            result = re.sub(pattern, '', result)
        return result

    def _wrap_text(self, text: str, bg_color: str = None) -> list:
        """Wrap text to fit in bubble.

        Args:
            text: Text to wrap
            bg_color: Background color to restore after markdown (e.g., Colors.BG_BLUE)
        """
        import re

        # Handle multi-line text - wrap BEFORE markdown processing
        paragraphs = text.split('\n')
        all_lines = []

        for para in paragraphs:
            if para.strip():
                wrapped = textwrap.wrap(
                    para,
                    width=self.max_bubble_width - 4,
                    break_long_words=True,
                    break_on_hyphens=True
                )
                all_lines.extend(wrapped)
            else:
                all_lines.append('')

        # Now apply markdown formatting to each line
        all_lines = [self._process_markdown(line, bg_color=bg_color) for line in all_lines]

        return all_lines if all_lines else ['']

    def _visible_len(self, text: str) -> int:
        """Get visible length of text (excluding ANSI codes)."""
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        return len(ansi_escape.sub('', text))

    def _process_markdown(self, text: str, bg_color: str = None) -> str:
        """Convert markdown to terminal formatting.

        Args:
            text: Text to process
            bg_color: Background color to restore after each element (for bubbles)
        """
        import re

        # What to restore after formatting - include background for bubbles
        if bg_color:
            restore = f'{Colors.RESET}{bg_color}{Colors.WHITE}'
        else:
            restore = f'{Colors.RESET}{Colors.WHITE}'

        # Bold: **text** or __text__ -> BOLD text RESET
        text = re.sub(
            r'\*\*(.+?)\*\*',
            f'{Colors.BOLD}\\1{restore}',
            text
        )
        text = re.sub(
            r'__(.+?)__',
            f'{Colors.BOLD}\\1{restore}',
            text
        )

        # Italic: *text* or _text_ -> ITALIC text RESET (but not inside bold)
        text = re.sub(
            r'(?<!\*)\*([^*]+?)\*(?!\*)',
            f'{Colors.ITALIC}\\1{restore}',
            text
        )

        # Code: `text` -> DIM text RESET
        text = re.sub(
            r'`([^`]+?)`',
            f'{Colors.DIM}\\1{restore}',
            text
        )

        # Headers: remove # but make bold
        text = re.sub(
            r'^#+\s*(.+)$',
            f'{Colors.BOLD}\\1{restore}',
            text,
            flags=re.MULTILINE
        )

        # Bullet points: keep but clean up
        text = re.sub(r'^[-*]\s+', '• ', text, flags=re.MULTILINE)

        return text

    def _stance_color(self, stance: str) -> str:
        """Get color for stance."""
        colors = {
            'sensemaking': Colors.MAGENTA,
            'discovery': Colors.CYAN,
            'execution': Colors.GREEN,
            'evaluation': Colors.YELLOW,
        }
        return colors.get(stance.lower(), Colors.WHITE)

    def _health_color(self, health: str) -> str:
        """Get color for health status."""
        colors = {
            'healthy': Colors.GREEN,
            'concerning': Colors.YELLOW,
            'critical': Colors.RED,
        }
        return colors.get(health.lower(), Colors.DIM)


def create_chat_ui(history_file: Optional[Path] = None) -> ChatUI:
    """Create and return a ChatUI instance."""
    return ChatUI(history_file)
