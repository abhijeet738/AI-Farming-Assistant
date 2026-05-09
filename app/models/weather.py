from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class WeatherAlert(BaseModel):
    type: str
    severity: str  # low, medium, high, critical
    message: str
    valid_from: datetime
    valid_until: datetime
    crop_impact: Optional[str] = None

class WeatherForecast(BaseModel):
    date: str
    temp_max: float
    temp_min: float
    humidity: int
    rainfall: float
    wind_speed: float
    conditions: str

class AgriculturalParams(BaseModel):
    gdd_today: Optional[float] = None
    gdd_cumulative: Optional[float] = None
    evapotranspiration: Optional[float] = None
    soil_temperature_0_10cm: Optional[float] = None
    soil_moisture_0_10cm: Optional[float] = None
    delta_t: Optional[float] = None
    spray_suitability: Optional[str] = None

class WeatherRecommendation(BaseModel):
    category: str  # irrigation, spraying, harvesting, etc.
    priority: str  # low, medium, high
    message: str
    timing: Optional[str] = None

class WeatherResponse(BaseModel):
    location: str
    current_temperature: float
    current_humidity: int
    current_conditions: str
    forecast: List[WeatherForecast]
    alerts: List[WeatherAlert]
    agricultural_params: Optional[AgriculturalParams] = None
    recommendations: List[WeatherRecommendation]
    success: bool = True
    message: str = "Weather data retrieved successfully"