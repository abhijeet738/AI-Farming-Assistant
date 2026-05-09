import time
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.models.market_price import MarketPriceResponse
from app.services.market_service import MarketService
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.db import crud

router = APIRouter()

def get_market_service():
    return MarketService()


@router.get("/{crop}", response_model=MarketPriceResponse)
@limiter.limit("120/minute")
async def get_market_price(
    request: Request,
    crop: str,
    state: str = Query(None, description="State name for regional prices"),
    market_service: MarketService = Depends(get_market_service),
    db: Session = Depends(get_db),
):
    """Get current market prices and forecasts for a crop."""
    start = time.time()
    success = True
    result = None
    try:
        result = await market_service.get_market_price(crop, state)
        return result
    except Exception as e:
        success = False
        raise HTTPException(status_code=500, detail=f"Error fetching market prices: {str(e)}")
    finally:
        latency_ms = (time.time() - start) * 1000
        try:
            crud.log_prediction(
                db=db,
                service_type="market_price",
                request_data={"crop": crop, "state": state},
                response_data=result.model_dump() if result else {},
                latency_ms=round(latency_ms, 2),
                success=success,
            )
        except Exception:
            pass


@router.get("/")
@limiter.limit("120/minute")
async def get_supported_crops(request: Request):
    """Get list of crops with market price data."""
    market_service = MarketService()
    
    crops = []
    if market_service.encoders and "label_encoder_crop" in market_service.encoders:
        encoder = market_service.encoders["label_encoder_crop"]
        if hasattr(encoder, "classes_"):
            crops = list(encoder.classes_)
            
    if not crops:
        crops = ["Rice", "Wheat", "Maize", "Cotton"]
        
    return {
        "supported_crops": crops,
        "total_count": len(crops),
        "success": True,
    }