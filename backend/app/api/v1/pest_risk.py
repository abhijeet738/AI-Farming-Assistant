import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.db import crud
from app.db.database import get_db
from app.models.pest_risk import PestRiskRequest, PestRiskResponse
from app.services.pest_service import PestService

router = APIRouter()

def get_pest_service():
    return PestService()


@router.post("/assess", response_model=PestRiskResponse)
@limiter.limit("60/minute")
async def assess_pest_risk(
    request: Request,
    payload: PestRiskRequest,
    pest_service: PestService = Depends(get_pest_service),
    db: Session = Depends(get_db),
):
    """
    Assess pest and disease risk for a crop based on location and growth stage.

    Returns risk scores, 7-day timeline, matching diseases, and preventive measures.
    """
    start = time.time()
    success = True
    result = None
    try:
        result = await pest_service.assess_pest_risk(payload)
        return result
    except Exception as e:
        success = False
        raise HTTPException(status_code=500, detail=f"Error assessing pest risk: {str(e)}")
    finally:
        latency_ms = (time.time() - start) * 1000
        try:
            crud.log_prediction(
                db=db,
                service_type="pest_risk",
                request_data=payload.model_dump(),
                response_data=result.model_dump() if result else {},
                latency_ms=round(latency_ms, 2),
                success=success,
            )
        except Exception:
            pass


@router.get("/crops")
@limiter.limit("120/minute")
async def get_supported_crops(request: Request):
    """Get list of crops supported for pest risk assessment."""
    pest_service = PestService()
    metadata = pest_service.metadata or {}
    return {
        "supported_crops": metadata.get("crop_classes", []),
        "risk_levels": metadata.get("risk_classes", ["Low", "Moderate", "High", "Critical"]),
        "total_diseases": metadata.get("num_diseases", 0),
        "success": True,
    }
