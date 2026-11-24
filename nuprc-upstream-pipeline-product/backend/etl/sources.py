"""Source URLs for ETL. NUPRC moved publications onto /reports."""
from dataclasses import dataclass
from typing import List

REPORTS_INDEX = "https://www.nuprc.gov.ng/reports"
FILE_BASE = "https://www.nuprc.gov.ng/upload/"

OIL_SLUG = "oil-production-report"
GAS_SLUG = "gas-production-status-report"
RIG_SLUG = "rig-disposition-report"
ACREAGE_SLUG = "acreage-situation-report"

OIL_PAGE = f"{REPORTS_INDEX}/{OIL_SLUG}"
GAS_PAGE = f"{REPORTS_INDEX}/{GAS_SLUG}"
RIG_PAGE = f"{REPORTS_INDEX}/{RIG_SLUG}"
ACREAGE_PAGE = f"{REPORTS_INDEX}/{ACREAGE_SLUG}"

# Current acreage/concession PDF from the reports catalog. The pipeline resolves the live file at run time.
CONCESSION_PDF_URL = "https://www.nuprc.gov.ng/upload/nuprc_reports/November_8e4fb84b2c7c9ef76f361ebf.pdf"


def report_api(slug: str) -> str:
    return f"https://www.nuprc.gov.ng/api/report-pages/slug/{slug}"


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
    SourceDef("concession", "Acreage Situation", ACREAGE_PAGE, True, CONCESSION_PDF_URL),
]


def get_source(key: str) -> SourceDef:
    for s in SOURCES:
        if s.key == key:
            return s
    raise ValueError(f"Unknown source: {key}")
