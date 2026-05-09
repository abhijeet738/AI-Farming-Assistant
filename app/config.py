from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "Farming Assistant API"
    version: str = "1.0.0"
    debug: bool = False

    # ── Supabase ────────────────────────────────────────────────────────
    supabase_url: str = Field("", description="Supabase project URL (https://xxx.supabase.co)")
    supabase_key: str = Field("", description="Supabase anon/public API key")
    supabase_service_key: Optional[str] = Field(None, description="Supabase service_role key (server-side)")
    supabase_jwt_secret: Optional[str] = Field(None, description="Supabase JWT secret for local verification")

    # ── Database ────────────────────────────────────────────────────────
    # For Supabase: use the Transaction Pooler connection string
    # For local dev: use sqlite:///./farming_assistant.db
    database_url: str = Field(
        "sqlite:///./farming_assistant.db",
        description="Database connection string"
    )

    # ── External APIs ───────────────────────────────────────────────────
    openweather_api_key: str = Field("", description="OpenWeatherMap API key")
    google_api_key: Optional[str] = Field(None, description="Google Gemini API key for LangGraph agent")
    imd_api_key: Optional[str] = None

    # ── Weather Configuration ───────────────────────────────────────────
    weather_cache_ttl_hours: int = Field(1, description="Weather cache TTL in hours")
    enable_weather_caching: bool = Field(True, description="Enable weather data caching")
    visual_crossing_api_key: Optional[str] = None
    weatherbit_api_key: Optional[str] = None

    # ── Security ────────────────────────────────────────────────────────
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ── ML Models ───────────────────────────────────────────────────────
    models_path: str = "./ml_models"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
