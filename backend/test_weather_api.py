#!/usr/bin/env python3
"""
Test script for Weather API Integration
Run this to test the live weather API implementation
"""

import asyncio
import os

from app.config import settings
from app.services.weather_service import WeatherService


async def test_weather_service():
    """Test the weather service with various location formats"""

    print("🌤️  Testing Weather API Integration")
    print("=" * 50)

    # Check if API key is configured
    if not settings.openweather_api_key or settings.openweather_api_key == "your_openweather_api_key_here":
        print("❌ OpenWeatherMap API key not configured!")
        print("Please set OPENWEATHER_API_KEY in your .env file")
        print("Get a free API key from: https://openweathermap.org/api")
        return

    weather_service = WeatherService()

    # Test locations
    test_locations = [
        "Mumbai",
        "Maharashtra",
        "Delhi",
        "19.0760,72.8777",  # Mumbai coordinates
        "Bangalore, Karnataka"
    ]

    for location in test_locations:
        print(f"\n🌍 Testing location: {location}")
        print("-" * 30)

        try:
            # Test weather intelligence
            weather_data = await weather_service.get_weather_intelligence(location, crop="rice")

            print(f"✅ Location: {weather_data.location}")
            print(f"🌡️  Temperature: {weather_data.current_temperature}°C")
            print(f"💧 Humidity: {weather_data.current_humidity}%")
            print(f"☁️  Conditions: {weather_data.current_conditions}")
            print(f"📊 Forecast days: {len(weather_data.forecast)}")
            print(f"⚠️  Alerts: {len(weather_data.alerts)}")
            print(f"💡 Recommendations: {len(weather_data.recommendations)}")

            if weather_data.agricultural_params:
                print(f"🌱 GDD Today: {weather_data.agricultural_params.gdd_today}")
                print(f"💨 Evapotranspiration: {weather_data.agricultural_params.evapotranspiration} mm/day")
                print(f"🚿 Spray Suitability: {weather_data.agricultural_params.spray_suitability}")

            # Test ML weather data
            ml_data = await weather_service.get_weather_for_ml(location)
            print(f"🤖 ML Data - Temp: {ml_data['temperature']}°C, 7-day Rain: {ml_data['rainfall_7day']}mm")

        except Exception as e:
            print(f"❌ Error testing {location}: {e}")

    # Test cache stats
    print("\n📊 Cache Statistics:")
    print("-" * 20)
    cache_stats = weather_service.get_cache_stats()
    for key, value in cache_stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    # Set up environment
    os.environ.setdefault("OPENWEATHER_API_KEY", "your_api_key_here")

    # Run tests
    asyncio.run(test_weather_service())
