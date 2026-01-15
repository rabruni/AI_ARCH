#!/usr/bin/env python3
"""
Cloud - Cloud Services Bootstrap (BOOT-015)

Purpose: Provision and manage cloud services based on registry configuration.

Usage:
    python cloud.py status                    # Show status of all cloud services
    python cloud.py plan                      # Show what would be provisioned
    python cloud.py up [service_id]           # Provision service(s)
    python cloud.py down [service_id]         # Deprovision service(s)
    python cloud.py check                     # Health check running services

Exit codes:
    0 = Success
    1 = Service not found
    2 = Provisioning failed
    3 = Configuration error
"""

import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def get_repo_root() -> Path:
    """Find repository root (contains .git/)."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").is_dir():
            return parent
    return Path.cwd()


REPO_ROOT = get_repo_root()
CONTROL_PLANE = REPO_ROOT / "Control_Plane"
CLOUD_REGISTRY = CONTROL_PLANE / "registries" / "cloud_services_registry.csv"
CLOUD_STATE = CONTROL_PLANE / "generated" / "cloud_state.json"

# Supported providers and their provisioners
PROVIDERS = {
    "docker": "provision_docker",
    "local": "provision_local",
    "aws": "provision_aws",
    "gcp": "provision_gcp",
    "azure": "provision_azure",
}


def load_cloud_state() -> dict:
    """Load cloud state from file."""
    if CLOUD_STATE.is_file():
        try:
            with open(CLOUD_STATE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"services": {}, "last_updated": None}


def save_cloud_state(state: dict):
    """Save cloud state to file."""
    CLOUD_STATE.parent.mkdir(parents=True, exist_ok=True)
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(CLOUD_STATE, "w") as f:
        json.dump(state, f, indent=2)


def read_cloud_registry() -> tuple[list[str], list[dict]]:
    """Read cloud services registry."""
    if not CLOUD_REGISTRY.is_file():
        return [], []

    with open(CLOUD_REGISTRY, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def get_selected_services() -> list[dict]:
    """Get services marked as selected=yes."""
    _, rows = read_cloud_registry()
    return [r for r in rows if r.get("selected", "").lower() == "yes"]


def find_service_by_id(service_id: str) -> Optional[dict]:
    """Find a service by ID."""
    _, rows = read_cloud_registry()
    for row in rows:
        if row.get("cloud_service_id", "").upper() == service_id.upper():
            return row
    return None


# === Provisioners ===

def provision_docker(service: dict, action: str) -> tuple[bool, str]:
    """Provision/deprovision a Docker container."""
    service_id = service.get("cloud_service_id", "unknown")
    image = service.get("image", "")
    ports = service.get("ports", "")
    env_vars = service.get("env_vars", "")
    container_name = f"cp_{service_id.lower()}"

    if not image:
        return False, "No image specified"

    if action == "up":
        # Check if already running
        check = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={container_name}"],
            capture_output=True, text=True
        )
        if check.stdout.strip():
            return True, f"Already running: {container_name}"

        # Build docker run command
        cmd = ["docker", "run", "-d", "--name", container_name]

        if ports:
            for port in ports.split(","):
                cmd.extend(["-p", port.strip()])

        if env_vars:
            for env in env_vars.split(","):
                cmd.extend(["-e", env.strip()])

        cmd.append(image)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, f"Started: {container_name}"
        else:
            return False, f"Failed: {result.stderr}"

    elif action == "down":
        # Stop and remove
        subprocess.run(["docker", "stop", container_name], capture_output=True)
        subprocess.run(["docker", "rm", container_name], capture_output=True)
        return True, f"Stopped: {container_name}"

    elif action == "check":
        check = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={container_name}"],
            capture_output=True, text=True
        )
        if check.stdout.strip():
            return True, "Running"
        else:
            return False, "Not running"

    return False, f"Unknown action: {action}"


def provision_local(service: dict, action: str) -> tuple[bool, str]:
    """Provision/deprovision a local process."""
    service_id = service.get("cloud_service_id", "unknown")
    command = service.get("command", "")
    pid_file = CONTROL_PLANE / "generated" / f"{service_id.lower()}.pid"

    if not command:
        return False, "No command specified"

    if action == "up":
        # Check if already running
        if pid_file.is_file():
            pid = pid_file.read_text().strip()
            try:
                os.kill(int(pid), 0)
                return True, f"Already running (PID {pid})"
            except (ProcessLookupError, ValueError):
                pid_file.unlink()

        # Start process
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(process.pid))
        return True, f"Started (PID {process.pid})"

    elif action == "down":
        if pid_file.is_file():
            pid = pid_file.read_text().strip()
            try:
                os.kill(int(pid), 15)  # SIGTERM
                pid_file.unlink()
                return True, f"Stopped (PID {pid})"
            except (ProcessLookupError, ValueError):
                pid_file.unlink()
                return True, "Process not found, cleaned up"
        return True, "Not running"

    elif action == "check":
        if pid_file.is_file():
            pid = pid_file.read_text().strip()
            try:
                os.kill(int(pid), 0)
                return True, f"Running (PID {pid})"
            except (ProcessLookupError, ValueError):
                return False, "Not running (stale PID)"
        return False, "Not running"

    return False, f"Unknown action: {action}"


def provision_aws(service: dict, action: str) -> tuple[bool, str]:
    """Placeholder for AWS provisioning."""
    return False, "AWS provisioning not yet implemented. Use Terraform or AWS CDK."


def provision_gcp(service: dict, action: str) -> tuple[bool, str]:
    """Placeholder for GCP provisioning."""
    return False, "GCP provisioning not yet implemented. Use Terraform or Pulumi."


def provision_azure(service: dict, action: str) -> tuple[bool, str]:
    """Placeholder for Azure provisioning."""
    return False, "Azure provisioning not yet implemented. Use Terraform or Bicep."


def get_provisioner(provider: str):
    """Get provisioner function for provider."""
    provisioners = {
        "docker": provision_docker,
        "local": provision_local,
        "aws": provision_aws,
        "gcp": provision_gcp,
        "azure": provision_azure,
    }
    return provisioners.get(provider.lower())


# === Commands ===

def cmd_status():
    """Show status of all cloud services."""
    _, rows = read_cloud_registry()
    state = load_cloud_state()

    if not rows:
        print("\nNo cloud services registry found.")
        print(f"Create: {CLOUD_REGISTRY.relative_to(REPO_ROOT)}")
        print("\nRequired columns:")
        print("  cloud_service_id, name, provider, selected, status")
        return 0

    print("\nCloud Services Status")
    print("=" * 70)

    for row in rows:
        service_id = row.get("cloud_service_id", "?")
        name = row.get("name", "?")
        provider = row.get("provider", "?")
        selected = row.get("selected", "no")
        status = row.get("status", "?")

        # Check runtime status
        runtime = "unknown"
        provisioner = get_provisioner(provider)
        if provisioner and selected.lower() == "yes":
            success, msg = provisioner(row, "check")
            runtime = "UP" if success else "DOWN"

        selected_mark = "✓" if selected.lower() == "yes" else " "
        print(f"  [{selected_mark}] {service_id:12} {provider:8} {runtime:6} {name}")

    print()
    return 0


def cmd_plan():
    """Show what would be provisioned."""
    services = get_selected_services()

    if not services:
        print("\nNo services selected for provisioning.")
        return 0

    print("\nProvisioning Plan")
    print("=" * 70)

    for svc in services:
        service_id = svc.get("cloud_service_id", "?")
        name = svc.get("name", "?")
        provider = svc.get("provider", "?")
        image = svc.get("image", "")
        command = svc.get("command", "")

        print(f"\n  {service_id}: {name}")
        print(f"    Provider: {provider}")
        if image:
            print(f"    Image: {image}")
        if command:
            print(f"    Command: {command}")

        provisioner = get_provisioner(provider)
        if not provisioner:
            print(f"    ⚠ Provider '{provider}' not supported")

    print(f"\nTotal: {len(services)} services to provision")
    return 0


def cmd_up(service_id: Optional[str] = None):
    """Provision service(s)."""
    if service_id:
        service = find_service_by_id(service_id)
        if not service:
            print(f"Service not found: {service_id}")
            return 1
        services = [service]
    else:
        services = get_selected_services()

    if not services:
        print("No services to provision.")
        return 0

    print("\nProvisioning Services")
    print("=" * 70)

    state = load_cloud_state()
    success_count = 0

    for svc in services:
        sid = svc.get("cloud_service_id", "?")
        name = svc.get("name", "?")
        provider = svc.get("provider", "?")

        print(f"\n  {sid}: {name}")

        provisioner = get_provisioner(provider)
        if not provisioner:
            print(f"    ✗ Provider '{provider}' not supported")
            continue

        success, msg = provisioner(svc, "up")
        symbol = "✓" if success else "✗"
        print(f"    [{symbol}] {msg}")

        if success:
            success_count += 1
            state["services"][sid] = {
                "status": "running",
                "provider": provider,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

    save_cloud_state(state)
    print(f"\nProvisioned: {success_count}/{len(services)} services")
    return 0 if success_count == len(services) else 2


def cmd_down(service_id: Optional[str] = None):
    """Deprovision service(s)."""
    if service_id:
        service = find_service_by_id(service_id)
        if not service:
            print(f"Service not found: {service_id}")
            return 1
        services = [service]
    else:
        services = get_selected_services()

    if not services:
        print("No services to deprovision.")
        return 0

    print("\nDeprovisioning Services")
    print("=" * 70)

    state = load_cloud_state()

    for svc in services:
        sid = svc.get("cloud_service_id", "?")
        name = svc.get("name", "?")
        provider = svc.get("provider", "?")

        print(f"\n  {sid}: {name}")

        provisioner = get_provisioner(provider)
        if not provisioner:
            print(f"    ✗ Provider '{provider}' not supported")
            continue

        success, msg = provisioner(svc, "down")
        symbol = "✓" if success else "✗"
        print(f"    [{symbol}] {msg}")

        if sid in state["services"]:
            del state["services"][sid]

    save_cloud_state(state)
    print("\nDeprovisioning complete")
    return 0


def cmd_check():
    """Health check running services."""
    services = get_selected_services()

    if not services:
        print("No services to check.")
        return 0

    print("\nHealth Check")
    print("=" * 70)

    healthy = 0
    unhealthy = 0

    for svc in services:
        sid = svc.get("cloud_service_id", "?")
        name = svc.get("name", "?")
        provider = svc.get("provider", "?")

        provisioner = get_provisioner(provider)
        if not provisioner:
            print(f"  [?] {sid}: Provider '{provider}' not supported")
            continue

        success, msg = provisioner(svc, "check")
        if success:
            print(f"  [✓] {sid}: {msg}")
            healthy += 1
        else:
            print(f"  [✗] {sid}: {msg}")
            unhealthy += 1

    print(f"\nHealthy: {healthy}, Unhealthy: {unhealthy}")
    return 0 if unhealthy == 0 else 2


def cmd_init_registry():
    """Create initial cloud services registry."""
    if CLOUD_REGISTRY.is_file():
        print(f"Registry already exists: {CLOUD_REGISTRY.relative_to(REPO_ROOT)}")
        return 0

    CLOUD_REGISTRY.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "cloud_service_id",
        "name",
        "provider",
        "selected",
        "status",
        "image",
        "command",
        "ports",
        "env_vars",
        "depends_on",
        "description",
    ]

    # Example services
    examples = [
        {
            "cloud_service_id": "CLOUD-001",
            "name": "Redis Cache",
            "provider": "docker",
            "selected": "no",
            "status": "missing",
            "image": "redis:alpine",
            "ports": "6379:6379",
            "description": "In-memory cache for sessions",
        },
        {
            "cloud_service_id": "CLOUD-002",
            "name": "PostgreSQL",
            "provider": "docker",
            "selected": "no",
            "status": "missing",
            "image": "postgres:15-alpine",
            "ports": "5432:5432",
            "env_vars": "POSTGRES_PASSWORD=dev",
            "description": "Primary database",
        },
    ]

    with open(CLOUD_REGISTRY, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for ex in examples:
            row = {h: ex.get(h, "") for h in headers}
            writer.writerow(row)

    print(f"Created: {CLOUD_REGISTRY.relative_to(REPO_ROOT)}")
    print(f"Added {len(examples)} example services")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python cloud.py <command> [args]")
        print("\nCommands:")
        print("  status              Show status of all cloud services")
        print("  plan                Show what would be provisioned")
        print("  up [service_id]     Provision service(s)")
        print("  down [service_id]   Deprovision service(s)")
        print("  check               Health check running services")
        print("  init                Create initial cloud_services_registry.csv")
        print("\nProviders supported:")
        print("  docker, local, aws*, gcp*, azure*")
        print("  (* = placeholder, use Terraform/Pulumi)")
        return 1

    command = sys.argv[1].lower()

    if command == "status":
        return cmd_status()
    elif command == "plan":
        return cmd_plan()
    elif command == "up":
        service_id = sys.argv[2].upper() if len(sys.argv) > 2 else None
        return cmd_up(service_id)
    elif command == "down":
        service_id = sys.argv[2].upper() if len(sys.argv) > 2 else None
        return cmd_down(service_id)
    elif command == "check":
        return cmd_check()
    elif command == "init":
        return cmd_init_registry()
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
