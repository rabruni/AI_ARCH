"""Bundle Proposer - Agent bundle templates for common work types.

Bundles are pre-configured agent combinations:
- Writer bundle: Document creation workflow
- Finance bundle: Budget and expense analysis
- Monitor bundle: System monitoring
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class BundleType(Enum):
    """Types of agent bundles."""
    WRITER = "writer"
    FINANCE = "finance"
    RESEARCH = "research"
    MONITOR = "monitor"
    CUSTOM = "custom"


@dataclass
class Bundle:
    """
    An agent bundle configuration.

    Bundles specify:
    - Primary agent for the work type
    - Supporting agents that may be invoked
    - Default lane settings
    - Tool permissions
    """
    type: BundleType
    name: str
    description: str
    primary_agent: str
    supporting_agents: List[str] = field(default_factory=list)
    lane_kind: str = "writing"
    default_tools: List[str] = field(default_factory=list)
    default_gates: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'type': self.type.value,
            'name': self.name,
            'description': self.description,
            'primary_agent': self.primary_agent,
            'supporting_agents': self.supporting_agents,
            'lane_kind': self.lane_kind,
            'default_tools': self.default_tools,
            'default_gates': self.default_gates,
        }


class BundleProposer:
    """
    Proposes agent bundles based on work type.

    Pre-configured bundles for common workflows.
    """

    # Bundle definitions
    BUNDLES = {
        BundleType.WRITER: Bundle(
            type=BundleType.WRITER,
            name="Writer Bundle",
            description="Document creation and editing workflow",
            primary_agent="writer",
            supporting_agents=["analyst"],
            lane_kind="writing",
            default_tools=["fs.read_file", "fs.write_file", "fs.list_directory"],
            default_gates=["write_approval", "lane_switch"],
        ),

        BundleType.FINANCE: Bundle(
            type=BundleType.FINANCE,
            name="Finance Bundle",
            description="Budget analysis and expense tracking",
            primary_agent="analyst",
            supporting_agents=["monitor"],
            lane_kind="finance",
            default_tools=["fs.read_file", "fs.list_directory"],
            default_gates=["evaluation", "lane_switch"],
        ),

        BundleType.RESEARCH: Bundle(
            type=BundleType.RESEARCH,
            name="Research Bundle",
            description="Information gathering and analysis",
            primary_agent="analyst",
            supporting_agents=["writer"],
            lane_kind="research",
            default_tools=["fs.read_file", "fs.list_directory"],
            default_gates=["evaluation"],
        ),

        BundleType.MONITOR: Bundle(
            type=BundleType.MONITOR,
            name="Monitor Bundle",
            description="System status and operational monitoring",
            primary_agent="monitor",
            supporting_agents=[],
            lane_kind="ops",
            default_tools=["fs.read_file", "fs.file_info"],
            default_gates=["evaluation"],
        ),
    }

    def propose(self, work_type: str) -> Optional[Bundle]:
        """
        Propose a bundle for a work type.

        Args:
            work_type: Type of work (writing, finance, research, ops)

        Returns:
            Bundle if found, None otherwise
        """
        type_map = {
            'writing': BundleType.WRITER,
            'document': BundleType.WRITER,
            'documents': BundleType.WRITER,
            'finance': BundleType.FINANCE,
            'budget': BundleType.FINANCE,
            'expense': BundleType.FINANCE,
            'research': BundleType.RESEARCH,
            'analysis': BundleType.RESEARCH,
            'investigate': BundleType.RESEARCH,
            'ops': BundleType.MONITOR,
            'monitor': BundleType.MONITOR,
            'monitoring': BundleType.MONITOR,
            'status': BundleType.MONITOR,
        }

        bundle_type = type_map.get(work_type.lower())
        if bundle_type:
            return self.BUNDLES.get(bundle_type)
        return None

    def get_bundle(self, bundle_type: BundleType) -> Optional[Bundle]:
        """Get a specific bundle by type."""
        return self.BUNDLES.get(bundle_type)

    def list_bundles(self) -> List[Bundle]:
        """List all available bundles."""
        return list(self.BUNDLES.values())

    def create_custom_bundle(
        self,
        name: str,
        primary_agent: str,
        lane_kind: str,
        supporting_agents: List[str] = None,
        default_tools: List[str] = None,
    ) -> Bundle:
        """Create a custom bundle."""
        return Bundle(
            type=BundleType.CUSTOM,
            name=name,
            description=f"Custom bundle: {name}",
            primary_agent=primary_agent,
            supporting_agents=supporting_agents or [],
            lane_kind=lane_kind,
            default_tools=default_tools or ["fs.read_file"],
            default_gates=["write_approval", "lane_switch"],
        )
