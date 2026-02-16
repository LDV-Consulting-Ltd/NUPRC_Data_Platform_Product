"""
Concession PDF extraction: section headers (PEL/PPL/PML), full header text,
multi-value cell explosion. Strict header whitelist + blacklist.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

UNKNOWN_CATEGORY = "UNKNOWN"

# Whitelist: line is a header only if it matches PETROLEUM ... LICENCE/LEASE
HEADER_RE = re.compile(
    r"^\s*PETROLEUM\b.*\b(LICEN[CS]ES?|LEASES?)\b.*$",
    re.IGNORECASE,
)

# Blacklist: reject even if HEADER_RE matches (company names, IDs, numbers)
BLACKLIST_RE = re.compile(
    r"\b(LTD|LIMITED|PLC|INC|INCORPORATED|NIG\.|NIGERIA|%|SQ\.?\.?KM|\d{2}/\d{2}/\d{4}|OML\s*\d+|PPL\s*\d+|PEL\s*\d+|PML\s*\d+)\b",
    re.IGNORECASE,
)

# Multi-value columns that may contain newline-separated values
DEFAULT_MULTI_COLUMNS = [
    "name_of_company",
    "block_excised_from",
    "operator_spv",
    "equity_distribution",
]


def is_header_line(line: str) -> bool:
    """
    True only if line is a true section header (e.g. PETROLEUM EXPLORATION LICENCE (PEL)).
    Rejects company lines, concession IDs, numeric-heavy lines.
    """
    if not line or not isinstance(line, str):
        return False
    s = line.strip()
    if not s:
        return False
    if not HEADER_RE.search(s):
        return False
    if BLACKLIST_RE.search(s):
        return False
    return True


def _normalize_header_text(s: str) -> str:
    """Normalize spacing for stored header text."""
    return " ".join((s or "").split())


def explode_row(row: Dict[str, Any], multi_columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Explode multi-value cells (newlines) into multiple rows.
    multi_columns: list of keys that may contain \\n-separated values.
    Returns list of dicts; each has row_split_index, row_split_count at top level and in payload.
    """
    multi_columns = multi_columns or DEFAULT_MULTI_COLUMNS
    lists: Dict[str, List[str]] = {}
    n = 1
    for col in multi_columns:
        val = row.get(col)
        if val is None:
            lists[col] = [""]
            continue
        s = str(val).strip()
        if "\n" in s:
            parts = [p.strip() for p in s.split("\n")]
            if not parts:
                parts = [""]
            lists[col] = parts
            n = max(n, len(lists[col]))
        else:
            lists[col] = [s] if s else [""]
    n = max(n, 1)
    out = []
    for i in range(n):
        new_row = dict(row)
        payload = dict(new_row.get("payload") or {})
        for col in multi_columns:
            vals = lists.get(col, [""])
            v = vals[i] if i < len(vals) else (vals[0] if vals else "")
            new_row[col] = v
            payload[col] = v
        new_row["row_split_index"] = i
        new_row["row_split_count"] = n
        payload["row_split_index"] = i
        payload["row_split_count"] = n
        new_row["payload"] = payload
        out.append(new_row)
    return out


def extract_concession_pdf(file_path: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Extract concession PDF: detect section headers, assign concession_category_full,
    explode multi-value rows. Returns (raw_rows, section_events).
    raw_rows: list of dicts with page_number, row_number_on_page, concession_category_full, payload (with row_split_*).
    section_events: list of dicts with page_number, header_text, concession_category, line_index.
    """
    try:
        import pdfplumber
    except ImportError as e:
        raise RuntimeError("pdfplumber is required for concession PDF extraction; pip install pdfplumber") from e

    raw_rows: List[Dict] = []
    section_events: List[Dict] = []
    current_header_full_text: str = UNKNOWN_CATEGORY

    with pdfplumber.open(file_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\n")
            for line_index, line in enumerate(lines):
                s = line.strip()
                if not s:
                    continue
                if is_header_line(s):
                    current_header_full_text = _normalize_header_text(s)
                    section_events.append({
                        "page_number": page_no,
                        "header_text": current_header_full_text,
                        "concession_category": current_header_full_text,
                        "line_index": line_index,
                    })
                    continue
                # Table row: build row dict; if line has tab/split columns, parse; else single cell
                row_dict = _line_to_row_dict(s, line_index)
                row_dict["concession_category_full"] = current_header_full_text
                row_dict["page_number"] = page_no
                row_dict["row_number_on_page"] = line_index + 1
                # Check for newline-separated values in any known multi column
                has_newline = any(
                    "\n" in str(row_dict.get(k, "")) for k in DEFAULT_MULTI_COLUMNS
                )
                if has_newline:
                    # Build minimal row with keys that might have newlines (from raw_row_text we don't split here)
                    fake_row = {k: row_dict.get(k, "") for k in DEFAULT_MULTI_COLUMNS}
                    if not any(fake_row.values()) and row_dict.get("raw_row_text"):
                        # Simulate: treat raw_row_text as single column for explode
                        fake_row["name_of_company"] = row_dict.get("raw_row_text", "")
                    exploded = explode_row(fake_row, DEFAULT_MULTI_COLUMNS)
                    for ex in exploded:
                        payload = ex.get("payload") or {}
                        payload["raw_row_text"] = row_dict.get("raw_row_text", "")
                        raw_rows.append({
                            "page_number": page_no,
                            "row_number_on_page": row_dict["row_number_on_page"],
                            "concession_category_full": current_header_full_text,
                            "payload": payload,
                        })
                else:
                    payload = row_dict.get("payload") or {}
                    payload["raw_row_text"] = row_dict.get("raw_row_text", s)
                    payload["row_split_index"] = 0
                    payload["row_split_count"] = 1
                    raw_rows.append({
                        "page_number": page_no,
                        "row_number_on_page": row_dict["row_number_on_page"],
                        "concession_category_full": current_header_full_text,
                        "payload": payload,
                    })

    # If we have tables, try table extraction for richer structure (optional second pass)
    _enrich_from_tables(file_path, raw_rows, section_events)
    return raw_rows, section_events


def _line_to_row_dict(line: str, line_index: int) -> Dict[str, Any]:
    """Turn a single text line into a minimal row dict (payload)."""
    return {
        "raw_row_text": line,
        "line_index": line_index,
    }


def _enrich_from_tables(file_path: str, raw_rows: List[Dict], section_events: List[Dict]) -> None:
    """
    Optional: use pdfplumber table extraction to get structured columns per page,
    then merge into raw_rows by page/position. Keeps existing raw_rows and section_events;
    can append or enrich payloads. For now we leave raw_rows as line-based unless
    we add table extraction explicitly.
    """
    pass
