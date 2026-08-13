
from pydantic import BaseModel


class DiseasePrediction(BaseModel):
    disease_name: str
    confidence: float
    is_healthy: bool
    symptoms: list[str] = []
    treatment_recommendations: list[str] = []

class DiseaseDetectResponse(BaseModel):
    crop: str
    predictions: list[DiseasePrediction]
    is_plant: bool = True
    overall_health_score: float
    analysis_time_ms: float
    success: bool = True
    message: str = "Analysis complete"
