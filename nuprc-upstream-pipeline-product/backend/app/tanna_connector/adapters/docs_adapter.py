"""Read-only adapter for markdown documentation and glossaries."""
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


DOC_CATEGORIES: dict[str, str] = {
    "README.md": "documentation/overview",
    "ABOUT.md": "documentation/overview",
    "QUICKSTART.md": "documentation/overview",
    "ETL_README.md": "documentation/etl",
    "PIPELINE_ETL_STEPS.md": "documentation/pipeline",
    "PIPELINE_STEPS.md": "documentation/pipeline",
    "UNIFIED_CATALOG_AND_PIPELINE.md": "documentation/pipeline",
    "DATA_FLOW.md": "documentation/pipeline",
    "DIAGNOSE_PIPELINE.md": "documentation/troubleshooting",
    "DEBUG_PIPELINE.md": "documentation/troubleshooting",
    "TROUBLESHOOTING.md": "documentation/troubleshooting",
    "BRONZE_LOAD_TROUBLESHOOTING.md": "documentation/troubleshooting",
    "CLEAR_STUCK_RUNS.md": "documentation/troubleshooting",
    "CLEAR_STUCK_RUN_QUICK.md": "documentation/troubleshooting",
    "DATA_CATALOG_ALL_SOURCES.md": "documentation/catalog",
    "PIPELINE_PERFORMANCE_AND_SAFETY.md": "documentation/pipeline",
    "PERFORMANCE_OPTIMIZATIONS.md": "documentation/pipeline",
    "OPTIMIZED_EXTRACTORS.md": "documentation/etl",
    "OIL_PRODUCTION_OPTIMIZATION.md": "documentation/etl",
    "RESTART_INSTRUCTIONS.md": "documentation/troubleshooting",
    "RESTART_BACKEND_README.md": "documentation/troubleshooting",
}


KNOWN_MARKDOWN_FILES = list(DOC_CATEGORIES.keys())


def _read_excerpt(path: Path, max_len: int = 500) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return " ".join(text.split())[:max_len]
    except Exception:
        return ""


def scan_markdown_docs() -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    roots = [
        ("project_root", _project_root()),
        ("backend", _backend_root()),
        ("backend_scripts", _backend_root() / "scripts"),
    ]
    seen: set[str] = set()
    for source_label, root in roots:
        if not root.exists():
            continue
        for name in KNOWN_MARKDOWN_FILES:
            path = root / name
            key = str(path)
            if key in seen or not path.exists():
                continue
            seen.add(key)
            try:
                excerpt = _read_excerpt(path)
                items.append({
                    "asset_id": f"doc:{name}",
                    "title": name.replace(".md", "").replace("_", " ").title(),
                    "asset_type": DOC_CATEGORIES.get(name, "documentation"),
                    "path": str(path),
                    "summary": excerpt[:240] if excerpt else None,
                    "content_text": excerpt or None,
                    "source": source_label,
                    "status": "available",
                })
            except Exception as exc:
                warnings.append(f"Could not read {path}: {exc}")
    return items, warnings


def get_table_display_glossary() -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    try:
        from app.services.catalog_registry import TABLE_DISPLAY
        from app.tanna_connector.config import PRIMARY_GOLD_TABLES
        table_to_product = {k: v["id"] for k, v in PRIMARY_GOLD_TABLES.items()}
        for table_name, meta in TABLE_DISPLAY.items():
            items.append({
                "asset_id": f"glossary:table:{table_name}",
                "title": meta.get("display_name") or table_name,
                "asset_type": "metadata/TABLE_DISPLAY",
                "path": "app.services.catalog_registry.TABLE_DISPLAY",
                "summary": (
                    f"subject_area={meta.get('subject_area', '')}; "
                    f"grain={meta.get('grain', '')}; "
                    f"physical_name={table_name}"
                ),
                "source": "catalog_registry.TABLE_DISPLAY",
                "status": "available",
                "linked_data_product_id": table_to_product.get(table_name),
            })
    except Exception as exc:
        warnings.append(f"TABLE_DISPLAY glossary unavailable: {exc}")
    return items, warnings


def get_canonical_columns_glossary() -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    try:
        from app.services.fuzzy_matcher import CANONICAL_COLUMNS
        for canonical, variations in CANONICAL_COLUMNS.items():
            items.append({
                "asset_id": f"glossary:column:{canonical}",
                "title": canonical,
                "asset_type": "metadata/CANONICAL_COLUMNS",
                "path": "app.services.fuzzy_matcher.CANONICAL_COLUMNS",
                "summary": (
                    f"aliases: {', '.join(variations[:5])}"
                    f"{'...' if len(variations) > 5 else ''}"
                ),
                "source": "fuzzy_matcher.CANONICAL_COLUMNS",
                "status": "available",
            })
    except Exception as exc:
        warnings.append(f"CANONICAL_COLUMNS glossary unavailable: {exc}")
    return items, warnings
