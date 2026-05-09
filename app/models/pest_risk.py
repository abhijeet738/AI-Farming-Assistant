from pydantic import BaseModel, Field
from typing import List, Optional

class PestRiskRequest(BaseModel):
    crop: str = Field(..., description="Crop name")
    state: str = Field(..., description="State name")
    district: Optional[str] = Field(None, description="District name")
    growth_stage: str = Field(..., description="Current growth stage")
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class PestRiskScore(BaseModel):
    pest_name: str
    risk_level: str  # low, medium, high, critical
    risk_percentage: float
    peak_risk_date: str
    symptoms: List[str]

class PreventiveMeasure(BaseModel):
    measure_type: str  # cultural, biological, chemical
    action: str
    timing: str
    effectiveness: str

class PestRiskTimeline(BaseModel):
    date: str
    overall_risk: str
    high_risk_pests: List[str]

class PestRiskResponse(BaseModel):
    crop: str
    location: str
    growth_stage: str
    assessment_date: str
    pest_risks: List[PestRiskScore]
    risk_timeline_7_days: List[PestRiskTimeline]
    preventive_measures: List[PreventiveMeasure]
    weather_factors: List[str]
    recommendations: List[str]
    success: bool = True
    message: str = "Pest risk assessment completed successfully"
