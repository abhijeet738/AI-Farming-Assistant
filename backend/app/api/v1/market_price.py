import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.db import crud
from app.db.database import get_db
from app.models.market_price import MarketPriceResponse
from app.services.market_service import MarketService

router = APIRouter()

def get_market_service():
    return MarketService()


@router.get("/dashboard")
@limiter.limit("30/minute")
async def get_market_dashboard(
    request: Request,
    state: str = Query("Maharashtra", description="State name for regional prices"),
    crops: str = Query(None, description="Comma separated list of crops to fetch"),
    market_service: MarketService = Depends(get_market_service),
):
    """Get market dashboard data for requested crops."""
    import asyncio
    
    if crops:
        crop_list = [c.strip() for c in crops.split(",") if c.strip()]
    else:
        # Default crops if none provided
        crop_list = ["Wheat", "Tomato", "Maize", "Onion", "Soybean", "Rice"]
    
    # We use asyncio.gather to fetch all crops concurrently
    tasks = [market_service.get_market_price(crop, state) for crop in crop_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_results = []
    for result in results:
        if isinstance(result, MarketPriceResponse):
            valid_results.append(result)
            
    return {
        "success": True,
        "crops_data": valid_results
    }


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
    # Since we have live web search (Tavily), we can support almost any crop.
    # We provide a comprehensive list of common Indian crops for the UI.
    comprehensive_crops = [
        "Apple", "Arhar (Tur)", "Bajra", "Banana", "Barley", "Basmati Rice", 
        "Black Gram", "Cabbage", "Capsicum", "Cardamom", "Carrot", "Castor Seed", 
        "Cauliflower", "Chana", "Chili", "Coriander", "Cotton", "Cumin", 
        "Garlic", "Ginger", "Gram", "Green Gram", "Groundnut", "Guava", 
        "Jaggery", "Jowar", "Jute", "Lemon", "Lentil (Masur)", "Maize", 
        "Mango", "Mustard", "Onion", "Orange", "Paddy", "Papaya", 
        "Peas", "Pomegranate", "Potato", "Ragi", "Red Gram", "Rice", 
        "Sesame", "Soybean", "Sugarcane", "Sunflower", "Tomato", "Turmeric", "Wheat"
    ]

    return {
        "supported_crops": sorted(comprehensive_crops),
        "total_count": len(comprehensive_crops),
        "success": True,
    }
