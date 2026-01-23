"""The Assist - Console Formatter

Chat-style formatting:
- User messages: right-aligned
- Assist messages: left-aligned
- Hierarchical numbering (1, 1.1, 1.1.1) instead of bullets
- Clean, readable output
"""
import re
import shutil
import textwrap
from typing import Optional


# ============================================================
# CONFIGURATION
# ============================================================

# Get terminal width, default to 80
def get_terminal_width() -> int:
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80


# Formatting constants
USER_PREFIX = "You"
ASSIST_PREFIX = "Assist"
MAX_WIDTH_RATIO = 0.65  # Messages take up 65% of terminal width


# ANSI colors (optional, can be disabled)
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # User messages
    USER = "\033[36m"  # Cyan

    # Assist messages
    ASSIST = "\033[0m"  # Default

    # System/meta
    SYSTEM = "\033[33m"  # Yellow
    WARN = "\033[33m"    # Yellow
    ERROR = "\033[31m"   # Red
    SUCCESS = "\033[32m" # Green


def disable_colors():
    """Disable ANSI colors for terminals that don't support them."""
    for attr in dir(Colors):
        if not attr.startswith('_'):
            setattr(Colors, attr, "")


# ============================================================
# BULLET TO NUMBER CONVERSION
# ============================================================

def bullets_to_numbers(text: str) -> str:
    """
    Convert bullet points to hierarchical numbers.

    - Item 1        →  1. Item 1
      - Sub item    →  1.1. Sub item
        - Deep      →  1.1.1. Deep
    - Item 2        →  2. Item 2

    Also handles *, •, and numbered bullets that need fixing.
    """
    lines = text.split('\n')
    result = []

    # Track numbering at each indent level
    counters = {}  # indent_level -> current_number

    # Regex patterns for bullets
    bullet_pattern = re.compile(r'^(\s*)([-*•]|\d+\.)\s+(.*)$')

    for line in lines:
        match = bullet_pattern.match(line)

        if match:
            indent = match.group(1)
            bullet = match.group(2)
            content = match.group(3)

            # Calculate indent level (each 2 spaces = 1 level)
            indent_level = len(indent) // 2

            # Reset deeper levels when we go back up
            levels_to_remove = [l for l in counters if l > indent_level]
            for l in levels_to_remove:
                del counters[l]

            # Increment counter at this level
            counters[indent_level] = counters.get(indent_level, 0) + 1

            # Build hierarchical number (1.2.1 style)
            number_parts = []
            for level in range(indent_level + 1):
                number_parts.append(str(counters.get(level, 1)))

            number = ".".join(number_parts)

            # Reconstruct line with number instead of bullet
            new_indent = "  " * indent_level
            result.append(f"{new_indent}{number}. {content}")
        else:
            # Not a bullet line - reset counters if it's not empty/whitespace
            if line.strip() and not line.startswith(' '):
                counters = {}
            result.append(line)

    return '\n'.join(result)


# ============================================================
# TEXT WRAPPING
# ============================================================

def wrap_text(text: str, width: int, indent: str = "") -> str:
    """Wrap text to width with optional indent for continuation lines."""
    lines = text.split('\n')
    wrapped = []

    for line in lines:
        if not line.strip():
            wrapped.append("")
            continue

        # Preserve existing indentation
        existing_indent = len(line) - len(line.lstrip())
        line_indent = " " * existing_indent

        # Wrap the line
        wrapped_lines = textwrap.wrap(
            line.strip(),
            width=width - existing_indent,
            initial_indent="",
            subsequent_indent=""
        )

        for i, wl in enumerate(wrapped_lines):
            if i == 0:
                wrapped.append(line_indent + wl)
            else:
                wrapped.append(line_indent + indent + wl)

    return '\n'.join(wrapped)


# ============================================================
# MESSAGE FORMATTING
# ============================================================

