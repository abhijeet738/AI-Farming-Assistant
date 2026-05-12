import time

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.db import crud
from app.db.database import get_db
from app.models.disease_detect import DiseaseDetectResponse
from app.services.disease_service import DiseaseService

router = APIRouter()

# Instantiate service once to keep PyTorch model in memory
_disease_service = DiseaseService()

def get_disease_service():
    return _disease_service


@router.post("/analyze", response_model=DiseaseDetectResponse)
@limiter.limit("60/minute")
async def analyze_plant_disease(
    request: Request,
    file: UploadFile = File(...),
    disease_service: DiseaseService = Depends(get_disease_service),
    db: Session = Depends(get_db),
):
    """
    Upload a leaf image to detect diseases using PyTorch Computer Vision.

    Accepts: jpg, jpeg, png
    Returns: Top 3 predictions, overall health score, and treatment recommendations.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (jpg/png)")

    start = time.time()
    success = True
    result = None
    try:
        image_bytes = await file.read()
        result = await disease_service.detect_disease(image_bytes)
        return result
    except Exception as e:
        success = False
        raise HTTPException(status_code=500, detail=f"Error analyzing image: {str(e)}")
    finally:
        latency_ms = (time.time() - start) * 1000
        try:
            crud.log_prediction(
                db=db,
                service_type="disease_detect",
                request_data={"filename": file.filename, "content_type": file.content_type},
                response_data=result.model_dump() if result else {},
                latency_ms=round(latency_ms, 2),
                success=success,
            )
        except Exception:
            pass
