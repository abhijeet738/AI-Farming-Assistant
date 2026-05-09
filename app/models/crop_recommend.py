from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

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
    soil_type: Optional[SoilType] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class CropPrediction(BaseModel):
    crop_name: str
    confidence: float = Field(..., ge=0, le=1)
    suitability_score: float = Field(..., ge=0, le=100)

class SHAPExplanation(BaseModel):
    feature_name: str
    importance: float
    value: float

class CropRecommendResponse(BaseModel):
    predictions: List[CropPrediction]
    shap_explanation: Optional[List[SHAPExplanation]] = None
    recommendations: List[str]
    success: bool = True
    message: str = "Crop recommendation generated successfully"