def format_user_message(text: str) -> str:
    """Format user message (right-aligned style)."""
    term_width = get_terminal_width()
    msg_width = int(term_width * MAX_WIDTH_RATIO)

    # Wrap text
    wrapped = wrap_text(text, msg_width)

    # Right-align each line
    lines = wrapped.split('\n')
    formatted = []

    # Add header
    header = f"{Colors.USER}{Colors.BOLD}{USER_PREFIX}:{Colors.RESET}"
    padding = term_width - len(USER_PREFIX) - 1
    formatted.append(" " * padding + header)

    for line in lines:
        padding = term_width - len(line)
        formatted.append(f"{Colors.USER}" + " " * padding + line + f"{Colors.RESET}")

    formatted.append("")  # Blank line after

    return '\n'.join(formatted)


def format_assist_message(text: str) -> str:
    """Format assist message (left-aligned, with number conversion)."""
    term_width = get_terminal_width()
    msg_width = int(term_width * MAX_WIDTH_RATIO)

    # Convert bullets to numbers
    text = bullets_to_numbers(text)

    # Wrap text
    wrapped = wrap_text(text, msg_width)

    lines = wrapped.split('\n')
    formatted = []

    # Add header
    formatted.append(f"{Colors.BOLD}{ASSIST_PREFIX}:{Colors.RESET}")

    for line in lines:
        formatted.append(f"{Colors.ASSIST}{line}{Colors.RESET}")

    formatted.append("")  # Blank line after

    return '\n'.join(formatted)


def format_system_message(text: str, msg_type: str = "info") -> str:
    """Format system messages (warnings, errors, info)."""
    color = Colors.SYSTEM
    if msg_type == "error":
        color = Colors.ERROR
    elif msg_type == "warn":
        color = Colors.WARN
    elif msg_type == "success":
        color = Colors.SUCCESS

    return f"{color}[{text}]{Colors.RESET}"


# ============================================================
# HEADER/DIVIDER FORMATTING
# ============================================================

def format_header(title: str, subtitle: str = None) -> str:
    """Format app header."""
    term_width = get_terminal_width()

    lines = []
    lines.append("=" * term_width)

    # Center title
    padding = (term_width - len(title)) // 2
    lines.append(" " * padding + f"{Colors.BOLD}{title}{Colors.RESET}")

    if subtitle:
        padding = (term_width - len(subtitle)) // 2
        lines.append(" " * padding + f"{Colors.DIM}{subtitle}{Colors.RESET}")

    lines.append("=" * term_width)

    return '\n'.join(lines)


def format_divider(char: str = "-") -> str:
    """Format a divider line."""
    return char * min(get_terminal_width(), 50)


# ============================================================
# INPUT PROMPT
# ============================================================

def get_input_prompt() -> str:
    """Get formatted input prompt (right-aligned indicator)."""
    term_width = get_terminal_width()
    prompt = f"{Colors.USER}> {Colors.RESET}"
    # Right align the prompt indicator
    padding = term_width - 2
    return " " * padding + prompt


def get_simple_prompt() -> str:
    """Simple left-aligned prompt."""
    return f"{Colors.USER}You: {Colors.RESET}"


# ============================================================
# DEMO / TEST
# ============================================================

def demo():
    """Demonstrate formatting."""
    print(format_header("THE ASSIST", "Cognitive Anchor | v0.2"))
    print()

    # Simulated exchange
    user_msg = "What's on my plate today?"
    print(format_user_message(user_msg))

    assist_msg = """Looking at your current state:

- Austin travel booking is 11 days out
  - Flights need booking
  - Hotel not confirmed
- Sunday has conflicts:
  - Patent work scheduled
  - Family time competing
- Monday is stacked:
  - Eye appointment PM
  - Parents/grandma visit evening

The Austin booking feels most time-sensitive. Want to tackle that first?"""

    print(format_assist_message(assist_msg))

    print(format_system_message("Memory curated", "info"))
    print(format_system_message("Unclean shutdown detected", "warn"))


if __name__ == "__main__":
    demo()
