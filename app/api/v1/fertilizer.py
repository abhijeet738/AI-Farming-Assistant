import time
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.models.fertilizer import FertilizerRequest, FertilizerResponse
from app.services.fertilizer_service import FertilizerService
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.db import crud

router = APIRouter()

def get_fertilizer_service():
    return FertilizerService()


@router.post("/recommend", response_model=FertilizerResponse)
@limiter.limit("120/minute")
async def recommend_fertilizer(
    request: Request,
    payload: FertilizerRequest,
    fertilizer_service: FertilizerService = Depends(get_fertilizer_service),
    db: Session = Depends(get_db),
):
    """Get fertilizer recommendations based on soil test data and crop."""
    start = time.time()
    success = True
    result = None
    try:
        result = await fertilizer_service.recommend_fertilizer(payload)
        return result
    except Exception as e:
        success = False
        raise HTTPException(status_code=500, detail=f"Error generating fertilizer recommendations: {str(e)}")
    finally:
        latency_ms = (time.time() - start) * 1000
        try:
            crud.log_prediction(
                db=db,
                service_type="fertilizer",
                request_data=payload.model_dump(),
                response_data=result.model_dump() if result else {},
                latency_ms=round(latency_ms, 2),
                success=success,
            )
        except Exception:
            pass


@router.get("/products")
@limiter.limit("120/minute")
async def get_fertilizer_products(request: Request):
    """Get list of available fertilizer products."""
    fertilizer_service = FertilizerService()
    return {
        "products": fertilizer_service.fertilizer_products,
        "total_count": len(fertilizer_service.fertilizer_products),
        "success": True,
    }