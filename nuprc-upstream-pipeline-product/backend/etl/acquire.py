"""
Reliable file acquisition with httpx: timeouts, retries (exponential backoff + jitter),
User-Agent, redirects, checksum (sha256), size and content-type validation.
Stores files in data/raw/{source}/{yyyy-mm-dd}/.
Ignores chrome-extension:// wrappers: use HTTPS URL only.
"""
import hashlib
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import httpx

from etl.config import (
    DATA_RAW,
    CONNECT_TIMEOUT,
    READ_TIMEOUT,
    MAX_FILE_SIZE,
    USER_AGENT,
)


def _normalize_download_url(url: str) -> str:
    """Strip chrome-extension:// or other non-HTTPS wrappers; return HTTPS URL only."""
    if not url or not isinstance(url, str):
        return url or ""
    s = url.strip()
    # If URL was wrapped by extension, extract the actual https URL
    m = re.search(r"https?://[^\s]+", s)
    if m:
        return m.group(0).rstrip(")\"'")
    if s.startswith("https://") or s.startswith("http://"):
        return s
    return s

# Retries: 3 attempts, exponential backoff + jitter
MAX_RETRIES = 3
BACKOFF_BASE = 1.0
BACKOFF_MAX = 30.0


def _backoff(attempt: int) -> float:
    delay = min(BACKOFF_MAX, BACKOFF_BASE * (2 ** attempt))
    jitter = delay * 0.2 * (2 * random.random() - 1)
    return max(0.1, delay + jitter)


def _storage_dir(source_key: str) -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    d = DATA_RAW / source_key / today
    d.mkdir(parents=True, exist_ok=True)
    return d


def download_file(
    url: str,
    source_key: str,
    filename: Optional[str] = None,
    *,
    max_size: Optional[int] = None,
    allowed_content_types: Optional[List[str]] = None,
) -> Tuple[Optional[Path], Optional[str], Optional[int], Optional[str], Optional[str]]:
    """
    Download a single file with retries and validation.
    Returns: (file_path, sha256_hex, file_size_bytes, content_type, error_message).
    On success error_message is None.
    """
    url = _normalize_download_url(url)
    max_size = max_size or MAX_FILE_SIZE
    storage_dir = _storage_dir(source_key)
    name = filename or url.split("/")[-1].split("?")[0] or "download"
    # Sanitize filename
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)[:200]

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=httpx.Timeout(CONNECT_TIMEOUT, read=READ_TIMEOUT),
                headers={"User-Agent": USER_AGENT},
            ) as client:
                resp = client.get(url)
                resp.raise_for_status()

                content_type = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
                allow_any = allowed_content_types and ("" in allowed_content_types or "application/octet-stream" in allowed_content_types)
                if allowed_content_types and content_type and not allow_any and content_type not in allowed_content_types:
                    last_error = f"content-type not allowed: {content_type}"
                    break

                content = b""
                for chunk in resp.iter_bytes():
                    content += chunk
                    if len(content) > max_size:
                        last_error = f"file too large: {len(content)} > {max_size}"
                        break
                if last_error:
                    break

                if not content:
                    last_error = "empty response"
                    break

                sha = hashlib.sha256(content).hexdigest()
                file_path = storage_dir / f"{sha[:16]}_{safe_name}"
                file_path.write_bytes(content)
                return (file_path, sha, len(content), content_type or None, None)
        except httpx.HTTPStatusError as e:
            last_error = f"HTTP {e.response.status_code}: {e.response.text[:200] if e.response.text else ''}"
        except httpx.TimeoutException as e:
            last_error = f"timeout: {e}"
        except Exception as e:
            last_error = str(e)

        if attempt < MAX_RETRIES - 1:
            time.sleep(_backoff(attempt))

    return (None, None, None, None, last_error or "unknown error")


def download_concession_pdf(url: str, source_key: str = "concession") -> Tuple[Optional[Path], Optional[str], Optional[str]]:
    """
    Download concession PDF from direct URL.
    Returns (file_path, sha256_hex, error_message).
    URL is normalized (e.g. strip chrome-extension wrappers).
    """
    url = _normalize_download_url(url)
    path, sha, size, ct, err = download_file(
        url,
        source_key,
        filename=url.split("/")[-1].split("?")[0],
        allowed_content_types=["application/pdf", "application/octet-stream", ""],
    )
    if err:
        return (None, None, err)
    return (path, sha, None)
