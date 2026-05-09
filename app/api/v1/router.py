from fastapi import APIRouter
from app.api.v1 import crop_recommend, weather, yield_predict, market_price, fertilizer, health, pest_risk, disease_detect, chat, auth

api_router = APIRouter()

# Auth endpoints (first, so they appear at top of docs)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["🔐 Authentication"]
)

# Include all endpoint routers
api_router.include_router(
    crop_recommend.router, 
    prefix="/crop", 
    tags=["Crop Recommendation"]
)

api_router.include_router(
    weather.router, 
    prefix="/weather", 
    tags=["Weather Intelligence"]
)

api_router.include_router(
    yield_predict.router,
    prefix="/yield",
    tags=["Yield Prediction"]
)

api_router.include_router(
    market_price.router,
    prefix="/market",
    tags=["Market Prices"]
)

api_router.include_router(
    fertilizer.router,
    prefix="/fertilizer", 
    tags=["Fertilizer Recommendations"]
)

api_router.include_router(
    health.router, 
    prefix="/health", 
    tags=["Health Check"]
)

api_router.include_router(
    pest_risk.router,
    prefix="/pest",
    tags=["Pest & Disease Risk"]
)

api_router.include_router(
    disease_detect.router,
    prefix="/disease",
    tags=["Computer Vision Disease Detection"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["🧠 Agentic Chat (LangGraph)"]
)

# Add a summary endpoint
@api_router.get("/", tags=["API Info"])
async def api_info():
    """
    API information and available endpoints
    """
    return {
        "name": "Farming Assistant API",
        "version": "1.0.0",
        "description": "AI-powered agricultural advisory platform",
        "endpoints": {
            "crop_recommendation": "/api/v1/crop/recommend",
            "weather_intelligence": "/api/v1/weather/{location}",
            "yield_prediction": "/api/v1/yield/predict",
            "market_prices": "/api/v1/market/{crop}",
            "fertilizer_recommendation": "/api/v1/fertilizer/recommend",
            "pest_risk_assessment": "/api/v1/pest/assess",
            "health_check": "/api/v1/health/"
        },
        "documentation": "/docs",
        "status": "operational"
    }
