"""Bridge Memory - Artifact Index.

Index only, not content. Registered agents can write.
Status-based decay: current → stale → review-needed
"""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal


@dataclass
class Artifact:
    """An indexed artifact (pointer only, not content)."""
    name: str
    type: Literal["doc", "spec", "code", "deck", "other"]
    pointer: str  # path | link | id
    status: Literal["draft", "review", "final", "deprecated", "stale", "review-needed"]
    version: str
    owner: str  # agent or human
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    staleness_turns: int = 30  # Turns until status decays

    def decay_status(self):
        """Apply status decay."""
        self.staleness_turns -= 1
        if self.staleness_turns <= 0:
            if self.status == "final":
                self.status = "stale"
                self.staleness_turns = 20
            elif self.status == "stale":
                self.status = "review-needed"
            elif self.status in ["draft", "review"]:
                self.status = "stale"
                self.staleness_turns = 10


class BridgeMemory:
    """
    Bridge memory manager.

    Artifact index only. Registered agents can write.
    """

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir / "bridge"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self._artifacts_file = self.memory_dir / "artifacts.json"
        self._artifacts: dict[str, Artifact] = {}

        self._load()

    def _load(self):
        """Load artifacts from disk."""
        if self._artifacts_file.exists():
            try:
                data = json.loads(self._artifacts_file.read_text())
                for name, artifact_data in data.items():
                    artifact_data['created_at'] = datetime.fromisoformat(artifact_data['created_at'])
                    artifact_data['updated_at'] = datetime.fromisoformat(artifact_data['updated_at'])
                    self._artifacts[name] = Artifact(**artifact_data)
            except (json.JSONDecodeError, KeyError):
                self._artifacts = {}

    def _save(self):
        """Save artifacts to disk."""
        data = {}
        for name, artifact in self._artifacts.items():
            d = asdict(artifact)
            d['created_at'] = d['created_at'].isoformat()
            d['updated_at'] = d['updated_at'].isoformat()
            data[name] = d
        self._artifacts_file.write_text(json.dumps(data, indent=2))

    def register(self, artifact: Artifact):
        """Register a new artifact."""
        self._artifacts[artifact.name] = artifact
        self._save()

    def get(self, name: str) -> Optional[Artifact]:
        """Get artifact by name."""
        return self._artifacts.get(name)

    def update_status(self, name: str, status: str):
        """Update artifact status."""
        if name in self._artifacts:
            self._artifacts[name].status = status
            self._artifacts[name].updated_at = datetime.now()
            self._artifacts[name].staleness_turns = 30  # Reset decay
            self._save()

    def list_by_status(self, status: str) -> list[Artifact]:
        """List artifacts by status."""
        return [a for a in self._artifacts.values() if a.status == status]

    def list_by_owner(self, owner: str) -> list[Artifact]:
        """List artifacts by owner."""
        return [a for a in self._artifacts.values() if a.owner == owner]

    def decay_all(self):
        """Apply decay to all artifacts."""
        for artifact in self._artifacts.values():
            artifact.decay_status()
        self._save()

    def remove(self, name: str):
        """Remove an artifact from index."""
        if name in self._artifacts:
            del self._artifacts[name]
            self._save()

    def list_all(self) -> list[Artifact]:
        """List all artifacts."""
        return list(self._artifacts.values())
