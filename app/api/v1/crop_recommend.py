import time
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.models.crop_recommend import CropRecommendRequest, CropRecommendResponse
from app.services.crop_service import CropService
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.db import crud

router = APIRouter()

def get_crop_service():
    return CropService()


@router.post("/recommend", response_model=CropRecommendResponse)
@limiter.limit("120/minute")
async def recommend_crops(
    request: Request,
    payload: CropRecommendRequest,
    crop_service: CropService = Depends(get_crop_service),
    db: Session = Depends(get_db),
):
    """
    Recommend crops based on soil and climate conditions.

    Returns top 5 crop recommendations with confidence scores and SHAP explanations.
    """
    start = time.time()
    success = True
    result = None
    try:
        result = await crop_service.recommend_crops(payload)
        return result
    except Exception as e:
        success = False
        raise HTTPException(status_code=500, detail=f"Error generating crop recommendations: {str(e)}")
    finally:
        latency_ms = (time.time() - start) * 1000
        try:
            crud.log_prediction(
                db=db,
                service_type="crop_recommend",
                request_data=payload.model_dump(),
                response_data=result.model_dump() if result else {},
                latency_ms=round(latency_ms, 2),
                success=success,
            )
        except Exception:
            pass  # Never let logging break the user response


@router.get("/list")
@limiter.limit("120/minute")
async def list_supported_crops(request: Request):
    """Get list of supported crops for recommendation."""
    crop_service = CropService()
    return {
        "crops": crop_service.crops,
        "total_count": len(crop_service.crops),
        "success": True,
    }
