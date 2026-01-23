"""Compile registry XLSX files into JSON."""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET


@dataclass
class SheetData:
    name: str
    rows: List[Dict[str, str]]


def compile_registry(xlsx_path: str | Path) -> Dict:
    sheets = _read_xlsx(Path(xlsx_path))
    by_name = {_normalize_name(s.name): s for s in sheets}

    agents = _rows_to_keyed_dict(_select_sheet(by_name, ["agents", "agentmap"]))
    prompts = _rows_to_keyed_dict(_select_sheet(by_name, ["prompts", "promptmap"]))
    gates = _rows_to_keyed_dict(_select_sheet(by_name, ["gates", "gatesmap", "gatemap"]))

    flows_sheet = _select_sheet(by_name, ["flows", "flowmap"])
    flows = _build_flows(flows_sheet)

    session_state = _extract_session_state(_select_sheet(by_name, ["sessionstate", "session"]))

    version = _extract_version(by_name.get("meta")) or "0.1.0"

    return {
        "version": version,
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "agents": agents,
        "prompts": prompts,
        "gates": gates,
        "flows": flows,
        "session_state": session_state,
    }


def write_compiled_registry(xlsx_path: str | Path, output_path: str | Path) -> Path:
    data = compile_registry(xlsx_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return output_path


def _rows_to_keyed_dict(sheet: SheetData | None) -> Dict[str, Dict[str, str]]:
    if not sheet:
        return {}
    result: Dict[str, Dict[str, str]] = {}
    for row in sheet.rows:
        key = row.get("id") or row.get("key") or row.get("name")
        if not key:
            continue
        result[str(key)] = row
    return result


def _build_flows(sheet: SheetData | None) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    flows: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
    if not sheet:
        return flows

    for row in sheet.rows:
        flow_key = _get_value(row, ["flow_key", "flow", "sessionkey"]) or "DEFAULT"
        phase_id = _get_value(row, ["id", "phase_id", "phase"])
        if not phase_id:
            continue
        phase = {
            "id": phase_id,
            "role": _get_value(row, ["role", "rolekey"]),
            "agent_selector": _get_value(row, ["agent_selector", "agentselector"]),
            "prompt_key": _get_value(row, ["prompt_key", "promptkey"]),
            "gate_keys": _split_list(_get_value(row, ["gate_keys", "gatekeys"])),
            "iteration_rule": _get_value(row, ["iteration_rule", "iterationrule"]),
            "constraint_rule": _get_value(row, ["constraint_rule", "constraintrule"]),
            "outputs": _get_value(row, ["outputs"]),
            "stop_condition": _get_value(row, ["stop_condition", "stopcondition"]),
            "max_retries": _to_int(_get_value(row, ["max_retries", "maxretries"])),
        }
        flows.setdefault(flow_key, {"phases": []})["phases"].append(phase)
    return flows


def _extract_session_state(sheet: SheetData | None) -> Dict[str, str]:
    if not sheet or not sheet.rows:
        return {}
    if "key" in sheet.rows[0] and "value" in sheet.rows[0]:
        return {row.get("key"): row.get("value") for row in sheet.rows if row.get("key")}
    return sheet.rows[0]


def _extract_version(sheet: SheetData | None) -> str | None:
    if not sheet or not sheet.rows:
        return None
    first = sheet.rows[0]
    return first.get("version") or first.get("Version")


def _split_list(value: str | None) -> List[str]:
    if not value:
        return []
    parts = []
    for chunk in value.replace(";", ",").split(","):
        chunk = chunk.strip()
        if chunk:
            parts.append(chunk)
    return parts


def _to_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _read_xlsx(path: Path) -> List[SheetData]:
    if not path.is_file():
        raise FileNotFoundError(f"XLSX not found: {path}")

    with zipfile.ZipFile(path) as zf:
        shared_strings = _read_shared_strings(zf)
        workbook_xml = _read_xml(zf, "xl/workbook.xml")
        rels_xml = _read_xml(zf, "xl/_rels/workbook.xml.rels")
        sheet_map = _sheet_relationships(workbook_xml, rels_xml)

        sheets: List[SheetData] = []
        for name, sheet_path in sheet_map:
            sheet_xml = _read_xml(zf, sheet_path)
            rows = _parse_sheet(sheet_xml, shared_strings)
            sheets.append(SheetData(name=name, rows=rows))
        return sheets


def _normalize_name(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def _select_sheet(sheets: Dict[str, SheetData], keys: List[str]) -> SheetData | None:
    for key in keys:
        if key in sheets:
            return sheets[key]
    return None


def _get_value(row: Dict[str, str], keys: List[str]) -> str | None:
    normalized = { _normalize_name(k): v for k, v in row.items() }
    for key in keys:
        normalized_key = _normalize_name(key)
        if normalized_key in normalized:
            return normalized[normalized_key]
    return None


def _read_shared_strings(zf: zipfile.ZipFile) -> List[str]:
    try:
        xml = _read_xml(zf, "xl/sharedStrings.xml")
    except KeyError:
        return []
    strings: List[str] = []
    for si in xml.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
        text_parts = []
        for t in si.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"):
            if t.text:
                text_parts.append(t.text)
        strings.append("".join(text_parts))
    return strings


def _read_xml(zf: zipfile.ZipFile, path: str) -> ET.Element:
    with zf.open(path) as handle:
        return ET.parse(handle).getroot()


def _sheet_relationships(workbook: ET.Element, rels: ET.Element) -> List[Tuple[str, str]]:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rel_ns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    rel_pkg = "{http://schemas.openxmlformats.org/package/2006/relationships}"

    rel_map = {}
    for rel in rels.findall(f"{rel_pkg}Relationship"):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rel_id and target:
            target = target.lstrip("/")
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            rel_map[rel_id] = target

    sheets = []
    for sheet in workbook.findall(f"{ns}sheets/{ns}sheet"):
        name = sheet.attrib.get("name")
        rel_id = sheet.attrib.get(f"{rel_ns}id")
        if name and rel_id and rel_id in rel_map:
            sheets.append((name, rel_map[rel_id]))
    return sheets


def _parse_sheet(sheet: ET.Element, shared_strings: List[str]) -> List[Dict[str, str]]:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rows = []
    headers: List[str] = []

    for row in sheet.findall(f".//{ns}row"):
        values: Dict[int, str] = {}
        for cell in row.findall(f"{ns}c"):
            cell_ref = cell.attrib.get("r")
            if not cell_ref:
                continue
            col_idx = _column_index(cell_ref)
            value = _cell_value(cell, shared_strings)
            values[col_idx] = value

        if not values:
            continue

        max_col = max(values.keys())
        row_values = [values.get(i, "") for i in range(1, max_col + 1)]
        if not headers:
            headers = [h.strip() for h in row_values]
            continue

        row_dict = {}
        for idx, header in enumerate(headers):
            if not header:
                continue
            row_dict[header] = row_values[idx] if idx < len(row_values) else ""
        if row_dict:
            rows.append(row_dict)

    return rows


def _column_index(cell_ref: str) -> int:
    col = ""
    for char in cell_ref:
        if char.isalpha():
            col += char.upper()
        else:
            break
    idx = 0
    for char in col:
        idx = idx * 26 + (ord(char) - ord("A") + 1)
    return idx


def _cell_value(cell: ET.Element, shared_strings: List[str]) -> str:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        text_el = cell.find(f"{ns}is/{ns}t")
        return text_el.text if text_el is not None and text_el.text else ""
    value_el = cell.find(f"{ns}v")
    if value_el is None or value_el.text is None:
        return ""
    raw = value_el.text
    if cell_type == "s":
        try:
            return shared_strings[int(raw)]
        except (ValueError, IndexError):
            return ""
    return raw
