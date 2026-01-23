"""
Slot Modules - Hot-swappable component implementations.

This package contains interface definitions and implementations for
the Control Plane's modular architecture.

Slots:
- memory_bus: Memory storage and retrieval
- llm_provider: Language model API access
- reasoning_engine: Core reasoning and decision making
- vector_store: Vector embeddings storage
- cache: Caching layer
"""

from .interfaces import (
    MemoryBusInterface,
    LLMProviderInterface,
    ReasoningInterface,
    VectorStoreInterface,
    CacheInterface,
)

__all__ = [
    "MemoryBusInterface",
    "LLMProviderInterface",
    "ReasoningInterface",
    "VectorStoreInterface",
    "CacheInterface",
]
