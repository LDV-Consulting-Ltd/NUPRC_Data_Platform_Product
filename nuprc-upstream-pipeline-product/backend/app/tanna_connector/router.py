"""PetroCore Tanna Connector v0.2.1 — /api/v1/tanna/* surface."""

import traceback



from fastapi import APIRouter, Depends

from fastapi.responses import JSONResponse



from app.tanna_connector.config import TANNA_API_PREFIX

from app.tanna_connector.envelope import build_envelope

from app.tanna_connector.security import require_connector_token

from app.tanna_connector.services import (

    data_product_service,

    decision_product_service,

    entity_service,

    health_service,

    illumination_service,

    knowledge_asset_service,

    manifest_service,

    pattern_service,

    relationship_service,

    signal_service,

    status_service,

)



router = APIRouter(prefix=TANNA_API_PREFIX, tags=["Tanna Connector"])





def _safe(handler, object_type: str):

    try:

        return handler()

    except Exception as exc:

        return JSONResponse(

            status_code=200,

            content=build_envelope(

                object_type=object_type,

                implementation_status="partial",

                items=[],

                source="petrocore.tanna_connector.router",

                notes=f"Connector endpoint degraded: {exc}",

                warnings=[traceback.format_exc()],

            ),

        )





@router.get("/health")

def get_health(_token: str = Depends(require_connector_token)):

    return _safe(health_service.get_health, "health")





@router.get("/status")

def get_status(_token: str = Depends(require_connector_token)):

    return _safe(status_service.get_status, "status")





@router.get("/manifest")

def get_manifest(_token: str = Depends(require_connector_token)):

    return _safe(manifest_service.get_manifest, "manifest")





@router.get("/data-products")

def get_data_products(_token: str = Depends(require_connector_token)):

    return _safe(data_product_service.get_data_products, "data_products")





@router.get("/entities")

def get_entities(_token: str = Depends(require_connector_token)):

    return _safe(entity_service.get_entities, "entities")





@router.get("/relationships")

def get_relationships(_token: str = Depends(require_connector_token)):

    return _safe(relationship_service.get_relationships, "relationships")





@router.get("/signals")

def get_signals(_token: str = Depends(require_connector_token)):

    return _safe(signal_service.get_signals, "signals")





@router.get("/patterns")

def get_patterns(_token: str = Depends(require_connector_token)):

    return _safe(pattern_service.get_patterns, "patterns")





@router.get("/illuminations")

def get_illuminations(_token: str = Depends(require_connector_token)):

    return _safe(illumination_service.get_illuminations, "illuminations")





@router.get("/decision-products")

def get_decision_products(_token: str = Depends(require_connector_token)):

    return _safe(decision_product_service.get_decision_products, "decision_products")





@router.get("/knowledge-assets")

def get_knowledge_assets(_token: str = Depends(require_connector_token)):

    return _safe(knowledge_asset_service.get_knowledge_assets, "knowledge_assets")

