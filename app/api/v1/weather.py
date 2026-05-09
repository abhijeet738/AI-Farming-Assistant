from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.weather import WeatherResponse
from app.services.weather_service import WeatherService
from app.dependencies import get_weather_service

router = APIRouter()

@router.get("/{location}", response_model=WeatherResponse)
async def get_weather_intelligence(
    location: str,
    crop: str = Query(None, description="Crop type for specific agricultural advice"),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Get weather intelligence for agricultural planning
    
    Provides current weather, 7-day forecast, agricultural alerts, and recommendations.
    Supports location formats: city names, state names, or coordinates (lat,lon).
    """
    try:
        result = await weather_service.get_weather_intelligence(location, crop)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {str(e)}")

@router.get("/alerts/{location}")
async def get_weather_alerts(
    location: str,
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Get only weather alerts for a location
    """
    try:
        weather_data = await weather_service.get_weather_intelligence(location)
        return {
            "location": location,
            "alerts": weather_data.alerts,
            "alert_count": len(weather_data.alerts),
            "success": True
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather alerts: {str(e)}")

@router.get("/ml/{location}")
async def get_weather_for_ml(
    location: str,
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Get weather data formatted for ML model input
    
    Returns weather parameters optimized for machine learning models
    """
    try:
        ml_weather = await weather_service.get_weather_for_ml(location)
        return {
            "location": location,
            "weather_data": ml_weather,
            "success": True
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ML weather data: {str(e)}")

@router.get("/cache/stats")
async def get_cache_stats(
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Get weather cache statistics
    """
    try:
        stats = weather_service.get_cache_stats()
        return {
            "cache_stats": stats,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cache stats: {str(e)}")

@router.delete("/cache")
async def clear_weather_cache(
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    Clear weather cache
    """
    try:
        result = await weather_service.clear_cache()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")
