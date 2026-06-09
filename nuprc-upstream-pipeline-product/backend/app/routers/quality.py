from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/quality", tags=["quality"])


def _rule_status(passed: bool) -> str:
    return "pass" if passed else "fail"


@router.get("/summary")
def summary() -> dict[str, Any]:
    """Live quality summary from v1 bronze source health and gold freshness."""
    warnings: list[str] = []
    datasets: list[dict[str, Any]] = []
    rule_checks: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    try:
        from app.routers.v1_pipeline import get_sources_health, get_gold_freshness
        bronze = get_sources_health()
        gold = get_gold_freshness()
    except Exception as exc:
        return {
            "ok": True,
            "status": "degraded",
            "source": "unavailable",
            "warnings": [str(exc)],
            "kpis": {},
            "rule_checks": [],
            "issues": [],
            "datasets": [],
        }

    bronze_sources = bronze.get("sources") or []
    gold_sources = gold.get("sources") or []
    gold_by_key = {g.get("source_key"): g for g in gold_sources}

    total_bronze_rows = 0
    total_gold_rows = 0
    degraded_count = 0
    down_count = 0
    scores: list[int] = []

    for src in bronze_sources:
        key = src.get("source_key")
        label = src.get("label") or key
        row_count = int(src.get("row_count") or 0)
        score = int(src.get("score") or src.get("freshness_score") or 0)
        total_bronze_rows += row_count
        scores.append(score)

        gold_src = gold_by_key.get(key) or {}
        gold_rows = int(gold_src.get("row_count") or 0)
        gold_score = int(gold_src.get("freshness_score") or 0)
        total_gold_rows += gold_rows
        if gold_score:
            scores.append(gold_score)

        legacy_status = src.get("status") or "unknown"
        if legacy_status == "degraded":
            degraded_count += 1
        if legacy_status == "down":
            down_count += 1

        datasets.append({
            "source_key": key,
            "label": label,
            "bronze_rows": row_count,
            "bronze_score": score,
            "bronze_status": legacy_status,
            "gold_rows": gold_rows,
            "gold_score": gold_score,
            "gold_status": gold_src.get("status"),
            "gold_last_updated": gold_src.get("last_updated"),
            "data_presence_status": src.get("data_presence_status"),
            "explanation": src.get("explanation"),
        })

        has_bronze = row_count > 0
        rule_checks.append({
            "rule_id": f"bronze_presence_{key}",
            "label": f"{label}: bronze rows present",
            "source": label,
            "status": _rule_status(has_bronze),
            "detail": f"{row_count:,} rows in bronze" if has_bronze else "No bronze rows",
        })
        rule_checks.append({
            "rule_id": f"gold_presence_{key}",
            "label": f"{label}: gold mart populated",
            "source": label,
            "status": _rule_status(gold_rows > 0),
            "detail": f"{gold_rows:,} rows in gold" if gold_rows > 0 else "No gold rows",
        })

        if legacy_status == "down":
            issues.append({
                "severity": "critical",
                "source": label,
                "message": src.get("explanation") or f"{label} is unavailable or missing data.",
            })
        elif legacy_status == "degraded":
            issues.append({
                "severity": "advisory",
                "source": label,
                "message": src.get("explanation") or f"{label} has lower freshness score ({score}) but data is present.",
            })

    avg_score = round(sum(scores) / len(scores)) if scores else 0
    kpis = {
        "sources_monitored": len(bronze_sources),
        "sources_with_data": sum(1 for s in bronze_sources if (s.get("row_count") or 0) > 0),
        "sources_degraded": degraded_count,
        "sources_down": down_count,
        "avg_quality_score": avg_score,
        "total_bronze_rows": total_bronze_rows,
        "total_gold_rows": total_gold_rows,
        "rules_passed": sum(1 for r in rule_checks if r.get("status") == "pass"),
        "rules_failed": sum(1 for r in rule_checks if r.get("status") == "fail"),
    }

    return {
        "ok": True,
        "status": "ok" if down_count == 0 else "degraded",
        "source": "v1_pipeline",
        "warnings": warnings,
        "kpis": kpis,
        "rule_checks": rule_checks,
        "issues": issues,
        "datasets": datasets,
    }
