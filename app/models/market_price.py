from datetime import datetime

from pydantic import BaseModel, Field


class MarketPriceRequest(BaseModel):
    crop: str = Field(..., description="Crop name")
    state: str | None = Field(None, description="State name for regional prices")
    district: str | None = Field(None, description="District name for local prices")

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
    data_source: str = "estimated"
    source_url: str = ""
    forecast_label: str = ""
    suggestions: list[str] = Field(default_factory=list)
    forecast_7_days: list[PriceForecast]
    forecast_30_days: list[PriceForecast]
    forecast_90_days: list[PriceForecast]
    market_trend: MarketTrend
    best_sell_window: BestSellWindow | None = None
    price_alerts: list[str]
    success: bool = True
    message: str = "Market price data retrieved successfully"
