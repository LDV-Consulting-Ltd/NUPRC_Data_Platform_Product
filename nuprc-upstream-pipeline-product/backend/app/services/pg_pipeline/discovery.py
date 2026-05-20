"""Source discovery: extract file links from NUPRC HTML pages."""
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.pg_pipeline.sources import SOURCES, SourceConfig
from etl.scrape import fetch_page

FILE_EXT = (".xlsx", ".xls", ".pdf")


def discover_files() -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Discover downloadable files for all four sources.
    Returns (files, errors) where each file dict has: source_key, source_name, url, file_type.
    """
    files: List[Dict[str, Any]] = []
    errors: List[str] = []
    for src in SOURCES:
        if src.is_direct_file:
            files.append({
                "source_key": src.key,
                "source_name": src.name,
                "url": src.direct_url,
                "file_type": "pdf" if src.direct_url.lower().endswith(".pdf") else "unknown",
            })
            continue
        html, err = fetch_page(src.page_url)
        if err:
            errors.append(f"{src.key}: {err}")
            continue
        for link in _extract_file_links(html, src.page_url):
            files.append({
                "source_key": src.key,
                "source_name": src.name,
                "url": link["url"],
                "file_type": link["file_type"],
            })
    return files, errors


def _extract_file_links(html: str, base_url: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    out: List[Dict[str, str]] = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full = urljoin(base_url, href)
        path = urlparse(full).path.lower()
        if not any(path.endswith(ext) for ext in FILE_EXT):
            continue
        if full in seen:
            continue
        seen.add(full)
        ftype = "pdf" if path.endswith(".pdf") else "excel"
        out.append({"url": full, "file_type": ftype})
    return out
