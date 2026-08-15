from pydantic import BaseModel, Field
from app.models.crop_recommend import SHAPExplanation


class YieldPredictRequest(BaseModel):
    crop: str = Field(..., description="Crop name (e.g., Rice, Wheat, Maize)")
    state: str = Field(..., description="State name")
    district: str = Field(..., description="District name")
    season: str = Field(..., description="Season (Kharif, Rabi, Summer)")
    area_hectares: float = Field(..., gt=0, description="Area in hectares")
    nitrogen: float | None = Field(None, ge=0, le=200)
    phosphorus: float | None = Field(None, ge=0, le=200)
    potassium: float | None = Field(None, ge=0, le=300)
    temperature: float | None = Field(None, ge=-10, le=55)
    humidity: float | None = Field(None, ge=0, le=100)
    rainfall: float | None = Field(None, ge=0, le=5000)

class YieldBenchmark(BaseModel):
    district_average: float
    state_average: float
    national_average: float

class YieldPredictResponse(BaseModel):
    predicted_yield_tonnes_per_hectare: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    total_production_tonnes: float
    benchmark: YieldBenchmark
    factors_analysis: list[str]
    recommendations: list[str]
    shap_explanation: list[SHAPExplanation] | None = None
    success: bool = True
    message: str = "Yield prediction generated successfully"
