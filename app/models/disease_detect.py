from pydantic import BaseModel
from typing import List, Optional

class DiseasePrediction(BaseModel):
    disease_name: str
    confidence: float
    is_healthy: bool
    symptoms: List[str] = []
    treatment_recommendations: List[str] = []

class DiseaseDetectResponse(BaseModel):
    crop: str
    predictions: List[DiseasePrediction]
    is_plant: bool = True
    overall_health_score: float
    analysis_time_ms: float
    success: bool = True
    message: str = "Analysis complete"
