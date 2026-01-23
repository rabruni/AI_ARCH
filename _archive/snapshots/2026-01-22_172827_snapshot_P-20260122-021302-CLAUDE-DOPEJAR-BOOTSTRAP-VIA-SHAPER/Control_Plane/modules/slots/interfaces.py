"""
Slot Interfaces - Abstract base classes for slot modules.

Each slot has a defined interface that implementations must follow.
This enables hot-swapping of modules without changing dependent code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


# === Memory Bus Interface ===

@dataclass
class MemoryEntry:
    """A single memory entry."""
    key: str
    value: Any
    created_at: datetime
    updated_at: datetime
    ttl: Optional[int] = None  # Time to live in seconds
    tags: Optional[list[str]] = None


class MemoryBusInterface(ABC):
    """
    Interface for memory storage and retrieval.

    Memory bus handles persistent and ephemeral storage for the system.
    Implementations may use files, Redis, databases, or other backends.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key. Returns None if not found."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value. Returns True on success."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key existed."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def keys(self, pattern: str = "*") -> list[str]:
        """List keys matching pattern."""
        pass

    @abstractmethod
    def clear(self) -> int:
        """Clear all entries. Returns count deleted."""
        pass


# === LLM Provider Interface ===

@dataclass
class Message:
    """A chat message."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str


class LLMProviderInterface(ABC):
    """
    Interface for language model API providers.

    Implementations handle authentication, rate limiting, and API calls
    to various LLM providers (Anthropic, OpenAI, etc.).
    """

    @abstractmethod
    def chat(self, messages: list[Message], **kwargs) -> LLMResponse:
        """Send chat messages and get a response."""
        pass

    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Complete a prompt."""
        pass

    @abstractmethod
    def get_models(self) -> list[str]:
        """List available models."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and reachable."""
        pass


# === Reasoning Interface ===

@dataclass
class ReasoningResult:
    """Result of a reasoning operation."""
    conclusion: str
    confidence: float
    steps: list[str]
    evidence: list[str]


class ReasoningInterface(ABC):
    """
    Interface for reasoning engines.

    Reasoning engines implement different strategies for
    problem-solving and decision-making (HRM, CoT, etc.).
    """

    @abstractmethod
    def reason(self, query: str, context: dict) -> ReasoningResult:
        """Perform reasoning on a query with given context."""
        pass

    @abstractmethod
    def plan(self, goal: str, constraints: list[str]) -> list[str]:
        """Generate a plan to achieve a goal."""
        pass

    @abstractmethod
    def evaluate(self, action: str, outcome: str) -> dict:
        """Evaluate an action's outcome."""
        pass


# === Vector Store Interface ===

@dataclass
class VectorEntry:
    """A vector embedding with metadata."""
    id: str
    vector: list[float]
    metadata: dict
    text: Optional[str] = None


@dataclass
class SearchResult:
    """A search result with similarity score."""
    entry: VectorEntry
    score: float


class VectorStoreInterface(ABC):
    """
    Interface for vector embedding storage.

    Vector stores handle storage and similarity search
    for embeddings used in RAG and semantic search.
    """

    @abstractmethod
    def add(self, entries: list[VectorEntry]) -> int:
        """Add entries to the store. Returns count added."""
        pass

    @abstractmethod
    def search(self, vector: list[float], k: int = 10) -> list[SearchResult]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    def delete(self, ids: list[str]) -> int:
        """Delete entries by ID. Returns count deleted."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total entries in store."""
        pass


# === Cache Interface ===

class CacheInterface(ABC):
    """
    Interface for caching layer.

    Cache provides fast access to frequently used data
    with optional TTL and eviction policies.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get cached value. Returns None if not found or expired."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cached value with TTL in seconds."""
        pass

    @abstractmethod
    def invalidate(self, key: str) -> bool:
        """Invalidate a cached key."""
        pass

    @abstractmethod
    def flush(self) -> int:
        """Flush entire cache. Returns count flushed."""
        pass

    @abstractmethod
    def stats(self) -> dict:
        """Return cache statistics (hits, misses, size)."""
        pass
