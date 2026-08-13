
from pydantic import BaseModel, Field


class PestRiskRequest(BaseModel):
    crop: str = Field(..., description="Crop name")
    state: str = Field(..., description="State name")
    district: str | None = Field(None, description="District name")
    growth_stage: str = Field(..., description="Current growth stage")
    latitude: float | None = None
    longitude: float | None = None

class PestRiskScore(BaseModel):
    pest_name: str
    risk_level: str  # low, medium, high, critical
    risk_percentage: float
    peak_risk_date: str
    symptoms: list[str]

class PreventiveMeasure(BaseModel):
    measure_type: str  # cultural, biological, chemical
    action: str
    timing: str
    effectiveness: str

class PestRiskTimeline(BaseModel):
    date: str
    overall_risk: str
    high_risk_pests: list[str]

class PestRiskResponse(BaseModel):
    crop: str
    location: str
    growth_stage: str
    assessment_date: str
    pest_risks: list[PestRiskScore]
    risk_timeline_7_days: list[PestRiskTimeline]
    preventive_measures: list[PreventiveMeasure]
    weather_factors: list[str]
    recommendations: list[str]
    success: bool = True
    message: str = "Pest risk assessment completed successfully"
