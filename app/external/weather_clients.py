import asyncio
from datetime import datetime
from typing import Any

import httpx

from app.core.logging import logger


class OpenWeatherMapClient:
    """OpenWeatherMap API client for weather data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.geo_url = "http://api.openweathermap.org/geo/1.0"
        self.timeout = 10.0

    async def get_coordinates(self, location: str) -> tuple[float, float]:
        """Convert location name to coordinates"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.geo_url}/direct",
                    params={
                        "q": location,
                        "limit": 1,
                        "appid": self.api_key
                    }
                )
                response.raise_for_status()
                data = response.json()

                if not data:
                    raise ValueError(f"Location '{location}' not found")

                lat, lon = data[0]["lat"], data[0]["lon"]
                logger.info(f"Resolved location '{location}' to coordinates: {lat}, {lon}")
                return lat, lon

        except httpx.TimeoutException:
            logger.error(f"Timeout while resolving location: {location}")
            raise ValueError(f"Timeout while resolving location: {location}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while resolving location {location}: {e}")
            raise ValueError(f"Error resolving location: {location}")
        except Exception as e:
            logger.error(f"Unexpected error resolving location {location}: {e}")
            raise

    async def get_current_weather(self, lat: float, lon: float) -> dict[str, Any]:
        """Get current weather data"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.api_key,
                        "units": "metric"
                    }
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Fetched current weather for coordinates: {lat}, {lon}")
                return data

        except httpx.TimeoutException:
            logger.error(f"Timeout while fetching current weather for {lat}, {lon}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while fetching current weather: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching current weather: {e}")
            raise

    async def get_forecast(self, lat: float, lon: float, days: int = 7) -> dict[str, Any]:
        """Get weather forecast"""
        try:
            # OpenWeatherMap 5-day forecast with 3-hour intervals
            cnt = min(days * 8, 40)  # 8 forecasts per day, max 40 (5 days)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.api_key,
                        "units": "metric",
                        "cnt": cnt
                    }
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Fetched {days}-day forecast for coordinates: {lat}, {lon}")
                return data

        except httpx.TimeoutException:
            logger.error(f"Timeout while fetching forecast for {lat}, {lon}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while fetching forecast: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching forecast: {e}")
            raise

    async def get_weather_intelligence(self, location: str) -> dict[str, Any]:
        """Get comprehensive weather data for a location"""
        try:
            # Get coordinates
            lat, lon = await self.get_coordinates(location)

            # Fetch current weather and forecast in parallel
            current_task = self.get_current_weather(lat, lon)
            forecast_task = self.get_forecast(lat, lon)

            current_weather, forecast_data = await asyncio.gather(
                current_task, forecast_task
            )

            return {
                "location": location,
                "coordinates": {"lat": lat, "lon": lon},
                "current": current_weather,
                "forecast": forecast_data,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching weather intelligence for {location}: {e}")
            raise

class IMDClient:
    """India Meteorological Department API client (placeholder for future implementation)"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.base_url = "https://api.imd.gov.in"

    async def get_weather_data(self, location: str) -> dict[str, Any]:
        """Get weather data from IMD (to be implemented)"""
        # Placeholder for future IMD API integration
        logger.info("IMD API integration not yet implemented")
        return {}

class VisualCrossingClient:
    """Visual Crossing Weather API client (placeholder for future implementation)"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

    async def get_agricultural_data(self, location: str) -> dict[str, Any]:
        """Get agricultural weather data (to be implemented)"""
        # Placeholder for future Visual Crossing integration
        logger.info("Visual Crossing API integration not yet implemented")
        return {}
