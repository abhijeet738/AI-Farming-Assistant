from datetime import datetime

from pydantic import BaseModel


class WeatherAlert(BaseModel):
    type: str
    severity: str  # low, medium, high, critical
    message: str
    valid_from: datetime
    valid_until: datetime
    crop_impact: str | None = None

class WeatherForecast(BaseModel):
    date: str
    temp_max: float
    temp_min: float
    humidity: int
    rainfall: float
    wind_speed: float
    conditions: str

class AgriculturalParams(BaseModel):
    gdd_today: float | None = None
    gdd_cumulative: float | None = None
    evapotranspiration: float | None = None
    soil_temperature_0_10cm: float | None = None
    soil_moisture_0_10cm: float | None = None
    delta_t: float | None = None
    spray_suitability: str | None = None

class WeatherRecommendation(BaseModel):
    category: str  # irrigation, spraying, harvesting, etc.
    priority: str  # low, medium, high
    message: str
    timing: str | None = None

class WeatherResponse(BaseModel):
    location: str
    current_temperature: float
    current_humidity: int
    current_conditions: str
    forecast: list[WeatherForecast]
    alerts: list[WeatherAlert]
    agricultural_params: AgriculturalParams | None = None
    recommendations: list[WeatherRecommendation]
    success: bool = True
    message: str = "Weather data retrieved successfully"
