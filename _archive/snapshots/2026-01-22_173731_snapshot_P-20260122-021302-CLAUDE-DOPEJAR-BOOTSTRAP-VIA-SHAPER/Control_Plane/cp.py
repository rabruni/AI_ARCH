#!/usr/bin/env python3
"""
cp - Unified Control Plane CLI

Usage:
    cp init                        # Initialize (bootstrap + validate + plan)
    cp status                      # Show system status and mode
    cp list [registry]             # List registries or items
    cp show <name-or-id>           # Show item details
    cp install <name-or-id>        # One-command install flow
    cp verify [name-or-id]         # Verify item or all selected
    cp deps <name-or-id>           # Show dependencies
    cp plan                        # Regenerate plan.json
    cp shape                       # Interactive artifact shaping (L3/L4)
    cp apply-spec --target <id>    # Create spec pack from templates
    cp validate-spec [--all]       # Validate spec packs
    cp gate G0|G1|--all <target>   # Run gates on spec pack
    cp compile-registry <xlsx> --output <path>
    cp flow start <SPEC_ID> [--registry <json>] [--flow-key VISION_TO_VALIDATE]
    cp flow status <SPEC_ID>
    cp flow next <SPEC_ID>
    cp flow done <SPEC_ID> [--phase PhaseX] [--paste|--stdin]
    cp flow resume <SPEC_ID>

Aliases:
    cp ls = cp list
    cp i = cp install
    cp v = cp verify
    cp s = cp status
"""
import json
import subprocess
import sys
from pathlib import Path

# Add repo root to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from Control_Plane.lib import (
    REPO_ROOT,
    CONTROL_PLANE,
    GENERATED_DIR,
    REGISTRIES_DIR,
    find_item,
    find_registry_by_name,
    find_all_registries,
    read_registry,
    write_registry,
    get_id_column,
    count_registry_stats,
    resolve_artifact_path,
)
from Control_Plane.flow_runner import write_compiled_registry, FlowRunner


