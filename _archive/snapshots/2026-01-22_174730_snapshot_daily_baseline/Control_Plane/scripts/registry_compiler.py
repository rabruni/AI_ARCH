#!/usr/bin/env python3
"""
Registry Compiler: Parse Excel workbook into JSON registry files.

Uses stdlib only (zipfile + xml.etree) - no pip installs required.
Input: Control_Plane/registries/Prompt Map.xlsx
Output: Control_Plane/generated/compiled_registry.json
"""

import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONTROL_PLANE = REPO_ROOT / "Control_Plane"
REGISTRIES_DIR = CONTROL_PLANE / "registries"
GENERATED_DIR = CONTROL_PLANE / "generated"

XLSX_FILE = REGISTRIES_DIR / "Prompt Map.xlsx"
OUTPUT_FILE = GENERATED_DIR / "compiled_registry.json"

# XML namespaces used in xlsx
NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def extract_sheet_names(workbook_xml: str) -> Dict[str, str]:
    """Extract sheet names and their rIds from workbook.xml."""
    root = ET.fromstring(workbook_xml)
    sheets = {}
    for sheet in root.findall(".//main:sheet", NS):
        name = sheet.get("name")
        rid = sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        sheets[rid] = name
    return sheets


def extract_relationships(rels_xml: str) -> Dict[str, str]:
    """Extract relationship ID to target file mapping."""
    root = ET.fromstring(rels_xml)
    rels = {}
    for rel in root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
        rid = rel.get("Id")
        target = rel.get("Target")
        rels[rid] = target
    return rels


def parse_cell_value(cell: ET.Element) -> Any:
    """Extract value from a cell element."""
    cell_type = cell.get("t")

    # Inline string
    if cell_type == "inlineStr":
        is_elem = cell.find("main:is", NS)
        if is_elem is not None:
            t_elem = is_elem.find("main:t", NS)
            if t_elem is not None and t_elem.text:
                return t_elem.text
        return ""

    # Boolean
    if cell_type == "b":
        v_elem = cell.find("main:v", NS)
        if v_elem is not None:
            return v_elem.text == "1"
        return False

    # Number
    if cell_type == "n" or cell_type is None:
        v_elem = cell.find("main:v", NS)
        if v_elem is not None and v_elem.text:
            try:
                if "." in v_elem.text:
                    return float(v_elem.text)
                return int(v_elem.text)
            except ValueError:
                return v_elem.text
        return None

    # Default: try to get value
    v_elem = cell.find("main:v", NS)
    if v_elem is not None:
        return v_elem.text
    return ""


def col_letter_to_index(col: str) -> int:
    """Convert column letter (A, B, AA, etc.) to 0-based index."""
    result = 0
    for char in col:
        result = result * 26 + (ord(char.upper()) - ord('A') + 1)
    return result - 1


def parse_cell_ref(ref: str) -> tuple:
    """Parse cell reference like 'A1' into (row, col) 0-based indices."""
    col_str = ""
    row_str = ""
    for char in ref:
        if char.isalpha():
            col_str += char
        else:
            row_str += char
    return int(row_str) - 1, col_letter_to_index(col_str)


def parse_sheet(sheet_xml: str) -> List[List[Any]]:
    """Parse a worksheet XML into a 2D list of values."""
    root = ET.fromstring(sheet_xml)

    # Find dimension to know grid size
    dimension = root.find("main:dimension", NS)
    if dimension is not None:
        ref = dimension.get("ref", "A1")
        if ":" in ref:
            _, end = ref.split(":")
            max_row, max_col = parse_cell_ref(end)
        else:
            max_row, max_col = 0, 0
    else:
        max_row, max_col = 100, 26  # fallback

    # Initialize grid
    grid = [[None for _ in range(max_col + 1)] for _ in range(max_row + 1)]

    # Parse all cells
    for row in root.findall(".//main:row", NS):
        for cell in row.findall("main:c", NS):
            ref = cell.get("r")
            if ref:
                row_idx, col_idx = parse_cell_ref(ref)
                if row_idx < len(grid) and col_idx < len(grid[0]):
                    grid[row_idx][col_idx] = parse_cell_value(cell)

    return grid


