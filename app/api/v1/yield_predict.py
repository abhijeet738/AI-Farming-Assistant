import time
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.models.yield_predict import YieldPredictRequest, YieldPredictResponse
from app.services.yield_service import YieldService
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.db import crud

router = APIRouter()

def get_yield_service():
    return YieldService()


@router.post("/predict", response_model=YieldPredictResponse)
@limiter.limit("60/minute")
async def predict_yield(
    request: Request,
    payload: YieldPredictRequest,
    yield_service: YieldService = Depends(get_yield_service),
    db: Session = Depends(get_db),
):
    """
    Predict crop yield based on location, crop type, and growing conditions.

    Returns yield prediction with confidence intervals and benchmark comparisons.
    """
    start = time.time()
    success = True
    result = None
    try:
        result = await yield_service.predict_yield(payload)
        return result
    except Exception as e:
        success = False
        raise HTTPException(status_code=500, detail=f"Error predicting yield: {str(e)}")
    finally:
        latency_ms = (time.time() - start) * 1000
        try:
            crud.log_prediction(
                db=db,
                service_type="yield_predict",
                request_data=payload.model_dump(),
                response_data=result.model_dump() if result else {},
                latency_ms=round(latency_ms, 2),
                success=success,
            )
        except Exception:
            pass


@router.get("/crops")
@limiter.limit("120/minute")
async def get_supported_crops_for_yield(request: Request):
    """Get list of crops supported for yield prediction."""
    yield_service = YieldService()
    
    crops = []
    if yield_service.encoders and "label_encoder_crop" in yield_service.encoders:
        encoder = yield_service.encoders["label_encoder_crop"]
        if hasattr(encoder, "classes_"):
            crops = list(encoder.classes_)
            
    if not crops:
        # Fallback if model not loaded
        crops = ["Rice", "Wheat", "Maize", "Cotton", "Sugarcane"]
        
    return {
        "supported_crops": crops,
        "total_count": len(crops),
        "success": True,
    }
