# backend/app/services/fuzzy_matcher.py
"""
Fuzzy matching service for column name standardization across years.
"""
from typing import Dict, List, Tuple, Optional
from rapidfuzz import fuzz, process
import re


# Canonical column names dictionary
CANONICAL_COLUMNS = {
    # Operator/Company
    'operator': ['operator', 'company', 'operator name', 'company name', 'operating company'],
    'operator_code': ['operator code', 'op code', 'company code'],
    
    # Asset/Field
    'asset_name': ['asset', 'field', 'field name', 'block', 'block name', 'concession'],
    'asset_type': ['asset type', 'type', 'category'],
    
    # Production
    'production_volume': ['production', 'volume', 'quantity', 'output', 'production volume', 'qty'],
    'production_unit': ['unit', 'uom', 'unit of measure'],
    
    # Dates
    'report_date': ['date', 'report date', 'period', 'report period', 'reporting date'],
    'report_month': ['month', 'report month'],
    'report_year': ['year', 'report year'],
    
    # Rig specific
    'rig_name': ['rig', 'rig name', 'rig number'],
    'rig_status': ['status', 'rig status', 'disposition'],
    'activity_type': ['activity', 'activity type', 'type of activity'],
    
    # Concession specific
    'concession_status': ['status', 'concession status', 'license status'],
    'concession_type': ['type', 'concession type', 'license type'],
    
    # Common
    'id': ['id', 'identifier', 'key'],
    'name': ['name', 'title'],
}


def normalize_column_name(column: str) -> str:
    """Normalize a column name: lowercase, strip, remove punctuation."""
    # Convert to lowercase
    normalized = column.lower().strip()
    
    # Remove special characters except spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip()


def find_canonical_match(column: str, threshold: float = 85.0) -> Tuple[Optional[str], float]:
    """
    Find the best matching canonical column name.
    Returns: (canonical_name, similarity_score) or (None, score) if below threshold.
    """
    normalized = normalize_column_name(column)
    
    # Build a flat list of all variations for matching
    all_variations = []
    for canonical, variations in CANONICAL_COLUMNS.items():
        for variation in variations:
            all_variations.append((canonical, variation))
    
    # Use rapidfuzz to find best match
    best_match = process.extractOne(
        normalized,
        [var[1] for var in all_variations],
        scorer=fuzz.token_sort_ratio
    )
    
    if best_match and best_match[1] >= threshold:
        # Find which canonical this variation belongs to
        for canonical, variation in all_variations:
            if variation == best_match[0]:
                return canonical, best_match[1]
    
    return None, best_match[1] if best_match else 0.0


def standardize_columns(columns: List[str], source_id: str) -> Dict[str, str]:
    """
    Standardize a list of column names using fuzzy matching.
    Returns mapping: original_column -> canonical_column
    """
    mapping = {}
    
    for col in columns:
        canonical, score = find_canonical_match(col)
        if canonical:
            mapping[col] = canonical
        else:
            # Keep original if no good match found
            mapping[col] = normalize_column_name(col)
    
    return mapping


def detect_schema_drift(
    columns: List[str],
    source_id: str,
    table_name: str,
    run_id: str
) -> List[Dict[str, Any]]:
    """
    Detect schema drift by comparing columns to canonical names.
    Returns list of drift records to log.
    """
    drift_records = []
    
    for col in columns:
        canonical, score = find_canonical_match(col)
        
        drift_type = None
        if score < 85.0:
            drift_type = "low_similarity"
        elif canonical is None:
            drift_type = "unknown_column"
        
        if drift_type:
            drift_records.append({
                'source_id': source_id,
                'table_name': table_name,
                'column_name': col,
                'canonical_name': canonical,
                'similarity_score': score,
                'drift_type': drift_type
            })
    
    return drift_records


def log_schema_drift(drift_records: List[Dict[str, Any]], run_id: str):
    """Log schema drift records to silver.schema_drift table."""
    from sqlalchemy import text
    from app.core.db import engine
    
    with engine.begin() as cxn:
        for record in drift_records:
            cxn.execute(text("""
                INSERT INTO silver.schema_drift
                (source_id, table_name, column_name, canonical_name, similarity_score, drift_type)
                VALUES (:source_id, :table_name, :column_name, :canonical_name, :similarity_score, :drift_type)
            """), record)
