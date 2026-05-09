from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MarketPriceRequest(BaseModel):
    crop: str = Field(..., description="Crop name")
    state: Optional[str] = Field(None, description="State name for regional prices")
    district: Optional[str] = Field(None, description="District name for local prices")

class PriceForecast(BaseModel):
    date: str
    predicted_price: float
    confidence_lower: float
    confidence_upper: float

class MarketTrend(BaseModel):
    trend_direction: str  # rising, falling, stable
    trend_strength: str  # weak, moderate, strong
    percentage_change: float

class BestSellWindow(BaseModel):
    start_date: str
    end_date: str
    expected_price_range: str
    reasoning: str

class MarketPriceResponse(BaseModel):
    crop: str
    location: str
    current_price_per_quintal: float
    currency: str = "INR"
    last_updated: datetime
    forecast_7_days: List[PriceForecast]
    forecast_30_days: List[PriceForecast]
    forecast_90_days: List[PriceForecast]
    market_trend: MarketTrend
    best_sell_window: BestSellWindow
    price_alerts: List[str]
    success: bool = True
    message: str = "Market price data retrieved successfully"
