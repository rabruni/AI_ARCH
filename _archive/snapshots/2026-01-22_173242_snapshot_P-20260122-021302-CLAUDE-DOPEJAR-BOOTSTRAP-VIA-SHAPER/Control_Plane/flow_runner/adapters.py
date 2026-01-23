"""Agent adapter stubs."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Dict, Any


AdapterResult = Dict[str, Any]


@dataclass
class AgentAdapter:
    command: str | None = None

    def is_available(self) -> bool:
        if not self.command:
            return True
        return shutil.which(self.command) is not None

    def execute(self, prompt: str, context: Dict[str, Any]) -> AdapterResult:
        return {"status": "manual_required", "output": None, "artifacts": []}


class ClaudeAdapter(AgentAdapter):
    def __init__(self) -> None:
        super().__init__(command="claude")


class CodexAdapter(AgentAdapter):
    def __init__(self) -> None:
        super().__init__(command="codex")


class GeminiAdapter(AgentAdapter):
    def __init__(self) -> None:
        super().__init__(command="gemini")


class ManualAdapter(AgentAdapter):
    def __init__(self) -> None:
        super().__init__(command=None)

    def is_available(self) -> bool:
        return True


def resolve_adapter(agent_selector: str | None) -> AgentAdapter:
    selector = (agent_selector or "").lower()
    if "claude" in selector:
        adapter = ClaudeAdapter()
    elif "codex" in selector:
        adapter = CodexAdapter()
    elif "gemini" in selector:
        adapter = GeminiAdapter()
    elif "vision" in selector:
        adapter = ClaudeAdapter()
    else:
        adapter = ManualAdapter()

    if adapter.is_available():
        return adapter
    return ManualAdapter()
