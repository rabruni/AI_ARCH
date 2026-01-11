"""Session Logger - Date-stamped conversation logging."""
from datetime import datetime
from pathlib import Path


class SessionLogger:
    """Logs conversation to date-stamped file."""

    def __init__(self, logs_dir: Path):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Create date-stamped filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = self.logs_dir / f"{timestamp}.log"

        # Write header
        self._write(f"=== Locked System Session ===")
        self._write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._write("=" * 40 + "\n")

    def _write(self, text: str):
        """Append text to log file."""
        with open(self.log_file, "a") as f:
            f.write(text + "\n")

    def log_system(self, message: str):
        """Log system message."""
        self._write(f"[SYSTEM] {message}")

    def log_assistant(self, message: str, metadata: dict = None):
        """Log assistant message."""
        self._write(f"\nAssistant: {message}")
        if metadata:
            self._write(f"  [{metadata}]")

    def log_user(self, message: str):
        """Log user message."""
        self._write(f"\nYou: {message}")

    def log_result(self, result):
        """Log LoopResult metadata."""
        meta = f"Turn {result.turn_number} | Stance: {result.stance} | Altitude: {result.altitude} | Health: {result.quality_health}"
        self._write(f"  [{meta}]")
        if result.bootstrap_active:
            self._write("  [Bootstrap mode active]")
        if result.gate_transitions:
            self._write(f"  [Gate transitions: {', '.join(result.gate_transitions)}]")

    def close(self):
        """Write session end."""
        self._write("\n" + "=" * 40)
        self._write(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._write("=== Session Complete ===")
