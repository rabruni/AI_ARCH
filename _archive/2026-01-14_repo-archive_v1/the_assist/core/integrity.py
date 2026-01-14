"""The Assist - System Integrity Module

V1-inspired boot/shutdown sequence with checkpointing.
Designed for future multi-agent architecture.

Components:
- Preflight verification
- Checkpoint system with version log
- Write verification
- Hash-based corruption detection
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path

from the_assist.config.settings import MEMORY_DIR


# ============================================================
# PATHS
# ============================================================

STATE_DIR = os.path.join(os.path.dirname(MEMORY_DIR), "state")
CHECKPOINTS_DIR = os.path.join(STATE_DIR, "checkpoints")
VERSION_LOG = os.path.join(STATE_DIR, "version_log.json")
PREFLIGHT_LOG = os.path.join(STATE_DIR, "preflight_log.json")
INTEGRITY_STATE = os.path.join(STATE_DIR, "integrity.json")


# ============================================================
# CORE STRUCTURES
# ============================================================

REQUIRED_DIRS = [
    "the_assist/core",
    "the_assist/config",
    "the_assist/prompts",
    "the_assist/memory/store",
]

REQUIRED_FILES = [
    "the_assist/core/orchestrator.py",
    "the_assist/core/memory_v2.py",
    "the_assist/prompts/system.md",
    "the_assist/config/settings.py",
]

MEMORY_FILES = [
    "compressed/state.json",
    "curator/state.json",
    "proactive/state.json",
]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def _ensure_state_dirs():
    """Ensure state directories exist."""
    os.makedirs(STATE_DIR, exist_ok=True)
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)


def _compute_hash(filepath: str) -> Optional[str]:
    """Compute MD5 hash of a file."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None


def _compute_state_hash() -> str:
    """Compute combined hash of all memory files."""
    hashes = []
    for mf in MEMORY_FILES:
        path = os.path.join(MEMORY_DIR, mf)
        h = _compute_hash(path)
        if h:
            hashes.append(h)
    return hashlib.md5("".join(hashes).encode()).hexdigest()


def _validate_json(filepath: str) -> Tuple[bool, Optional[str]]:
    """Validate that a file is valid JSON."""
    if not os.path.exists(filepath):
        return False, "File does not exist"
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Read error: {e}"


def _get_version_log() -> Dict:
    """Load or initialize version log."""
    if os.path.exists(VERSION_LOG):
        try:
            with open(VERSION_LOG, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "version_log": [],
        "last_updated": None
    }


def _save_version_log(log: Dict):
    """Save version log."""
    log["last_updated"] = datetime.utcnow().isoformat() + "Z"
    with open(VERSION_LOG, 'w') as f:
        json.dump(log, f, indent=2)


def _get_integrity_state() -> Dict:
    """Load or initialize integrity state."""
    if os.path.exists(INTEGRITY_STATE):
        try:
            with open(INTEGRITY_STATE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "session_count": 0,
        "last_boot": None,
        "last_shutdown": None,
        "last_hash": None,
        "clean_shutdown": True,
        "agents": {}  # Future: per-agent state
    }


def _save_integrity_state(state: Dict):
    """Save integrity state."""
    with open(INTEGRITY_STATE, 'w') as f:
        json.dump(state, f, indent=2)


# ============================================================
# PREFLIGHT CHECKS
# ============================================================

