"""Capability Registry - Central registry for gated capabilities.

All capabilities:
- Require explicit delegation to use
- Are logged when invoked
- Can be revoked at any time
- Have defined side effects
"""
from typing import Dict, Any, Optional, Callable


# Capability definitions
CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "note_capture": {
        "requires_delegation": True,
        "default_granted": False,
        "side_effects": ["file_write"],
        "description": "Write notes to files (personal or developer)",
        "risk_level": "low",
    },
    "memory_write": {
        "requires_delegation": True,
        "default_granted": False,
        "side_effects": ["slow_memory"],
        "description": "Write to slow memory (decisions, commitments)",
        "risk_level": "medium",
    },
    "context_injection": {
        "requires_delegation": True,
        "default_granted": False,
        "side_effects": ["prompt_modification"],
        "description": "Inject context into prompts (bounded, sandboxed)",
        "risk_level": "high",
    },
}


def check_capability(
    capability_id: str,
    delegation_check: Optional[Callable[[str, str], bool]] = None,
    grantee: str = "agent"
) -> dict:
    """
    Check if a capability can be used.

    Returns dict with authorization status and info.
    """
    if capability_id not in CAPABILITIES:
        return {
            "exists": False,
            "authorized": False,
            "message": f"Unknown capability: {capability_id}"
        }

    cap = CAPABILITIES[capability_id]

    # If no delegation required, allow
    if not cap["requires_delegation"]:
        return {
            "exists": True,
            "authorized": True,
            "message": "No delegation required"
        }

    # If delegation check provided, use it
    if delegation_check:
        authorized = delegation_check(grantee, capability_id)
        return {
            "exists": True,
            "authorized": authorized,
            "message": "Authorized" if authorized else "Delegation required"
        }

    # If default_granted, allow
    if cap.get("default_granted", False):
        return {
            "exists": True,
            "authorized": True,
            "message": "Default granted"
        }

    # Deny by default
    return {
        "exists": True,
        "authorized": False,
        "message": "Delegation required - not granted"
    }


def get_capability_info(capability_id: str) -> Optional[dict]:
    """Get info about a capability."""
    return CAPABILITIES.get(capability_id)


def list_capabilities() -> list[str]:
    """List all registered capabilities."""
    return list(CAPABILITIES.keys())


def get_side_effects(capability_id: str) -> list[str]:
    """Get side effects for a capability."""
    cap = CAPABILITIES.get(capability_id)
    return cap["side_effects"] if cap else []


def register_capability(
    capability_id: str,
    requires_delegation: bool = True,
    default_granted: bool = False,
    side_effects: list[str] = None,
    description: str = "",
    risk_level: str = "medium"
):
    """
    Register a new capability.

    Use this for dynamically registered capabilities.
    """
    CAPABILITIES[capability_id] = {
        "requires_delegation": requires_delegation,
        "default_granted": default_granted,
        "side_effects": side_effects or [],
        "description": description,
        "risk_level": risk_level,
    }
