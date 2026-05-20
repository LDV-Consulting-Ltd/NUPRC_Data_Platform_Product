"""Source URLs for ETL. Concession: direct PDF URL. Oil/Gas/Rig: page URLs (scrape for Excel links)."""
from dataclasses import dataclass
from typing import List

CONCESSION_PDF_URL = (
    "https://www.nuprc.gov.ng/wp-content/uploads/2026/01/"
    "NUPRC-Concession-Situation-Final-Merged-%40-1st-January-2026.pdf"
)

OIL_PAGE = "https://www.nuprc.gov.ng/oil-production-status-report/"
GAS_PAGE = "https://www.nuprc.gov.ng/gas-production-status-report/"
RIG_PAGE = "https://www.nuprc.gov.ng/rig-disposition-report/"


@dataclass
class SourceDef:
    key: str
    name: str
    page_url: str
    is_direct_file: bool
    direct_url: str = ""


SOURCES: List[SourceDef] = [
    SourceDef("oil", "Oil Production Status", OIL_PAGE, False),
    SourceDef("gas", "Gas Production Status", GAS_PAGE, False),
    SourceDef("rig", "Rig Disposition", RIG_PAGE, False),
    SourceDef("concession", "Concession Situation", "", True, CONCESSION_PDF_URL),
]


def get_source(key: str) -> SourceDef:
    for s in SOURCES:
        if s.key == key:
            return s
    raise ValueError(f"Unknown source: {key}")
