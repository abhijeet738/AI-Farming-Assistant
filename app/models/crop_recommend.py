from enum import Enum

from pydantic import BaseModel, Field


class SoilType(str, Enum):
    BLACK = "Black"
    CLAYEY = "Clayey"
    LOAMY = "Loamy"
    RED = "Red"
    SANDY = "Sandy"

class CropRecommendRequest(BaseModel):
    nitrogen: float = Field(..., ge=0, le=200, description="Nitrogen content (kg/ha)")
    phosphorus: float = Field(..., ge=0, le=200, description="Phosphorus content (kg/ha)")
    potassium: float = Field(..., ge=0, le=300, description="Potassium content (kg/ha)")
    temperature: float = Field(..., ge=-10, le=55, description="Temperature (°C)")
    humidity: float = Field(..., ge=0, le=100, description="Humidity (%)")
    ph: float = Field(..., ge=0, le=14, description="Soil pH")
    rainfall: float = Field(..., ge=0, le=5000, description="Rainfall (mm)")
    soil_type: SoilType | None = None
    latitude: float | None = None
    longitude: float | None = None

class CropPrediction(BaseModel):
    crop_name: str
    confidence: float = Field(..., ge=0, le=1)
    suitability_score: float = Field(..., ge=0, le=100)

class SHAPExplanation(BaseModel):
    feature_name: str
    importance: float
    value: float

class CropRecommendResponse(BaseModel):
    predictions: list[CropPrediction]
    shap_explanation: list[SHAPExplanation] | None = None
    recommendations: list[str]
    success: bool = True
    message: str = "Crop recommendation generated successfully"
