from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


HistoryPair = Tuple[str, str]


@dataclass(frozen=True)
class ContextWindow:
    block1: str
    block2: str
    block3: str
    block4: List[HistoryPair]


def build_context_window(
    block1: str,
    block2: str,
    block3: str,
    history_pairs: List[HistoryPair],
) -> ContextWindow:
    trimmed_pairs = history_pairs[-2:]
    return ContextWindow(block1=block1, block2=block2, block3=block3, block4=trimmed_pairs)
