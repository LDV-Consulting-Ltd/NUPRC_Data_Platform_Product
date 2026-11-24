"""
Scrape oil/gas/rig pages and return Excel links ONLY (.xlsx, .xls). No PDFs.
Uses retries with backoff for reliability (fix "Failed to fetch").
"""
import json
import random
import time
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from etl.config import CONNECT_TIMEOUT, READ_TIMEOUT, USER_AGENT
from etl.sources import ACREAGE_SLUG, FILE_BASE, GAS_SLUG, OIL_SLUG, RIG_SLUG, report_api

MAX_FETCH_RETRIES = 3
BACKOFF_BASE = 1.0
BACKOFF_MAX = 30.0


def _backoff(attempt: int) -> float:
    delay = min(BACKOFF_MAX, BACKOFF_BASE * (2 ** attempt))
    jitter = delay * 0.2 * (2 * random.random() - 1)
    return max(0.1, delay + jitter)

EXCEL_EXT = (".xlsx", ".xls")
_SLUGS = {"oil": OIL_SLUG, "gas": GAS_SLUG, "rig": RIG_SLUG}


def _extract_excel_links(html: str, base_url: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        path_lower = parsed.path.lower()
        if path_lower.endswith(EXCEL_EXT) and full not in seen:
            seen.add(full)
            links.append({
                "url": full,
                "filename": (parsed.path or "/").split("/")[-1] or "file.xlsx",
                "file_type": "excel",
            })
    return links


def fetch_page(url: str) -> tuple:
    """Fetch page HTML with retries. Returns (html_string, error_message). error_message is None on success."""
    last_error = None
    for attempt in range(MAX_FETCH_RETRIES):
        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=httpx.Timeout(CONNECT_TIMEOUT, read=READ_TIMEOUT),
                headers={"User-Agent": USER_AGENT},
            ) as client:
                r = client.get(url)
                r.raise_for_status()
                return (r.text, None)
        except httpx.HTTPStatusError as e:
            last_error = f"HTTP {e.response.status_code}"
        except httpx.TimeoutException as e:
            last_error = f"timeout: {e}"
        except Exception as e:
            last_error = str(e)
        if attempt < MAX_FETCH_RETRIES - 1:
            time.sleep(_backoff(attempt))
    return ("", last_error or "unknown error")


def _absolute_upload(path: str) -> str:
    cleaned = path.strip()
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return cleaned
    return FILE_BASE + cleaned.lstrip("/")


def _documents(slug: str) -> tuple:
    """Returns (documents, error). Documents are ordered as published."""
    body, err = fetch_page(report_api(slug))
    if err:
        return ([], err)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        return ([], f"Report catalog was not JSON: {exc}")
    data = payload.get("data") if isinstance(payload, dict) else None
    docs = data.get("documents") if isinstance(data, dict) else None
    if not isinstance(docs, list):
        return ([], "Report catalog did not include documents")
    docs.sort(key=lambda doc: doc.get("order") if isinstance(doc, dict) and isinstance(doc.get("order"), int) else 0)
    return (docs, None)


def excel_links_for_slug(slug: str) -> tuple:
    docs, err = _documents(slug)
    if err:
        return ([], err)
    links = []
    seen = set()
    for doc in docs:
        raw = str(doc.get("excelUrl") or "").strip()
        if not raw:
            continue
        full = _absolute_upload(raw)
        if not urlparse(full).path.lower().endswith(EXCEL_EXT) or full in seen:
            continue
        seen.add(full)
        links.append({
            "url": full,
            "filename": (urlparse(full).path or "/").split("/")[-1] or "file.xlsx",
            "file_type": "excel",
        })
    return (links, None)


def latest_pdf_for_slug(slug: str) -> tuple:
    """Returns (url, error) for the first published PDF on a report page."""
    docs, err = _documents(slug)
    if err:
        return ("", err)
    for doc in docs:
        raw = str(doc.get("pdfUrl") or "").strip()
        if raw:
            return (_absolute_upload(raw), None)
    return ("", "No PDF is published for this report")


def get_excel_links_oil() -> tuple:
    """Returns (list of link dicts, error_message)."""
    return excel_links_for_slug(OIL_SLUG)


def get_excel_links_gas() -> tuple:
    """Returns (list of link dicts, error_message)."""
    return excel_links_for_slug(GAS_SLUG)


def get_excel_links_rig() -> tuple:
    """Returns (list of link dicts, error_message)."""
    return excel_links_for_slug(RIG_SLUG)


def get_excel_links_for_source(source: str) -> tuple:
    """source in ('oil','gas','rig'). Returns (links, error)."""
    slug = _SLUGS.get(source)
    if not slug:
        return ([], f"unknown source: {source}")
    return excel_links_for_slug(slug)


def current_concession_pdf() -> tuple:
    """Live acreage/concession PDF from the reports catalog. Returns (url, error)."""
    return latest_pdf_for_slug(ACREAGE_SLUG)
