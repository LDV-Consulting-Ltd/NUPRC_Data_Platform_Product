# backend/app/services/sources.py
"""
Source configuration and URL definitions for NUPRC data sources.
"""
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class SourceConfig:
    """Configuration for a data source."""
    source_id: str
    name: str
    base_url: str
    bronze_table: str
    description: str


# The 4 NUPRC sources as specified
SOURCES: List[SourceConfig] = [
    SourceConfig(
        source_id="concession_situation",
        name="Concession Situation",
        base_url="https://www.nuprc.gov.ng/wp-content/uploads/2026/02/NUPRC-Concession-Situation-Final-Merged-@-1st-February-2026-V.1.xlsx.pdf",
        bronze_table="bronze.concession_situation_raw",
        description="Concession Situation PDF (Feb 2026)"
    ),
    SourceConfig(
        source_id="oil_production_status",
        name="Oil Production Status",
        base_url="https://www.nuprc.gov.ng/oil-production-status-report/",
        bronze_table="bronze.oil_production_status_raw",
        description="Oil Production Status page with PDF + Excel + archives"
    ),
    SourceConfig(
        source_id="gas_production_status",
        name="Gas Production Status",
        base_url="https://www.nuprc.gov.ng/gas-production-status-report/",
        bronze_table="bronze.gas_production_status_raw",
        description="Gas Production Status page with PDF + Excel + archives"
    ),
    SourceConfig(
        source_id="rig_disposition",
        name="Rig Disposition",
        base_url="https://www.nuprc.gov.ng/rig-disposition-report/",
        bronze_table="bronze.rig_disposition_raw",
        description="Rig Disposition page with PDF + Excel links"
    ),
]


def get_source_by_id(source_id: str) -> SourceConfig:
    """Get a source configuration by ID."""
    for source in SOURCES:
        if source.source_id == source_id:
            return source
    raise ValueError(f"Source not found: {source_id}")


def get_all_sources() -> List[SourceConfig]:
    """Get all source configurations."""
    return SOURCES