def run_preflight(base_dir: str = None) -> Dict:
    """
    Run preflight verification checks.

    Returns dict with:
    - status: "passed" | "failed" | "warning"
    - verified_dirs: list of verified directories
    - verified_files: list of verified files
    - memory_status: dict of memory file validation
    - errors: list of error messages
    - warnings: list of warning messages
    """
    _ensure_state_dirs()

    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "passed",
        "verified_dirs": [],
        "verified_files": [],
        "memory_status": {},
        "errors": [],
        "warnings": []
    }

    # Check required directories
    for d in REQUIRED_DIRS:
        path = os.path.join(base_dir, d)
        if os.path.isdir(path):
            result["verified_dirs"].append(d)
        else:
            result["errors"].append(f"Missing directory: {d}")
            result["status"] = "failed"

    # Check required files
    for f in REQUIRED_FILES:
        path = os.path.join(base_dir, f)
        if os.path.isfile(path):
            result["verified_files"].append(f)
        else:
            result["errors"].append(f"Missing file: {f}")
            result["status"] = "failed"

    # Validate memory files (warning if missing, error if corrupt)
    for mf in MEMORY_FILES:
        path = os.path.join(MEMORY_DIR, mf)
        if not os.path.exists(path):
            result["memory_status"][mf] = "missing"
            result["warnings"].append(f"Memory file missing (will be created): {mf}")
            if result["status"] == "passed":
                result["status"] = "warning"
        else:
            valid, error = _validate_json(path)
            if valid:
                result["memory_status"][mf] = "valid"
            else:
                result["memory_status"][mf] = f"corrupt: {error}"
                result["errors"].append(f"Corrupt memory file: {mf} - {error}")
                result["status"] = "failed"

    # Check for unclean shutdown
    integrity = _get_integrity_state()
    if not integrity.get("clean_shutdown", True):
        result["warnings"].append("Previous session did not shut down cleanly")
        if result["status"] == "passed":
            result["status"] = "warning"

    # Check hash for corruption
    if integrity.get("last_hash"):
        current_hash = _compute_state_hash()
        if current_hash != integrity["last_hash"]:
            result["warnings"].append("Memory state changed outside of session (external modification or corruption)")
            if result["status"] == "passed":
                result["status"] = "warning"

    # Save preflight log
    with open(PREFLIGHT_LOG, 'w') as f:
        json.dump(result, f, indent=2)

    return result


# ============================================================
# BOOT SEQUENCE
# ============================================================

def boot(agent_id: str = "orchestrator") -> Tuple[bool, Dict]:
    """
    Execute boot sequence.

    1. Run preflight checks
    2. Verify memory integrity
    3. Create checkpoint
    4. Update version log
    5. Mark session as active

    Returns (success, preflight_result)
    """
    _ensure_state_dirs()

    # Step 1: Preflight
    preflight = run_preflight()

    if preflight["status"] == "failed":
        return False, preflight

    # Step 2: Load integrity state
    integrity = _get_integrity_state()

    # Step 3: Create checkpoint
    checkpoint = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "session": integrity["session_count"] + 1,
        "agent": agent_id,
        "preflight_status": preflight["status"],
        "state_hash": _compute_state_hash(),
        "verified_files": preflight["verified_files"],
        "warnings": preflight["warnings"]
    }

    checkpoint_file = os.path.join(
        CHECKPOINTS_DIR,
        f"{datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')}.json"
    )
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2)

    # Step 4: Update version log
    version_log = _get_version_log()
    version_log["version_log"].append({
        "version": len(version_log["version_log"]) + 1,
        "timestamp": checkpoint["timestamp"],
        "session": checkpoint["session"],
        "agent": agent_id,
        "status": "boot",
        "checkpoint_file": os.path.basename(checkpoint_file)
    })
    _save_version_log(version_log)

    # Step 5: Update integrity state
    integrity["session_count"] += 1
    integrity["last_boot"] = checkpoint["timestamp"]
    integrity["clean_shutdown"] = False  # Will be set True on clean shutdown
    integrity["last_hash"] = checkpoint["state_hash"]
    integrity.setdefault("agents", {})[agent_id] = {
        "last_boot": checkpoint["timestamp"],
        "status": "active"
    }
    _save_integrity_state(integrity)

    return True, preflight


# ============================================================
# SHUTDOWN SEQUENCE
# ============================================================

def shutdown(agent_id: str = "orchestrator", verify_writes: bool = True) -> Tuple[bool, Dict]:
    """
    Execute shutdown sequence.

    1. Compute current state hash
    2. Verify memory files are valid
    3. Create shutdown checkpoint
    4. Update version log
    5. Mark clean shutdown

    Returns (success, result_dict)
    """
    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": agent_id,
        "status": "success",
        "errors": [],
        "state_hash": None
    }

    # Step 1: Compute hash
    result["state_hash"] = _compute_state_hash()

    # Step 2: Verify memory files
    if verify_writes:
        for mf in MEMORY_FILES:
            path = os.path.join(MEMORY_DIR, mf)
            if os.path.exists(path):
                valid, error = _validate_json(path)
                if not valid:
                    result["errors"].append(f"Memory file invalid: {mf} - {error}")
                    result["status"] = "failed"

    # Step 3: Update version log
    version_log = _get_version_log()
    integrity = _get_integrity_state()

    version_log["version_log"].append({
        "version": len(version_log["version_log"]) + 1,
        "timestamp": result["timestamp"],
        "session": integrity["session_count"],
        "agent": agent_id,
        "status": "shutdown",
        "clean": result["status"] == "success"
    })
    _save_version_log(version_log)

    # Step 4: Update integrity state
    integrity["last_shutdown"] = result["timestamp"]
    integrity["clean_shutdown"] = result["status"] == "success"
    integrity["last_hash"] = result["state_hash"]
    if agent_id in integrity.get("agents", {}):
        integrity["agents"][agent_id]["status"] = "stopped"
        integrity["agents"][agent_id]["last_shutdown"] = result["timestamp"]
    _save_integrity_state(integrity)

    return result["status"] == "success", result