def cmd_init() -> int:
    """Run full initialization: bootstrap -> validate -> plan."""
    print("=" * 60)
    print("CONTROL PLANE INITIALIZATION")
    print("=" * 60)

    scripts_dir = CONTROL_PLANE / "scripts"

    # Layer 1: Bootstrap
    print("\n[1/3] Bootstrap (environmental checks)...")
    result = subprocess.run(
        ["python3", str(scripts_dir / "bootstrap.py")],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print("\n[FAIL] Bootstrap failed. Fix environmental issues.")
        return 1
    print("[OK] Bootstrap passed")

    # Layer 2: Validate
    print("\n[2/3] Validate (integrity checks)...")
    result = subprocess.run(
        ["python3", str(scripts_dir / "validate.py")],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print("\n[FAIL] Validation failed. Fix integrity issues.")
        return 2
    print("[OK] Validation passed")

    # Layer 3: Plan
    print("\n[3/3] Generate plan...")
    result = subprocess.run(
        ["python3", str(scripts_dir / "apply_selection.py")],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print("\n[FAIL] Plan generation failed.")
        return 3
    print("[OK] Plan generated")

    # Final status
    return cmd_status()


def cmd_status() -> int:
    """Show current system status."""
    stats = count_registry_stats()

    # Determine mode
    if stats["missing"] > 0 or stats["draft"] > 0:
        mode = "BUILD"
    elif stats["selected"] > 0 and stats["active"] >= stats["selected"]:
        mode = "STABILIZE"
    else:
        mode = "BUILD"

    print(f"\n{'=' * 55}")
    print("CONTROL PLANE STATUS")
    print(f"{'=' * 55}")
    print(f"  Registries: {stats['registries']} loaded")
    print(f"  Total:      {stats['total']} items")
    print(f"  Selected:   {stats['selected']} items")
    print(f"  Active:     {stats['active']} items")
    print(f"  Missing:    {stats['missing']} items (to install)")
    print(f"  Draft:      {stats['draft']} items (incomplete)")
    print(f"  Mode:       {mode}")
    print(f"  Plan:       Control_Plane/generated/plan.json")
    print(f"{'=' * 55}")

    if mode == "BUILD":
        print("\nNext: Review plan.json, install missing items")
    else:
        print("\nSystem ready. Focus on verification and improvements.")

    return 0


def cmd_list(registry_name: str = None) -> int:
    """List registries or items in a specific registry."""
    if registry_name:
        reg_path = find_registry_by_name(registry_name)
        if not reg_path:
            print(f"Registry not found: {registry_name}")
            return 1

        headers, rows = read_registry(reg_path)
        id_col = get_id_column(headers)

        print(f"\n{reg_path.relative_to(REPO_ROOT)}")
        print("=" * 70)

        for row in rows:
            item_id = row.get(id_col, "?") if id_col else "?"
            name = row.get("name", "?")
            status = row.get("status", "?")
            selected = "[x]" if row.get("selected", "").lower() == "yes" else "[ ]"
            print(f"  {selected} {name:40} {status:10} ({item_id})")

        print(f"\nTotal: {len(rows)} items")
        return 0

    else:
        # List all registries
        registries = find_all_registries()

        print("\nRegistries")
        print("=" * 70)

        for reg in registries:
            rel_path = reg.relative_to(REPO_ROOT)
            _, rows = read_registry(reg)
            active = sum(1 for r in rows if r.get("status", "").lower() == "active")
            print(f"  {rel_path} ({active}/{len(rows)} active)")

        print(f"\nTotal: {len(registries)} registries")
        return 0


def cmd_show(query: str) -> int:
    """Show details of a specific item (by name or ID)."""
    found = find_item(query)

    if not found:
        print(f"Item not found: {query}")
        return 1

    row, reg_path, _ = found
    item_name = row.get("name", query)
    item_id = row.get("id", "?")

    print(f"\n{item_name} ({item_id})")
    print(f"Registry: {reg_path.relative_to(REPO_ROOT)}")
    print("=" * 60)

    for key, value in row.items():
        if value:
            print(f"  {key}: {value}")

    # Check artifact existence
    artifact_path = row.get("artifact_path", "")
    if artifact_path:
        resolved = resolve_artifact_path(artifact_path)
        exists = "[exists]" if resolved.exists() else "[missing]"
        print(f"\n  Artifact: {exists}")

    return 0


def cmd_install(query: str) -> int:
    """Unified install flow - select, plan, prompt, guide user."""
    print(f"\nInstalling: {query}")
    print("=" * 60)

    # Step 1: Find item
    found = find_item(query)
    if not found:
        print(f"[FAIL] Item not found: {query}")
        return 1

    row, reg_path, row_idx = found
    item_id = row.get("id", query)
    item_name = row.get("name", query)
    current_status = row.get("status", "missing")
    artifact_path = row.get("artifact_path", "")

    print(f"  Item:   {item_name} ({item_id})")
    print(f"  Status: {current_status}")
    print(f"  Path:   {artifact_path}")

    if current_status == "active":
        # Check if artifact actually exists
        if artifact_path:
            resolved = resolve_artifact_path(artifact_path)
            if resolved.exists():
                print(f"\n[OK] Already installed (status=active, artifact exists)")
                return 0
            else:
                print(f"\n[WARN] Status is active but artifact missing. Re-installing...")

    # Step 2: Select item if not already selected
    headers, rows = read_registry(reg_path)
    if rows[row_idx].get("selected", "").lower() != "yes":
        print("\n[1/4] Selecting item...")
        rows[row_idx]["selected"] = "yes"
        write_registry(reg_path, headers, rows)
        print("      selected=yes")

    # Step 3: Check dependencies
    print("\n[2/4] Checking dependencies...")
    deps_str = row.get("dependencies", "")
    if deps_str:
        deps = [d.strip() for d in deps_str.split(",") if d.strip()]
        missing_deps = []
        for dep_id in deps:
            dep_found = find_item(dep_id)
            if not dep_found:
                missing_deps.append(f"{dep_id} (not found)")
            elif dep_found[0].get("status", "").lower() != "active":
                missing_deps.append(f"{dep_id} (not active)")
        if missing_deps:
            print(f"      [WARN] Missing dependencies:")
            for md in missing_deps:
                print(f"        - {md}")
            print("      Install dependencies first.")
    else:
        print("      No dependencies")

    # Step 4: Show install prompt
    print("\n[3/4] Install prompt...")
    prompt_path = CONTROL_PLANE / "control_plane" / "prompts" / "install.md"
    if prompt_path.exists():
        print(f"      See: {prompt_path.relative_to(REPO_ROOT)}")
    else:
        print("      [WARN] Install prompt not found")

    # Step 5: Guide user
    print("\n[4/4] Manual steps required:")
    print("=" * 60)
    print(f"  1. Create artifact at: {artifact_path}")
    print(f"  2. Verify: python3 Control_Plane/cp.py verify {item_id}")
    print(f"  3. Or mark active: python3 Control_Plane/cp.py activate {item_id}")
    print("=" * 60)

    return 0


def cmd_activate(query: str) -> int:
    """Mark an item as active after installation."""
    found = find_item(query)
    if not found:
        print(f"Item not found: {query}")
        return 1

    row, reg_path, row_idx = found
    item_name = row.get("name", query)
    item_id = row.get("id", query)

    headers, rows = read_registry(reg_path)
    old_status = rows[row_idx].get("status", "missing")
    rows[row_idx]["status"] = "active"
    write_registry(reg_path, headers, rows)

    print(f"\n[OK] Activated: {item_name} ({item_id})")
    print(f"     Status: {old_status} -> active")

    return 0


def cmd_verify(query: str = None) -> int:
    """Verify an item or all selected items."""
    if query:
        found = find_item(query)
        if not found:
            print(f"Item not found: {query}")
            return 1

        row, reg_path, _ = found
        item_name = row.get("name", query)
        item_id = row.get("id", query)
        artifact_path = row.get("artifact_path", "")

        print(f"\nVerifying: {item_name} ({item_id})")
        print("=" * 60)

        if not artifact_path:
            print("  [WARN] No artifact_path defined")
            return 1

        resolved = resolve_artifact_path(artifact_path)
        if resolved.exists():
            print(f"  [OK] Artifact exists: {artifact_path}")
            return 0
        else:
            print(f"  [FAIL] Artifact missing: {artifact_path}")
            return 1

    else:
        # Verify all selected items
        print("\nVerifying all selected items...")
        print("=" * 60)

        errors = 0
        checked = 0

        for reg_path in find_all_registries():
            headers, rows = read_registry(reg_path)
            id_col = get_id_column(headers)
            if not id_col:
                continue

            for row in rows:
                if row.get("selected", "").lower() == "yes":
                    checked += 1
                    item_id = row.get(id_col, "?")
                    artifact_path = row.get("artifact_path", "")

                    if artifact_path:
                        resolved = resolve_artifact_path(artifact_path)
                        if resolved.exists():
                            print(f"  [OK] {item_id}")
                        else:
                            print(f"  [FAIL] {item_id}: {artifact_path}")
                            errors += 1
                    else:
                        print(f"  [SKIP] {item_id}: no artifact_path")

        print(f"\nVerified: {checked} items, {errors} failures")
        return errors


def cmd_deps(query: str) -> int:
    """Show dependencies for an item."""
    found = find_item(query)
    if not found:
        print(f"Item not found: {query}")
        return 1

    row, reg_path, _ = found
    item_name = row.get("name", query)
    item_id = row.get("id", query)
    deps_str = row.get("dependencies", "")

    print(f"\nDependencies for: {item_name} ({item_id})")
    print("=" * 60)

    if not deps_str:
        print("  (no dependencies)")
        return 0

    deps = [d.strip() for d in deps_str.split(",") if d.strip()]
    for dep_id in deps:
        dep_found = find_item(dep_id)
        if dep_found:
            dep_row = dep_found[0]
            dep_name = dep_row.get("name", dep_id)
            dep_status = dep_row.get("status", "?")
            symbol = "[OK]" if dep_status == "active" else "[--]"
            print(f"  {symbol} {dep_name} ({dep_id}) - {dep_status}")
        else:
            print(f"  [??] {dep_id} - not found")

    return 0


def cmd_plan() -> int:
    """Regenerate plan.json."""
    scripts_dir = CONTROL_PLANE / "scripts"
    result = subprocess.run(
        ["python3", str(scripts_dir / "apply_selection.py")],
        cwd=REPO_ROOT,
    )
    return result.returncode


def cmd_shape(output_dir: str = None) -> int:
    """Interactive artifact shaping (L3 work items, L4 specs).

    Launches the Shaper v2 interactive CLI for creating structured artifacts.
    Auto-detects altitude (L3 or L4) based on input keywords.

    Args:
        output_dir: Directory for output artifacts (default: current directory)
    """
    try:
        from Control_Plane.modules.design_framework.shaper.cli import ShaperCli
    except ImportError as e:
        print(f"[FAIL] Shaper module not available: {e}")
        print("Ensure Shaper v2 is installed in Control_Plane/modules/design_framework/shaper/")
        return 1

    output_path = Path(output_dir) if output_dir else Path(".")
    shaper = ShaperCli(output_dir=output_path)
    return shaper.run()


def cmd_apply_spec(target: str, force: bool = False) -> int:
    """Create spec pack from templates.

    Args:
        target: Spec pack ID (e.g., SPEC-001)
        force: If True, overwrite existing spec pack
    """
    script = CONTROL_PLANE / "scripts" / "apply_spec_pack.py"

    if not script.is_file():
        print(f"[FAIL] apply_spec_pack.py not found")
        print("Design Framework module may not be installed.")
        return 1

    cmd = ["python3", str(script), "--target", target]
    if force:
        cmd.append("--force")

    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


def cmd_validate_spec(target: str = None, validate_all: bool = False) -> int:
    """Validate spec packs.

    Args:
        target: Specific spec pack to validate (ID or path)
        validate_all: If True, validate all spec packs
    """
    script = CONTROL_PLANE / "scripts" / "validate_spec_pack.py"

    if not script.is_file():
        print(f"[FAIL] validate_spec_pack.py not found")
        print("Design Framework module may not be installed.")
        return 1

    # Extract spec ID from path if given (e.g., docs/specs/TEST-001 -> TEST-001)
    if target and "/" in target:
        target = Path(target).name

    cmd = ["python3", str(script)]
    if validate_all:
        cmd.append("--all")
    elif target:
        cmd.extend(["--target", target])

    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


def cmd_gate(gate: str = None, target: str = None, run_all: bool = False) -> int:
    """Run gates on spec pack.

    Args:
        gate: Gate to run (G0 or G1)
        target: Spec pack ID
        run_all: If True, run all gates in sequence
    """
    script = CONTROL_PLANE / "scripts" / "gate.py"

    if not script.is_file():
        print(f"[FAIL] gate.py not found")
        print("Design Framework module may not be installed.")
        return 1

    # Extract spec ID from path if given
    if target and "/" in target:
        target = Path(target).name

    cmd = ["python3", str(script)]
    if run_all:
        cmd.extend(["--all", target])
    elif gate and target:
        cmd.extend([gate.upper(), target])
    else:
        print("Usage: cp gate G0|G1 <target>")
        print("       cp gate --all <target>")
        return 1

    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


def cmd_compile_registry(xlsx_path: str, output_path: str) -> int:
    """Compile registry XLSX to JSON."""
    output = write_compiled_registry(xlsx_path, output_path)
    print(f"[OK] Registry compiled: {output}")
    return 0


def _default_registry_path() -> Path:
    return CONTROL_PLANE / "registries" / "compiled" / "registry.json"


def _flow_runner_from_session(spec_id: str) -> FlowRunner:
    spec_root = CONTROL_PLANE / "docs" / "specs" / spec_id
    session_path = spec_root / "artifacts" / "session.json"
    if not session_path.exists():
        raise FileNotFoundError("Session not found. Run: cp flow start <SPEC_ID>")
    session = json.loads(session_path.read_text(encoding="utf-8"))
    registry_path = session.get("registry_path") or str(_default_registry_path())
    flow_key = session.get("flow_key") or "DEFAULT"
    return FlowRunner(
        spec_id=spec_id,
        registry_path=Path(registry_path),
        flow_key=flow_key,
        repo_root=REPO_ROOT,
    )


def cmd_flow_start(spec_id: str, registry_path: str | None, flow_key: str | None) -> int:
    registry = Path(registry_path) if registry_path else _default_registry_path()
    if not registry.exists():
        print(f"[FAIL] Registry not found: {registry}")
        return 1
    flow_key = flow_key or _detect_flow_key(registry)
    runner = FlowRunner(
        spec_id=spec_id,
        registry_path=registry,
        flow_key=flow_key,
        repo_root=REPO_ROOT,
    )
    session = runner.start()
    print(f"[OK] Flow started: {spec_id}")
    print(f"     Flow key: {session.get('flow_key')}")
    print(f"     Current phase: {session.get('current_phase')}")
    return 0


def cmd_flow_status(spec_id: str) -> int:
    runner = _flow_runner_from_session(spec_id)
    session = runner.status()
    if not session:
        print(f"[FAIL] No session for {spec_id}")
        return 1
    print(json.dumps(session, indent=2))
    return 0


def cmd_flow_next(spec_id: str) -> int:
    runner = _flow_runner_from_session(spec_id)
    result = runner.next()
    print(json.dumps(result, indent=2))
    if result.get("prompt"):
        print("\n--- Prompt ---\n")
        print(result["prompt"])
    return 0


def cmd_flow_done(spec_id: str, phase_id: str | None, output: str | None) -> int:
    runner = _flow_runner_from_session(spec_id)
    result = runner.done(phase_id=phase_id, output=output)
    print(json.dumps(result, indent=2))
    return 0


def cmd_flow_resume(spec_id: str) -> int:
    runner = _flow_runner_from_session(spec_id)
    result = runner.resume()
    print(json.dumps(result, indent=2))
    if result.get("prompt"):
        print("\n--- Prompt ---\n")
        print(result["prompt"])
    return 0


def _detect_flow_key(registry_path: Path) -> str:
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    flows = data.get("flows", {})
    if flows:
        return next(iter(flows.keys()))
    return "DEFAULT"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    # Command aliases
    aliases = {
        "ls": "list",
        "i": "install",
        "v": "verify",
        "s": "status",
    }
    command = aliases.get(command, command)

    # Dispatch
    if command == "init":
        return cmd_init()
    elif command == "status":
        return cmd_status()
    elif command == "list":
        return cmd_list(args[0] if args else None)
    elif command == "show":
        if not args:
            print("Usage: cp show <name-or-id>")
            return 1
        return cmd_show(" ".join(args))
    elif command == "install":
        if not args:
            print("Usage: cp install <name-or-id>")
            return 1
        return cmd_install(" ".join(args))
    elif command == "activate":
        if not args:
            print("Usage: cp activate <name-or-id>")
            return 1
        return cmd_activate(" ".join(args))
    elif command == "verify":
        return cmd_verify(args[0] if args else None)
    elif command == "deps":
        if not args:
            print("Usage: cp deps <name-or-id>")
            return 1
        return cmd_deps(" ".join(args))
    elif command == "plan":
        return cmd_plan()
    elif command == "shape":
        output_dir = None
        if "--output-dir" in args:
            idx = args.index("--output-dir")
            if idx + 1 < len(args):
                output_dir = args[idx + 1]
        return cmd_shape(output_dir=output_dir)
    elif command == "apply-spec":
        force = "--force" in args
        target = None
        if "--target" in args:
            idx = args.index("--target")
            if idx + 1 < len(args):
                target = args[idx + 1]
        else:
            for arg in args:
                if not arg.startswith("-"):
                    target = arg
                    break
        if not target:
            print("Usage: cp apply-spec --target <id>")
            return 1
        return cmd_apply_spec(target=target, force=force)
    elif command == "validate-spec":
        validate_all = "--all" in args
        target = None
        if "--target" in args:
            idx = args.index("--target")
            if idx + 1 < len(args):
                target = args[idx + 1]
        else:
            # Accept positional argument as target
            for arg in args:
                if not arg.startswith("-"):
                    target = arg
                    break
        return cmd_validate_spec(target=target, validate_all=validate_all)
    elif command == "gate":
        run_all = "--all" in args
        gate = None
        target = None
        for arg in args:
            if arg.upper() in ["G0", "G1"]:
                gate = arg.upper()
            elif not arg.startswith("-"):
                target = arg
        return cmd_gate(gate=gate, target=target, run_all=run_all)
    elif command == "compile-registry":
        if not args:
            print("Usage: cp compile-registry <xlsx> --output <path>")
            return 1
        xlsx_path = args[0]
        output_path = None
        if "--output" in args:
            idx = args.index("--output")
            if idx + 1 < len(args):
                output_path = args[idx + 1]
        if not output_path:
            output_path = str(_default_registry_path())
        return cmd_compile_registry(xlsx_path, output_path)
    elif command == "flow":
        if not args:
            print("Usage: cp flow <start|status|next|done|resume> <SPEC_ID>")
            return 1
        subcommand = args[0].lower()
        if len(args) < 2:
            print("Usage: cp flow <start|status|next|done|resume> <SPEC_ID>")
            return 1
        spec_id = args[1]
        if subcommand == "start":
            registry_path = None
            flow_key = None
            if "--registry" in args:
                idx = args.index("--registry")
                if idx + 1 < len(args):
                    registry_path = args[idx + 1]
            if "--flow-key" in args:
                idx = args.index("--flow-key")
                if idx + 1 < len(args):
                    flow_key = args[idx + 1]
            return cmd_flow_start(spec_id, registry_path, flow_key)
        if subcommand == "status":
            return cmd_flow_status(spec_id)
        if subcommand == "next":
            return cmd_flow_next(spec_id)
        if subcommand == "done":
            phase_id = None
            output = None
            if "--phase" in args:
                idx = args.index("--phase")
                if idx + 1 < len(args):
                    phase_id = args[idx + 1]
            if "--stdin" in args:
                output = sys.stdin.read()
            elif "--paste" in args:
                skip_indices = set()
                if "--phase" in args:
                    idx = args.index("--phase")
                    skip_indices.update({idx, idx + 1})
                if "--paste" in args:
                    idx = args.index("--paste")
                    skip_indices.add(idx)
                remaining = [
                    arg
                    for i, arg in enumerate(args[2:], start=2)
                    if i not in skip_indices and not arg.startswith("--")
                ]
                output = " ".join(remaining).strip()
                if not output:
                    output = sys.stdin.read()
            return cmd_flow_done(spec_id, phase_id, output)
        if subcommand == "resume":
            return cmd_flow_resume(spec_id)
        print("Usage: cp flow <start|status|next|done|resume> <SPEC_ID>")
        return 1
    elif command == "help" or command == "-h" or command == "--help":
        print(__doc__)
        return 0
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
