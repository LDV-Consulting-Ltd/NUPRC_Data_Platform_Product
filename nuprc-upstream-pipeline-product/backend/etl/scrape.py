"""
Scrape oil/gas/rig pages and return Excel links ONLY (.xlsx, .xls). No PDFs.
Uses retries with backoff for reliability (fix "Failed to fetch").
"""
import random
import time
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from etl.config import CONNECT_TIMEOUT, READ_TIMEOUT, USER_AGENT

MAX_FETCH_RETRIES = 3
BACKOFF_BASE = 1.0
BACKOFF_MAX = 30.0


def _backoff(attempt: int) -> float:
    delay = min(BACKOFF_MAX, BACKOFF_BASE * (2 ** attempt))
    jitter = delay * 0.2 * (2 * random.random() - 1)
    return max(0.1, delay + jitter)

# Page URLs (same as prompt)
OIL_PAGE = "https://www.nuprc.gov.ng/oil-production-status-report/"
GAS_PAGE = "https://www.nuprc.gov.ng/gas-production-status-report/"
RIG_PAGE = "https://www.nuprc.gov.ng/rig-disposition-report/"

EXCEL_EXT = (".xlsx", ".xls")


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


def get_excel_links_oil() -> tuple:
    """Returns (list of link dicts, error_message)."""
    html, err = fetch_page(OIL_PAGE)
    if err:
        return ([], err)
    return (_extract_excel_links(html, OIL_PAGE), None)


def get_excel_links_gas() -> tuple:
    """Returns (list of link dicts, error_message)."""
    html, err = fetch_page(GAS_PAGE)
    if err:
        return ([], err)
    return (_extract_excel_links(html, GAS_PAGE), None)


def get_excel_links_rig() -> tuple:
    """Returns (list of link dicts, error_message)."""
    html, err = fetch_page(RIG_PAGE)
    if err:
        return ([], err)
    return (_extract_excel_links(html, RIG_PAGE), None)


def get_excel_links_for_source(source: str) -> tuple:
    """source in ('oil','gas','rig'). Returns (links, error)."""
    if source == "oil":
        return get_excel_links_oil()
    if source == "gas":
        return get_excel_links_gas()
    if source == "rig":
        return get_excel_links_rig()
    return ([], f"unknown source: {source}")
