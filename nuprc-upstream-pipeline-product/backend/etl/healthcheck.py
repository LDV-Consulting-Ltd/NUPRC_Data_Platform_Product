"""
Healthcheck: NUPRC pages reachable, concession PDF reachable, DB connectivity.
"""
from typing import List, Tuple

import httpx

from etl.sources import OIL_PAGE, GAS_PAGE, RIG_PAGE, CONCESSION_PDF_URL
from etl.config import USER_AGENT, CONNECT_TIMEOUT, READ_TIMEOUT


def healthcheck() -> Tuple[bool, List[str]]:
    """
    Returns (all_ok, list of message strings).
    """
    messages = []
    ok = True
    timeout = httpx.Timeout(CONNECT_TIMEOUT, read=READ_TIMEOUT)

    # DB
    try:
        from etl.config import get_etl_engine
        from sqlalchemy import text
        with get_etl_engine().connect() as cxn:
            cxn.execute(text("SELECT 1"))
        messages.append("DB: OK")
    except Exception as e:
        messages.append(f"DB: FAILED - {e}")
        ok = False

    # Oil page
    try:
        r = httpx.get(OIL_PAGE, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if r.status_code == 200:
            messages.append("Oil page: OK")
        else:
            messages.append(f"Oil page: HTTP {r.status_code}")
            ok = False
    except Exception as e:
        messages.append(f"Oil page: FAILED - {e}")
        ok = False

    # Gas page
    try:
        r = httpx.get(GAS_PAGE, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if r.status_code == 200:
            messages.append("Gas page: OK")
        else:
            messages.append(f"Gas page: HTTP {r.status_code}")
            ok = False
    except Exception as e:
        messages.append(f"Gas page: FAILED - {e}")
        ok = False

    # Rig page
    try:
        r = httpx.get(RIG_PAGE, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if r.status_code == 200:
            messages.append("Rig page: OK")
        else:
            messages.append(f"Rig page: HTTP {r.status_code}")
            ok = False
    except Exception as e:
        messages.append(f"Rig page: FAILED - {e}")
        ok = False

    # Concession PDF (HEAD to avoid full download; some hosts require GET)
    try:
        r = httpx.head(CONCESSION_PDF_URL, headers={"User-Agent": USER_AGENT}, timeout=timeout, follow_redirects=True)
        if r.status_code == 200:
            messages.append("Concession PDF: OK")
        else:
            messages.append(f"Concession PDF: HTTP {r.status_code}")
            ok = False
    except Exception as e:
        messages.append(f"Concession PDF: FAILED - {e}")
        ok = False

    return ok, messages