def grid_to_records(grid: List[List[Any]], has_header: bool = True) -> List[Dict[str, Any]]:
    """Convert grid to list of dicts using first row as headers."""
    if not grid or not grid[0]:
        return []

    # Clean headers
    headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(grid[0])]

    records = []
    start_row = 1 if has_header else 0

    for row in grid[start_row:]:
        # Skip empty rows
        if not any(cell is not None and cell != "" for cell in row):
            continue

        record = {}
        for i, header in enumerate(headers):
            if i < len(row):
                record[header] = row[i]
            else:
                record[header] = None
        records.append(record)

    return records


def compile_registry(xlsx_path: Path = XLSX_FILE) -> Dict[str, Any]:
    """
    Compile Excel workbook into structured registry JSON.

    Returns dict with keys:
    - agent_map: List of agent definitions
    - prompt_map: List of prompt definitions
    - gates_map: List of gate definitions
    - flow_map: List of flow step definitions
    - session_state: List of session state definitions
    - metadata: Compilation metadata
    """
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Registry workbook not found: {xlsx_path}")

    registry = {
        "metadata": {
            "source": str(xlsx_path),
            "version": "1.0.0",
        },
        "agent_map": [],
        "prompt_map": [],
        "gates_map": [],
        "flow_map": [],
        "session_state": [],
    }

    with zipfile.ZipFile(xlsx_path, 'r') as zf:
        # Read workbook structure
        workbook_xml = zf.read("xl/workbook.xml").decode("utf-8")
        rels_xml = zf.read("xl/_rels/workbook.xml.rels").decode("utf-8")

        sheet_names = extract_sheet_names(workbook_xml)
        relationships = extract_relationships(rels_xml)

        # Map sheet names to file paths
        sheet_files = {}
        for rid, name in sheet_names.items():
            if rid in relationships:
                target = relationships[rid]
                sheet_files[name] = f"xl/{target}" if not target.startswith("xl/") else target

        # Parse each known sheet
        sheet_mapping = {
            "Agent Map": "agent_map",
            "Prompt Map": "prompt_map",
            "Gates Map": "gates_map",
            "Flow Map": "flow_map",
            "Session State": "session_state",
        }

        for sheet_name, registry_key in sheet_mapping.items():
            if sheet_name in sheet_files:
                try:
                    sheet_path = sheet_files[sheet_name]
                    # Handle relative paths
                    if not sheet_path.startswith("xl/"):
                        sheet_path = f"xl/worksheets/{sheet_path.split('/')[-1]}"

                    sheet_xml = zf.read(sheet_path).decode("utf-8")
                    grid = parse_sheet(sheet_xml)
                    records = grid_to_records(grid)
                    registry[registry_key] = records
                except Exception as e:
                    print(f"Warning: Failed to parse sheet '{sheet_name}': {e}")

    return registry


def save_registry(registry: Dict[str, Any], output_path: Path = OUTPUT_FILE) -> None:
    """Save compiled registry to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    print(f"[OK] Compiled registry saved to: {output_path}")


def main():
    """Main entry point."""
    import sys

    xlsx_path = XLSX_FILE
    output_path = OUTPUT_FILE

    # Allow custom paths via args
    if len(sys.argv) > 1:
        xlsx_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    try:
        print(f"[...] Compiling registry from: {xlsx_path}")
        registry = compile_registry(xlsx_path)

        # Print summary
        print(f"      Agent Map:     {len(registry['agent_map'])} entries")
        print(f"      Prompt Map:    {len(registry['prompt_map'])} entries")
        print(f"      Gates Map:     {len(registry['gates_map'])} entries")
        print(f"      Flow Map:      {len(registry['flow_map'])} entries")
        print(f"      Session State: {len(registry['session_state'])} entries")

        save_registry(registry, output_path)
        return 0
    except Exception as e:
        print(f"[FAIL] Registry compilation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
