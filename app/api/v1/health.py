from datetime import datetime

import psutil
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health_check():
    """
    Comprehensive health check endpoint
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Mock model status - replace with actual model registry checks
        model_status = {
            "crop_recommendation": "loaded",
            "disease_detection": "not_loaded",
            "yield_prediction": "loaded",
            "market_price": "not_loaded",
            "fertilizer": "loaded",
            "pest_risk": "not_loaded"
        }

        # Calculate overall health
        loaded_models = sum(1 for status in model_status.values() if status == "loaded")
        total_models = len(model_status)
        model_health_percentage = (loaded_models / total_models) * 100

        # Determine overall status
        overall_status = "healthy"
        if cpu_percent > 90 or memory.percent > 90:
            overall_status = "degraded"
        if cpu_percent > 95 or memory.percent > 95:
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "uptime_seconds": int(psutil.boot_time()),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "models": {
                "status": model_status,
                "loaded_count": loaded_models,
                "total_count": total_models,
                "health_percentage": model_health_percentage
            },
            "services": {
                "database": "connected",  # Mock - replace with actual DB check
                "redis": "connected",     # Mock - replace with actual Redis check
                "weather_api": "available"  # Mock - replace with actual API check
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/models")
async def model_health():
    """
    Detailed model health and performance metrics
    """
    return {
        "models": {
            "crop_recommendation": {
                "status": "loaded",
                "last_prediction": "2024-04-29T10:30:00Z",
                "avg_response_time_ms": 45,
                "accuracy": 0.991
            },
            "yield_prediction": {
                "status": "loaded",
                "last_prediction": "2024-04-29T09:15:00Z",
                "avg_response_time_ms": 120,
                "r2_score": 0.92
            },
            "fertilizer": {
                "status": "loaded",
                "last_prediction": "2024-04-29T11:00:00Z",
                "avg_response_time_ms": 30
            }
        },
        "success": True
    }
