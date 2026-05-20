"""NUPRC source configuration (four upstream sources)."""
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

OIL_PAGE = "https://www.nuprc.gov.ng/oil-production-status-report/"
GAS_PAGE = "https://www.nuprc.gov.ng/gas-production-status-report/"
RIG_PAGE = "https://www.nuprc.gov.ng/rig-disposition-report/"
CONCESSION_PDF = (
    "https://www.nuprc.gov.ng/wp-content/uploads/2026/01/"
    "NUPRC-Concession-Situation-Final-Merged-%40-1st-January-2026.pdf"
)

BRONZE_TABLE = {
    "oil": "bronze.oil_production_status_raw",
    "gas": "bronze.gas_production_status_raw",
    "rig": "bronze.rig_disposition_raw",
    "concession": "bronze.concession_situation_raw",
}

ACTIVITY_TYPE = {
    "oil": "oil_production",
    "gas": "gas_production",
    "rig": "rig_disposition",
    "concession": "concession",
}


@dataclass
class SourceConfig:
    key: str
    name: str
    page_url: str
    is_direct_file: bool = False
    direct_url: str = ""

    def normalize_url(self, href: str) -> str:
        base = self.page_url or self.direct_url
        return urljoin(base, href)


SOURCES: List[SourceConfig] = [
    SourceConfig("oil", "Oil Production Status", OIL_PAGE),
    SourceConfig("gas", "Gas Production Status", GAS_PAGE),
    SourceConfig("rig", "Rig Disposition", RIG_PAGE),
    SourceConfig("concession", "Concession Situation", "", True, CONCESSION_PDF),
]
