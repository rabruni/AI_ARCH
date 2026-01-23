"""Agent Loader - Load agent definitions from YAML files."""

from typing import Dict, Optional, List
from pathlib import Path
import yaml

from locked_system.agents.models import AgentDefinition, PromptProfile


class AgentLoader:
    """
    Loads and manages agent definitions from YAML files.

    Default location: agents/defs/*.yaml
    """

    def __init__(self, defs_path: str = None):
        self._agents: Dict[str, AgentDefinition] = {}
        self._defs_path = Path(defs_path) if defs_path else None
        self._initialized = False

    def register(self, definition: AgentDefinition) -> None:
        """Register an agent definition."""
        self._agents[definition.agent_id] = definition

    def get(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get an agent definition by ID."""
        return self._agents.get(agent_id)

    def exists(self, agent_id: str) -> bool:
        """Check if agent exists."""
        return agent_id in self._agents

    def list_all(self) -> List[AgentDefinition]:
        """List all registered agents."""
        return list(self._agents.values())

    def list_by_tag(self, tag: str) -> List[AgentDefinition]:
        """List agents with a specific routing tag."""
        return [a for a in self._agents.values() if tag in a.routing_tags]

    def load_from_yaml(self, yaml_path: str) -> AgentDefinition:
        """
        Load an agent definition from a YAML file.

        Expected format:
        ```yaml
        agent_id: "writer"
        version: "1.0"
        role: "Document Writer"
        lifecycle: "session"
        routing_tags: ["writing"]
        prompt_profile:
          style: "balanced"
          tone: "direct"
        requested_scopes: ["fs.read", "fs.write"]
        allowed_tool_requests: ["fs.read_file", "fs.write_file"]
        allowed_gate_requests: ["write_approval", "lane_switch"]
        ```
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        definition = AgentDefinition.from_dict(data)
        self.register(definition)
        return definition

    def load_from_directory(self, dir_path: str = None) -> List[AgentDefinition]:
        """Load all YAML agent definitions from a directory."""
        path = Path(dir_path) if dir_path else self._defs_path
        if not path or not path.exists():
            return []

        loaded = []
        for yaml_file in path.glob("*.yaml"):
            try:
                definition = self.load_from_yaml(str(yaml_file))
                loaded.append(definition)
            except Exception as e:
                # Log but continue loading other agents
                print(f"Warning: Failed to load {yaml_file}: {e}")

        for yaml_file in path.glob("*.yml"):
            try:
                definition = self.load_from_yaml(str(yaml_file))
                loaded.append(definition)
            except Exception as e:
                print(f"Warning: Failed to load {yaml_file}: {e}")

        return loaded

    def initialize_defaults(self) -> None:
        """Register built-in default agents."""
        if self._initialized:
            return

        # Front-door agent (default router)
        self.register(AgentDefinition(
            agent_id="front_door",
            version="1.0",
            role="Front-Door Router",
            lifecycle="session",
            routing_tags=["routing", "default"],
            prompt_profile=PromptProfile(style="concise", tone="direct"),
            requested_scopes=["fs.read"],
            allowed_tool_requests=["fs.read_file", "fs.list_directory"],
            allowed_gate_requests=[
                "work_declaration",
                "lane_switch",
                "evaluation",
                "write_approval",
            ],
        ))

        # Writer agent
        self.register(AgentDefinition(
            agent_id="writer",
            version="1.0",
            role="Document Writer",
            lifecycle="session",
            routing_tags=["writing", "documents"],
            prompt_profile=PromptProfile(style="balanced", tone="direct", max_words=800),
            requested_scopes=["fs.read", "fs.write"],
            allowed_tool_requests=["fs.read_file", "fs.write_file", "fs.list_directory"],
            allowed_gate_requests=["write_approval", "lane_switch"],
        ))

        # Analyst agent
        self.register(AgentDefinition(
            agent_id="analyst",
            version="1.0",
            role="Data Analyst",
            lifecycle="ephemeral",
            routing_tags=["analysis", "research", "finance"],
            prompt_profile=PromptProfile(style="verbose", tone="formal", max_words=1000),
            requested_scopes=["fs.read"],
            allowed_tool_requests=["fs.read_file", "fs.list_directory", "fs.file_info"],
            allowed_gate_requests=["evaluation"],
        ))

        # Monitor agent
        self.register(AgentDefinition(
            agent_id="monitor",
            version="1.0",
            role="System Monitor",
            lifecycle="session",
            routing_tags=["monitoring", "ops"],
            prompt_profile=PromptProfile(style="concise", tone="direct", max_words=200),
            requested_scopes=["fs.read"],
            allowed_tool_requests=["fs.read_file", "fs.file_info"],
            allowed_gate_requests=["evaluation"],
        ))

        self._initialized = True

    def find_by_routing(self, intent: str) -> Optional[AgentDefinition]:
        """
        Find best agent for an intent based on routing tags.

        Simple keyword matching for V1.
        """
        intent_lower = intent.lower()

        # Score agents by tag matches
        scored = []
        for agent in self._agents.values():
            score = 0
            for tag in agent.routing_tags:
                if tag.lower() in intent_lower:
                    score += 1
            if score > 0:
                scored.append((score, agent))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]

        # Default to front_door
        return self.get("front_door")

    def validate_definition(self, definition: AgentDefinition) -> tuple[bool, List[str]]:
        """
        Validate an agent definition.

        Returns (valid, list_of_errors).
        """
        errors = []

        if not definition.agent_id:
            errors.append("agent_id is required")

        if not definition.role:
            errors.append("role is required")

        if definition.lifecycle not in ("ephemeral", "session"):
            errors.append(f"lifecycle must be 'ephemeral' or 'session', got {definition.lifecycle}")

        if definition.prompt_profile.max_words < 50:
            errors.append("max_words must be at least 50")

        return len(errors) == 0, errors