# ============================================================
# STATUS & DIAGNOSTICS
# ============================================================

def get_status() -> Dict:
    """Get current system integrity status."""
    integrity = _get_integrity_state()

    return {
        "session_count": integrity.get("session_count", 0),
        "last_boot": integrity.get("last_boot"),
        "last_shutdown": integrity.get("last_shutdown"),
        "clean_shutdown": integrity.get("clean_shutdown", True),
        "agents": integrity.get("agents", {}),
        "current_hash": _compute_state_hash(),
        "hash_match": _compute_state_hash() == integrity.get("last_hash")
    }


def get_recent_checkpoints(n: int = 5) -> List[Dict]:
    """Get N most recent checkpoints."""
    if not os.path.exists(CHECKPOINTS_DIR):
        return []

    files = sorted(os.listdir(CHECKPOINTS_DIR), reverse=True)[:n]
    checkpoints = []

    for f in files:
        try:
            with open(os.path.join(CHECKPOINTS_DIR, f), 'r') as file:
                checkpoints.append(json.load(file))
        except:
            pass

    return checkpoints


# ============================================================
# CONVENIENCE WRAPPERS
# ============================================================

def boot_or_warn() -> bool:
    """Boot with warning output. Returns True if boot succeeded."""
    success, preflight = boot()

    if not success:
        print("[BOOT FAILED]")
        for err in preflight.get("errors", []):
            print(f"  ERROR: {err}")
        return False

    if preflight.get("warnings"):
        for warn in preflight.get("warnings", []):
            print(f"[WARN] {warn}")

    return True


def shutdown_safe() -> bool:
    """Shutdown with error handling. Returns True if clean."""
    try:
        success, result = shutdown()
        if not success:
            print("[SHUTDOWN WARNING]")
            for err in result.get("errors", []):
                print(f"  {err}")
        return success
    except Exception as e:
        print(f"[SHUTDOWN ERROR] {e}")
        return False


# Global to store boot context for Assist visibility
_boot_context = {}


def boot_or_warn_with_context() -> Tuple[bool, Dict]:
    """Boot with warning output. Returns (success, context_for_assist)."""
    global _boot_context
    success, preflight = boot()

    _boot_context = {
        "session": get_status().get("session_count", 0),
        "clean_previous_shutdown": get_status().get("clean_shutdown", True),
        "warnings": preflight.get("warnings", []),
        "errors": preflight.get("errors", []) if not success else [],
        "hash_match": get_status().get("hash_match", True),
    }

    if not success:
        print("[BOOT FAILED]")
        for err in preflight.get("errors", []):
            print(f"  ERROR: {err}")
        return False, _boot_context

    if preflight.get("warnings"):
        for warn in preflight.get("warnings", []):
            print(f"[WARN] {warn}")

    return True, _boot_context


def get_boot_context() -> Dict:
    """Get boot context for Assist visibility."""
    return _boot_context


def get_boot_context_for_ai() -> str:
    """Get boot context formatted for AI consumption."""
    ctx = _boot_context
    if not ctx:
        return ""

    parts = []

    if not ctx.get("clean_previous_shutdown", True):
        parts.append("WARN:unclean_previous_shutdown")

    if not ctx.get("hash_match", True):
        parts.append("WARN:memory_modified_externally")

    if ctx.get("warnings"):
        parts.append(f"WARNINGS:{';'.join(ctx['warnings'][:3])}")

    if ctx.get("errors"):
        parts.append(f"ERRORS:{';'.join(ctx['errors'][:3])}")

    return "|".join(parts) if parts else ""
