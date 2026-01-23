from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Dict, Any


@dataclass
class GeminiModel:
    regions: List[str] = field(default_factory=list)
    distribute_requests: bool = False
    region: str | None = None

    def resolve_region(self, explicit_region: str | None = None) -> str | None:
        if self.distribute_requests:
            if explicit_region:
                return explicit_region
            if self.region:
                return self.region
            if self.regions:
                return self.regions[0]
            return None
        if explicit_region:
            return explicit_region
        if self.region:
            return self.region
        if self.regions:
            return self.regions[0]
        return None


@dataclass
class GeminiLlmConnection:
    model: GeminiModel

    def send_history(self, history: Iterable[Dict[str, Any]]) -> None:
        for message in history:
            parts = message.get("parts", [])
            for part in parts:
                part_type = part.get("type")
                if part_type != "text":
                    raise ValueError(
                        f"Unsupported content part type: {part_type}. No silent dropping allowed."
                    )
