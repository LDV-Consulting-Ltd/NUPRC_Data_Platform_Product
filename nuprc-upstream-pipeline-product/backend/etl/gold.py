"""
Gold: dataset-specific dimensional marts built from Silver only.
Each dataset (oil, gas, rig, concession) gets its own star/snapshot model.
Conformed: gold_dim_date only. No forced shared dimensions.
Mode-aware: oil -> oil mart only; gas -> gas mart only; rig -> rig mart; concession -> concession mart; full -> all.
"""
import json
import logging
from datetime import date
from pathlib import Path
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from etl.config import get_silver_engine, get_gold_engine

logger = logging.getLogger(__name__)

# Which Silver fact tables feed which marts per mode
MODE_TO_MARTS = {
    "full": ["oil", "gas", "rig", "concession"],
    "oil": ["oil"],
    "gas": ["gas"],
    "rig": ["rig"],
    "concession": ["concession"],
}


def _numeric(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(Decimal(str(val)))
    except Exception:
        return None


def _decimal(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except Exception:
        return None


def _str(val: Any, max_len: int = 500) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()[:max_len]
    return s or None


def _parse_payload(payload: Any) -> dict:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload) or {}
        except Exception:
            return {}
    return {}


def ensure_gold_schema(engine=None):
    """Create Gold schema and dataset-specific mart tables (migration 006)."""
    engine = engine or get_gold_engine()
    path = Path(__file__).parent / "migrations" / "006_gold_dataset_marts.sql"
    if not path.exists():
        with engine.begin() as cxn:
            cxn.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
            cxn.execute(text("""
                CREATE TABLE IF NOT EXISTS gold.gold_dim_date (
                    date_key INT PRIMARY KEY, date_actual DATE NOT NULL, year INT, month INT, day INT
                )
            """))
        return
    ddl = path.read_text()
    statements = []
    current = []
    depth = 0
    for line in ddl.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        current.append(line)
        depth += line.count("(") - line.count(")")
        if ";" in line and depth <= 0:
            stmt = "\n".join(current).strip()
            if stmt and "CREATE" in stmt.upper():
                statements.append(stmt)
            current = []
            depth = 0
    if current:
        stmt = "\n".join(current).strip()
        if stmt and "CREATE" in stmt.upper():
            statements.append(stmt)
    with engine.begin() as cxn:
        for stmt in statements:
            if not stmt.strip():
                continue
            try:
                cxn.execute(text(stmt))
            except Exception as e:
                logger.debug("Gold DDL step: %s", e)


def _sync_conformed_date(silver, gold) -> None:
    """Sync gold_dim_date from Silver (conformed dimension)."""
    with silver.connect() as scxn:
        with gold.begin() as gcxn:
            for row in scxn.execute(text("SELECT date_key, date_actual, year, month, day FROM silver.dim_date")).mappings():
                r = dict(row)
                gcxn.execute(
                    text("""
                        INSERT INTO gold.gold_dim_date (date_key, date_actual, year, month, day)
                        VALUES (:date_key, :date_actual, :year, :month, :day)
                        ON CONFLICT (date_key) DO NOTHING
                    """),
                    r,
                )


def _build_oil_mart(silver, gold) -> Dict[str, int]:
    """Oil Production Mart: gold_oil_dim_operator, gold_oil_fact_production. Grain: date × operator."""
    metrics = {}
    with silver.connect() as scxn:
        rows = list(scxn.execute(text("SELECT date_key, operator_key, payload FROM silver.fact_oil_production")).mappings().all())
    if not rows:
        return {"gold_oil_fact_production": 0}

    # Resolve operator_key -> operator_name from Silver
    op_keys = list({r["operator_key"] for r in rows})
    with silver.connect() as scxn:
        op_rows = list(scxn.execute(text("SELECT operator_key, operator_name FROM silver.dim_operator WHERE operator_key = ANY(:keys)"), {"keys": op_keys}).mappings().all())
    op_map = {r["operator_key"]: r["operator_name"] for r in op_rows}

    with gold.begin() as gcxn:
        for op_key, name in op_map.items():
            name = _str(name, 200) or "Unknown"
            gcxn.execute(
                text("INSERT INTO gold.gold_oil_dim_operator (operator_name) VALUES (:n) ON CONFLICT (operator_name) DO NOTHING"),
                {"n": name},
            )
        name_to_sk = {r[0]: r[1] for r in gcxn.execute(text("SELECT operator_name, operator_sk FROM gold.gold_oil_dim_operator")).fetchall()}

    inserted = 0
    with gold.begin() as gcxn:
        for r in rows:
            payload = _parse_payload(r.get("payload"))
            vol = _decimal(payload.get("production") or payload.get("volume") or payload.get("production_volume") or payload.get("oil_production") or 0)
            unit = _str(payload.get("unit") or payload.get("production_unit") or "bbl", 50) or "bbl"
            condensate = _decimal(payload.get("condensate") or payload.get("condensate_volume"))
            op_name = op_map.get(r["operator_key"]) or "Unknown"
            op_sk = name_to_sk.get(_str(op_name, 200) or "Unknown")
            if op_sk is None:
                continue
            try:
                gcxn.execute(
                    text("""
                        INSERT INTO gold.gold_oil_fact_production (date_key, operator_sk, production_volume, production_unit, condensate_volume)
                        VALUES (:date_key, :operator_sk, :production_volume, :production_unit, :condensate_volume)
                    """),
                    {"date_key": r["date_key"], "operator_sk": op_sk, "production_volume": vol, "production_unit": unit, "condensate_volume": condensate},
                )
                inserted += 1
            except Exception:
                pass
    metrics["gold_oil_fact_production"] = inserted
    return metrics


def _build_gas_mart(silver, gold) -> Dict[str, int]:
    """Gas Production Mart: gold_gas_dim_operator, gold_gas_fact_production. Grain: date × operator."""
    metrics = {}
    with silver.connect() as scxn:
        rows = list(scxn.execute(text("SELECT date_key, operator_key, payload FROM silver.fact_gas_production")).mappings().all())
    if not rows:
        return {"gold_gas_fact_production": 0}

    op_keys = list({r["operator_key"] for r in rows})
    with silver.connect() as scxn:
        op_rows = list(scxn.execute(text("SELECT operator_key, operator_name FROM silver.dim_operator WHERE operator_key = ANY(:keys)"), {"keys": op_keys}).mappings().all())
    op_map = {r["operator_key"]: r["operator_name"] for r in op_rows}

    with gold.begin() as gcxn:
        for op_key, name in op_map.items():
            name = _str(name, 200) or "Unknown"
            gcxn.execute(
                text("INSERT INTO gold.gold_gas_dim_operator (operator_name) VALUES (:n) ON CONFLICT (operator_name) DO NOTHING"),
                {"n": name},
            )
        name_to_sk = {r[0]: r[1] for r in gcxn.execute(text("SELECT operator_name, operator_sk FROM gold.gold_gas_dim_operator")).fetchall()}

    inserted = 0
    with gold.begin() as gcxn:
        for r in rows:
            payload = _parse_payload(r.get("payload"))
            vol = _decimal(payload.get("gas_production") or payload.get("production") or payload.get("volume") or payload.get("production_volume") or 0)
            unit = _str(payload.get("unit") or payload.get("production_unit") or "mmcf", 50) or "mmcf"
            flared = _decimal(payload.get("flared") or payload.get("flared_volume"))
            utilized = _decimal(payload.get("utilized") or payload.get("utilized_volume"))
            op_name = op_map.get(r["operator_key"]) or "Unknown"
            op_sk = name_to_sk.get(_str(op_name, 200) or "Unknown")
            if op_sk is None:
                continue
            try:
                gcxn.execute(
                    text("""
                        INSERT INTO gold.gold_gas_fact_production (date_key, operator_sk, gas_volume, gas_unit, flared_volume, utilized_volume)
                        VALUES (:date_key, :operator_sk, :gas_volume, :gas_unit, :flared_volume, :utilized_volume)
                    """),
                    {"date_key": r["date_key"], "operator_sk": op_sk, "gas_volume": vol, "gas_unit": unit, "flared_volume": flared, "utilized_volume": utilized},
                )
                inserted += 1
            except Exception:
                pass
    metrics["gold_gas_fact_production"] = inserted
    return metrics


def _build_rig_mart(silver, gold) -> Dict[str, int]:
    """Rig Disposition Mart: gold_rig_dim_operator, gold_rig_dim_rig, gold_rig_dim_status, gold_rig_fact_activity."""
    metrics = {}
    with silver.connect() as scxn:
        rows = list(scxn.execute(text("SELECT date_key, operator_key, payload FROM silver.fact_rig_disposition")).mappings().all())
    if not rows:
        return {"gold_rig_fact_activity": 0}

    op_keys = list({r["operator_key"] for r in rows})
    with silver.connect() as scxn:
        op_rows = list(scxn.execute(text("SELECT operator_key, operator_name FROM silver.dim_operator WHERE operator_key = ANY(:keys)"), {"keys": op_keys}).mappings().all())
    op_map = {r["operator_key"]: r["operator_name"] for r in op_rows}

    with gold.begin() as gcxn:
        for _, name in op_map.items():
            name = _str(name, 200) or "Unknown"
            gcxn.execute(text("INSERT INTO gold.gold_rig_dim_operator (operator_name) VALUES (:n) ON CONFLICT (operator_name) DO NOTHING"), {"n": name})
        for r in rows:
            payload = _parse_payload(r.get("payload"))
            rig_name = _str(payload.get("rig_name") or payload.get("rig") or payload.get("rig_name_") or "Unknown", 200) or "Unknown"
            activity = _str(payload.get("activity_type") or payload.get("activity") or payload.get("status") or "Unknown", 200) or "Unknown"
            gcxn.execute(text("INSERT INTO gold.gold_rig_dim_rig (rig_name) VALUES (:n) ON CONFLICT (rig_name) DO NOTHING"), {"n": rig_name})
            gcxn.execute(text("INSERT INTO gold.gold_rig_dim_status (activity_type) VALUES (:n) ON CONFLICT (activity_type) DO NOTHING"), {"n": activity})
        rig_to_sk = {r[0]: r[1] for r in gcxn.execute(text("SELECT rig_name, rig_sk FROM gold.gold_rig_dim_rig")).fetchall()}
        status_to_sk = {r[0]: r[1] for r in gcxn.execute(text("SELECT activity_type, status_sk FROM gold.gold_rig_dim_status")).fetchall()}
        op_name_to_sk = {r[0]: r[1] for r in gcxn.execute(text("SELECT operator_name, operator_sk FROM gold.gold_rig_dim_operator")).fetchall()}

    inserted = 0
    with gold.begin() as gcxn:
        for r in rows:
            payload = _parse_payload(r.get("payload"))
            rig_name = _str(payload.get("rig_name") or payload.get("rig") or payload.get("rig_name_") or "Unknown", 200) or "Unknown"
            activity = _str(payload.get("activity_type") or payload.get("activity") or payload.get("status") or "Unknown", 200) or "Unknown"
            op_name = op_map.get(r["operator_key"]) or "Unknown"
            rig_sk = rig_to_sk.get(rig_name)
            status_sk = status_to_sk.get(activity)
            op_sk = op_name_to_sk.get(_str(op_name, 200) or "Unknown")
            if rig_sk is None or status_sk is None or op_sk is None:
                continue
            try:
                gcxn.execute(
                    text("""
                        INSERT INTO gold.gold_rig_fact_activity (date_key, operator_sk, rig_sk, status_sk, rig_count)
                        VALUES (:date_key, :operator_sk, :rig_sk, :status_sk, 1)
                    """),
                    {"date_key": r["date_key"], "operator_sk": op_sk, "rig_sk": rig_sk, "status_sk": status_sk},
                )
                inserted += 1
            except Exception:
                pass
    metrics["gold_rig_fact_activity"] = inserted
    return metrics


def _parse_date(val: Any) -> Optional[date]:
    if val is None:
        return None
    if hasattr(val, "date"):
        return val.date() if hasattr(val, "date") else val
    try:
        s = str(val).strip()[:10]
        if len(s) >= 10:
            return date(int(s[:4]), int(s[5:7]), int(s[8:10]))
        if len(s) >= 7:
            return date(int(s[:4]), int(s[5:7]), 1)
    except Exception:
        pass
    return None


def _build_concession_mart(silver, gold) -> Dict[str, int]:
    """
    Concession Mart: gold_concession_dim_concession (register) + gold_concession_fact_snapshot.
    Grain: report_date × concession. Measures: is_active, tenure_days_remaining, area_sqkm, concession_count=1.
    """
    metrics = {}
    with silver.connect() as scxn:
        rows = list(scxn.execute(text("SELECT concession_category, payload FROM silver.fact_concession_status")).mappings().all())
    if not rows:
        return {"gold_concession_fact_snapshot": 0}

    today = date.today()
    report_date_key = today.year * 10000 + today.month * 100 + today.day
    with gold.begin() as gcxn:
        gcxn.execute(
            text("INSERT INTO gold.gold_dim_date (date_key, date_actual, year, month, day) VALUES (:dk, :d, :y, :m, :day) ON CONFLICT (date_key) DO NOTHING"),
            {"dk": report_date_key, "d": today, "y": today.year, "m": today.month, "day": today.day},
        )

    inserted_dim = 0
    inserted_fact = 0
    with gold.begin() as gcxn:
        for r in rows:
            cat_full = _str(r.get("concession_category") or "UNKNOWN", 500) or "UNKNOWN"
            payload = _parse_payload(r.get("payload"))
            concession_no = _str(payload.get("concession_id") or payload.get("concession_id_") or payload.get("concession_no"), 100) or ""
            company_op = _str(payload.get("operator") or payload.get("operator_name") or payload.get("company"), 200)
            contract_type = _str(payload.get("contract_type") or payload.get("contract"), 100)
            geo_location = _str(payload.get("geological_location") or payload.get("terrain") or payload.get("location"), 200)
            derived_from = _str(payload.get("derived_from") or payload.get("excised_from"), 200)
            block_excised = _str(payload.get("block_excised_from") or payload.get("block"), 200)
            grant_d = _parse_date(payload.get("grant_date") or payload.get("grant"))
            exp_d = _parse_date(payload.get("expiration_date") or payload.get("expiration") or payload.get("expiry"))
            area = _decimal(payload.get("area_sqkm") or payload.get("area"))

            try:
                gcxn.execute(
                    text("""
                        INSERT INTO gold.gold_concession_dim_concession
                        (concession_no, concession_category_full, company_operator_name, contract_type,
                         geological_location, derived_from, block_excised_from, grant_date, expiration_date, area_sqkm)
                        VALUES (:concession_no, :cat_full, :company_op, :contract_type, :geo_location, :derived_from, :block_excised, :grant_date, :expiration_date, :area_sqkm)
                        ON CONFLICT (concession_no, concession_category_full) DO NOTHING
                    """),
                    {
                        "concession_no": concession_no,
                        "cat_full": cat_full,
                        "company_op": company_op,
                        "contract_type": contract_type,
                        "geo_location": geo_location,
                        "derived_from": derived_from,
                        "block_excised": block_excised,
                        "grant_date": grant_d,
                        "expiration_date": exp_d,
                        "area_sqkm": area,
                    },
                )
                inserted_dim += 1
            except Exception:
                pass
            res = gcxn.execute(
                text("SELECT concession_sk FROM gold.gold_concession_dim_concession WHERE concession_no = :no AND concession_category_full = :cat"),
                {"no": concession_no, "cat": cat_full},
            ).fetchone()
            concession_sk = res[0] if res else None
            if concession_sk is None:
                continue
            is_active = 1 if (exp_d is None or exp_d >= today) else 0
            tenure_days = (exp_d - today).days if exp_d and exp_d >= today else None
            try:
                gcxn.execute(
                    text("""
                        INSERT INTO gold.gold_concession_fact_snapshot (report_date_key, concession_sk, is_active, tenure_days_remaining, area_sqkm, concession_count)
                        VALUES (:report_date_key, :concession_sk, :is_active, :tenure_days_remaining, :area_sqkm, 1)
                    """),
                    {
                        "report_date_key": report_date_key,
                        "concession_sk": concession_sk,
                        "is_active": is_active,
                        "tenure_days_remaining": tenure_days,
                        "area_sqkm": area,
                    },
                )
                inserted_fact += 1
            except Exception:
                pass

    metrics["gold_concession_dim_concession"] = inserted_dim
    metrics["gold_concession_fact_snapshot"] = inserted_fact
    return metrics


def transform_to_gold(run_id: str, mode: str = "full") -> dict:
    """
    Build dataset-specific Gold marts from Silver only. Mode: oil | gas | rig | concession | full.
    Returns metrics: tables_written, rows_written per table, mode. Fails loudly if mode expected data but nothing written.
    """
    ensure_gold_schema()
    silver = get_silver_engine()
    gold = get_gold_engine()
    marts_to_build = MODE_TO_MARTS.get(mode, MODE_TO_MARTS["full"])
    metrics = {"mode": mode, "tables_written": [], "rows_written": 0}

    _sync_conformed_date(silver, gold)

    for mart in marts_to_build:
        if mart == "oil":
            m = _build_oil_mart(silver, gold)
        elif mart == "gas":
            m = _build_gas_mart(silver, gold)
        elif mart == "rig":
            m = _build_rig_mart(silver, gold)
        elif mart == "concession":
            m = _build_concession_mart(silver, gold)
        else:
            m = {}
        for table, count in m.items():
            metrics[table] = count
            if count > 0:
                metrics["tables_written"] = list(set(metrics.get("tables_written", []) + [table]))
            metrics["rows_written"] = metrics.get("rows_written", 0) + count

    # Fail loudly if we expected data but wrote nothing (unless Silver had no rows for this mode)
    total_written = metrics.get("rows_written", 0)
    if total_written == 0 and mode != "full":
        silver_has_rows = False
        try:
            with silver.connect() as scxn:
                if mode == "oil":
                    silver_has_rows = scxn.execute(text("SELECT 1 FROM silver.fact_oil_production LIMIT 1")).fetchone() is not None
                elif mode == "gas":
                    silver_has_rows = scxn.execute(text("SELECT 1 FROM silver.fact_gas_production LIMIT 1")).fetchone() is not None
                elif mode == "rig":
                    silver_has_rows = scxn.execute(text("SELECT 1 FROM silver.fact_rig_disposition LIMIT 1")).fetchone() is not None
                elif mode == "concession":
                    silver_has_rows = scxn.execute(text("SELECT 1 FROM silver.fact_concession_status LIMIT 1")).fetchone() is not None
        except Exception:
            pass
        if silver_has_rows:
            raise RuntimeError(
                f"Gold warehouse_modeling wrote 0 rows for mode={mode} but Silver has data. Check Gold DDL and transform."
            )

    logger.info(
        "Gold transform done: mode=%s tables_written=%s rows_written=%s",
        mode,
        metrics.get("tables_written", []),
        metrics.get("rows_written", 0),
    )
    return metrics
