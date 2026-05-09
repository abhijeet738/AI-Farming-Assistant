from pydantic import BaseModel, Field
from typing import List, Optional

class FertilizerRequest(BaseModel):
    crop: str = Field(..., description="Crop name")
    nitrogen: float = Field(..., ge=0, le=200, description="Current soil nitrogen (kg/ha)")
    phosphorus: float = Field(..., ge=0, le=200, description="Current soil phosphorus (kg/ha)")
    potassium: float = Field(..., ge=0, le=300, description="Current soil potassium (kg/ha)")
    ph: float = Field(..., ge=0, le=14, description="Soil pH")
    organic_carbon: Optional[float] = Field(None, ge=0, le=10, description="Organic carbon %")
    area_hectares: float = Field(..., gt=0, description="Area in hectares")

class NPKDeficit(BaseModel):
    nitrogen_deficit: float
    phosphorus_deficit: float
    potassium_deficit: float
    deficit_percentage: float

class FertilizerProduct(BaseModel):
    product_name: str
    npk_ratio: str
    quantity_kg_per_hectare: float
    cost_per_kg: float
    total_cost: float
    application_method: str

class ApplicationSchedule(BaseModel):
    stage: str  # basal, top_dressing_1, top_dressing_2
    timing: str
    products: List[str]
    quantity_per_hectare: float

class FertilizerResponse(BaseModel):
    crop: str
    area_hectares: float
    npk_analysis: NPKDeficit
    recommended_products: List[FertilizerProduct]
    application_schedule: List[ApplicationSchedule]
    total_cost_estimate: float
    organic_alternatives: List[str]
    recommendations: List[str]
    success: bool = True
    message: str = "Fertilizer recommendation generated successfully"
