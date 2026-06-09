"""PetroCore Tanna connector configuration (connector boundary only)."""
import os
import sys
from pathlib import Path

_PRODUCT_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _PRODUCT_ROOT / "backend"
_DEFAULT_SDK_PACKAGES = _PRODUCT_ROOT.parent.parent.parent / "TANNA by LDV" / "packages"
SDK_PACKAGES_PATH = Path(os.getenv("TANNA_SDK_PACKAGES_PATH", str(_DEFAULT_SDK_PACKAGES)))

if SDK_PACKAGES_PATH.exists() and str(SDK_PACKAGES_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PACKAGES_PATH))

if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import tanna_connector_sdk.models as _sdk_models
import tanna_connector_sdk.schemas as _sdk_schemas

if "petrocore" not in _sdk_models.SUPPORTED_MODULE_IDS:
    _extended_ids = frozenset({*_sdk_models.SUPPORTED_MODULE_IDS, "petrocore"})
    _sdk_models.SUPPORTED_MODULE_IDS = _extended_ids
    _sdk_schemas.SUPPORTED_MODULE_IDS = _extended_ids

MODULE_ID = "petrocore"
MODULE_NAME = "PetroCore"
MODULE_CATEGORY = "Upstream Petroleum Intelligence"
MODULE_DESCRIPTION = (
    "NUPRC upstream petroleum regulatory intelligence: oil, gas, rig, and concession "
    "data products exposed read-only to Tanna Core."
)
MODULE_VERSION = "1.0.0"
OWNER = "LDV_Consulting_LTD_X_Mayowa_Lanre_Taiwo"
CONNECTOR_VERSION = "1.0.0"
SOURCE_SYSTEM = "nuprc-upstream-pipeline-product"

FRESHNESS_DEGRADED_THRESHOLD = 70

PRIMARY_DATA_PRODUCTS = {
    "gold_oil_fact_production": {
        "id": "pc-dp-oil-production",
        "name": "Oil Production Data Product",
        "domain": "Oil",
    },
    "gold_gas_fact_production": {
        "id": "pc-dp-gas-production",
        "name": "Gas Production Data Product",
        "domain": "Gas",
    },
    "gold_rig_fact_activity": {
        "id": "pc-dp-rig-activity",
        "name": "Rig Activity Data Product",
        "domain": "Rigs",
    },
    "gold_concession_fact_snapshot": {
        "id": "pc-dp-concession-snapshot",
        "name": "Concession Snapshot Data Product",
        "domain": "Concessions",
    },
}
