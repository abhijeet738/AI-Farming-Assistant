import asyncio
from datetime import datetime, timedelta
from typing import Any

from app.config import settings
from app.core.logging import logger
from app.external.weather_clients import IMDClient, OpenWeatherMapClient, VisualCrossingClient
from app.models.weather import (
    AgriculturalParams,
    WeatherAlert,
    WeatherForecast,
    WeatherRecommendation,
    WeatherResponse,
)
from app.services.weather_cache import WeatherCache
from app.services.weather_processor import WeatherDataProcessor
from app.utils.location_resolver import LocationResolver


class WeatherService:
    """Enhanced weather service with live API integration"""

    def __init__(self):
        # Initialize API clients
        if not settings.openweather_api_key:
            logger.warning("OpenWeatherMap API key not configured - using fallback data")
            self.openweather_client = None
        else:
            self.openweather_client = OpenWeatherMapClient(settings.openweather_api_key)

        self.imd_client = IMDClient(settings.imd_api_key) if settings.imd_api_key else None
        self.visual_crossing_client = VisualCrossingClient(settings.visual_crossing_api_key) if settings.visual_crossing_api_key else None

        # Initialize processors and cache
        self.processor = WeatherDataProcessor()
        self.cache = WeatherCache(ttl_hours=settings.weather_cache_ttl_hours) if settings.enable_weather_caching else None
        self.location_resolver = LocationResolver()

        logger.info("WeatherService initialized with live API integration")

    async def get_weather_intelligence(self, location: str, crop: str = None) -> WeatherResponse:
        """
        Get comprehensive weather intelligence for agricultural planning
        """
        try:
            # Normalize location
            normalized_location = self.location_resolver.normalize_location(location)
            logger.info(f"Processing weather request for: {location} -> {normalized_location}")

            # Check if location is coordinates
            coords = self.location_resolver.extract_coordinates(location)
            if coords:
                lat, lon = coords
                location_name = f"Location ({lat:.2f}, {lon:.2f})"
                logger.info(f"Using provided coordinates: {lat}, {lon}")
            else:
                location_name = normalized_location

                # Check cache first (only for named locations)
                if self.cache and settings.enable_weather_caching:
                    # We need coordinates for cache, so get them first
                    try:
                        lat, lon = await self._get_coordinates(normalized_location)
                        cached_data = self.cache.get(normalized_location, lat, lon)
                        if cached_data:
                            logger.info(f"Returning cached weather data for {normalized_location}")
                            return self._build_response_from_cache(cached_data, location_name, crop)
                    except Exception as e:
                        logger.warning(f"Error checking cache: {e}")
                        # Continue with fresh API call

                # Get coordinates for API call
                lat, lon = await self._get_coordinates(normalized_location)

            # Fetch fresh weather data
            weather_data = await self._fetch_weather_data(location_name, lat, lon)

            # Process the data
            current_weather = self.processor.process_current_weather(weather_data["current"])
            forecast = self.processor.process_forecast(weather_data["forecast"])
            agricultural_params = self.processor.calculate_agricultural_params(current_weather, forecast)

            # Generate alerts and recommendations
            alerts = self._generate_alerts(current_weather, forecast, crop)
            recommendations = self._generate_recommendations(current_weather, forecast, agricultural_params, crop)

            # Cache the processed data (only for named locations, not coordinates)
            if self.cache and settings.enable_weather_caching and not coords:
                processed_data = {
                    "current_weather": current_weather,
                    "forecast": [f.dict() for f in forecast],
                    "agricultural_params": agricultural_params.dict(),
                    "alerts": [a.dict() for a in alerts],
                    "recommendations": [r.dict() for r in recommendations]
                }
                self.cache.set(normalized_location, lat, lon, processed_data)

            response = WeatherResponse(
                location=location_name,
                current_temperature=current_weather["temperature"],
                current_humidity=current_weather["humidity"],
                current_conditions=current_weather["conditions"],
                forecast=forecast,
                alerts=alerts,
                agricultural_params=agricultural_params,
                recommendations=recommendations
            )

            logger.info(f"Successfully generated weather intelligence for {location_name}")
            return response

        except Exception as e:
            logger.error(f"Error fetching weather intelligence for {location}: {e}")
            # Fallback to mock data in case of API failure
            return await self._fallback_weather_response(location, crop)

    async def _get_coordinates(self, location: str) -> tuple[float, float]:
        """Get coordinates for a location"""
        if not self.openweather_client:
            raise ValueError("OpenWeatherMap API not configured")

        return await self.openweather_client.get_coordinates(location)

    async def _fetch_weather_data(self, location: str, lat: float, lon: float) -> dict[str, Any]:
        """Fetch weather data from APIs"""
        if not self.openweather_client:
            raise ValueError("OpenWeatherMap API not configured")

        # For now, use OpenWeatherMap as primary source
        # Future: implement multi-source data fusion
        try:
            # Fetch current weather and forecast in parallel
            current_task = self.openweather_client.get_current_weather(lat, lon)
            forecast_task = self.openweather_client.get_forecast(lat, lon)

            current_weather, forecast_data = await asyncio.gather(current_task, forecast_task)

            return {
                "location": location,
                "coordinates": {"lat": lat, "lon": lon},
                "current": current_weather,
                "forecast": forecast_data,
                "timestamp": datetime.now().isoformat(),
                "source": "openweathermap"
            }

        except Exception as e:
            logger.error(f"Error fetching weather data from OpenWeatherMap: {e}")
            raise

    def _generate_alerts(self, current: dict, forecast: list[WeatherForecast], crop: str | None) -> list[WeatherAlert]:
        """Generate weather alerts based on conditions"""
        alerts = []

        try:
            # Heat wave alert
            if current["temperature"] > 35:
                hot_days = sum(1 for f in forecast[:5] if f.temp_max > 35)
                if hot_days >= 3:
                    alerts.append(WeatherAlert(
                        type="heat_wave",
                        severity="high",
                        message=f"Heat wave: {hot_days} days above 35°C expected",
                        valid_from=datetime.now(),
                        valid_until=datetime.now() + timedelta(days=5),
                        crop_impact="High stress for crops, increase irrigation frequency"
                    ))

            # Frost warning
            frost_days = [f for f in forecast[:3] if f.temp_min < 2]
            if frost_days:
                alerts.append(WeatherAlert(
                    type="frost_warning",
                    severity="critical",
                    message=f"Frost warning: Temperature may drop to {min(f.temp_min for f in frost_days):.1f}°C",
                    valid_from=datetime.now(),
                    valid_until=datetime.now() + timedelta(days=3),
                    crop_impact="Risk of crop damage, protect sensitive plants"
                ))

            # Heavy rain alert
            heavy_rain_days = [f for f in forecast[:3] if f.rainfall > 50]
            if heavy_rain_days:
                total_rain = sum(f.rainfall for f in heavy_rain_days)
                alerts.append(WeatherAlert(
                    type="heavy_rain",
                    severity="medium",
                    message=f"Heavy rainfall expected: {total_rain:.1f}mm in next 3 days",
                    valid_from=datetime.now(),
                    valid_until=datetime.now() + timedelta(days=3),
                    crop_impact="Risk of waterlogging, ensure proper drainage"
                ))

            # Drought indicator
            recent_rain = sum(f.rainfall for f in forecast[:7])
            if recent_rain < 10:
                alerts.append(WeatherAlert(
                    type="drought",
                    severity="medium",
                    message="Low rainfall expected: Less than 10mm in next 7 days",
                    valid_from=datetime.now(),
                    valid_until=datetime.now() + timedelta(days=7),
                    crop_impact="Water stress likely, plan irrigation"
                ))

            # High humidity disease risk
            if current["humidity"] > 85 and 20 <= current["temperature"] <= 30:
                alerts.append(WeatherAlert(
                    type="disease_risk",
                    severity="medium",
                    message=f"High disease risk: {current['humidity']}% humidity at {current['temperature']}°C",
                    valid_from=datetime.now(),
                    valid_until=datetime.now() + timedelta(days=2),
                    crop_impact="Fungal disease risk high, monitor crops closely"
                ))

            # Wind damage warning
            if current["wind_speed"] > 40:
                alerts.append(WeatherAlert(
                    type="wind_warning",
                    severity="high",
                    message=f"Strong winds: {current['wind_speed']:.1f} km/h",
                    valid_from=datetime.now(),
                    valid_until=datetime.now() + timedelta(hours=12),
                    crop_impact="Risk of lodging and physical damage to crops"
                ))

        except Exception as e:
            logger.error(f"Error generating weather alerts: {e}")

        return alerts

    def _generate_recommendations(self, current: dict, forecast: list[WeatherForecast],
                                 agricultural_params: AgriculturalParams, crop: str | None) -> list[WeatherRecommendation]:
        """Generate actionable recommendations"""
        recommendations = []

        try:
            # Irrigation recommendations
            if current["temperature"] > 30 or (agricultural_params.evapotranspiration and agricultural_params.evapotranspiration > 6):
                recommendations.append(WeatherRecommendation(
                    category="irrigation",
                    priority="high",
                    message="Increase irrigation frequency due to high evapotranspiration",
                    timing="Early morning (5-7 AM) or evening (6-8 PM)"
                ))

            # Spraying recommendations
            if agricultural_params.spray_suitability == "optimal":
                recommendations.append(WeatherRecommendation(
                    category="spraying",
                    priority="medium",
                    message=f"Optimal spraying conditions (ΔT: {agricultural_params.delta_t}°C)",
                    timing="Current conditions favorable for next 6 hours"
                ))
            elif agricultural_params.spray_suitability == "poor":
                reasons = []
                if current["wind_speed"] > 15:
                    reasons.append("high wind")
                if current["humidity"] > 85:
                    reasons.append("high humidity")
                if current["conditions"] in ["Rain", "Thunderstorm"]:
                    reasons.append("precipitation")

                recommendations.append(WeatherRecommendation(
                    category="spraying",
                    priority="low",
                    message=f"Poor spraying conditions due to {', '.join(reasons)}",
                    timing="Wait for better conditions"
                ))

            # Field operations
            dry_days = sum(1 for f in forecast[:5] if f.rainfall < 1)
            if dry_days >= 4:
                recommendations.append(WeatherRecommendation(
                    category="field_operations",
                    priority="medium",
                    message=f"Good weather window for field operations ({dry_days} dry days ahead)",
                    timing="Next 5 days"
                ))

            # Harvesting recommendations
            if dry_days >= 3 and current["humidity"] < 70:
                recommendations.append(WeatherRecommendation(
                    category="harvesting",
                    priority="medium",
                    message="Favorable conditions for harvesting and drying",
                    timing="Next 3-4 days"
                ))

            # Crop-specific recommendations
            if crop:
                crop_recommendations = self._get_crop_specific_recommendations(crop, current, forecast)
                recommendations.extend(crop_recommendations)

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")

        return recommendations

    def _get_crop_specific_recommendations(self, crop: str, current: dict, forecast: list[WeatherForecast]) -> list[WeatherRecommendation]:
        """Generate crop-specific recommendations"""
        recommendations = []
        crop_lower = crop.lower()

        try:
            if crop_lower in ["rice", "paddy"]:
                if current["temperature"] > 35:
                    recommendations.append(WeatherRecommendation(
                        category="crop_care",
                        priority="high",
                        message="Rice heat stress risk - maintain water levels in fields",
                        timing="Immediate"
                    ))

                if current["humidity"] > 90:
                    recommendations.append(WeatherRecommendation(
                        category="crop_care",
                        priority="medium",
                        message="High humidity may increase blast disease risk in rice",
                        timing="Monitor for next 3 days"
                    ))

            elif crop_lower == "wheat":
                if any(f.temp_min < 5 for f in forecast[:3]):
                    recommendations.append(WeatherRecommendation(
                        category="crop_care",
                        priority="high",
                        message="Wheat frost protection needed - consider irrigation",
                        timing="Before temperature drops"
                    ))

                if current["temperature"] > 30 and any("flower" in stage for stage in ["flowering", "grain_filling"]):
                    recommendations.append(WeatherRecommendation(
                        category="crop_care",
                        priority="high",
                        message="High temperature during grain filling may reduce wheat yield",
                        timing="Increase irrigation frequency"
                    ))

            elif crop_lower in ["cotton"]:
                if current["temperature"] > 38:
                    recommendations.append(WeatherRecommendation(
                        category="crop_care",
                        priority="high",
                        message="Extreme heat may cause cotton boll shedding",
                        timing="Provide adequate irrigation"
                    ))

            elif crop_lower in ["tomato", "potato", "vegetables"]:
                if current["humidity"] > 80 and 20 <= current["temperature"] <= 30:
                    recommendations.append(WeatherRecommendation(
                        category="crop_care",
                        priority="medium",
                        message="High humidity increases late blight risk in vegetables",
                        timing="Consider preventive fungicide spray"
                    ))

        except Exception as e:
            logger.error(f"Error generating crop-specific recommendations: {e}")

        return recommendations

    async def _fallback_weather_response(self, location: str, crop: str | None) -> WeatherResponse:
        """Fallback response when API fails"""
        logger.warning(f"Using fallback weather data for {location}")

        # Return reasonable default values for India
        fallback_forecast = [
            WeatherForecast(
                date=(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                temp_max=30 + (i % 3),
                temp_min=20 + (i % 3),
                humidity=65,
                rainfall=0 if i % 3 != 0 else 5.0,
                wind_speed=10,
                conditions="Partly Cloudy" if i % 2 == 0 else "Sunny"
            ) for i in range(7)
        ]

        return WeatherResponse(
            location=location,
            current_temperature=27.0,
            current_humidity=65,
            current_conditions="Partly Cloudy",
            forecast=fallback_forecast,
            alerts=[],
            agricultural_params=AgriculturalParams(
                gdd_today=17.0,
                evapotranspiration=5.0,
                soil_temperature_0_10cm=24.0,
                soil_moisture_0_10cm=35.0,
                delta_t=5.0,
                spray_suitability="optimal"
            ),
            recommendations=[
                WeatherRecommendation(
                    category="system",
                    priority="low",
                    message="Weather data unavailable - using default values for India",
                    timing="N/A"
                )
            ]
        )

    def _build_response_from_cache(self, cached_data: dict, location: str, crop: str | None) -> WeatherResponse:
        """Build response from cached data"""
        try:
            return WeatherResponse(
                location=location,
                current_temperature=cached_data["current_weather"]["temperature"],
                current_humidity=cached_data["current_weather"]["humidity"],
                current_conditions=cached_data["current_weather"]["conditions"],
                forecast=[WeatherForecast(**f) for f in cached_data["forecast"]],
                alerts=[WeatherAlert(**a) for a in cached_data["alerts"]],
                agricultural_params=AgriculturalParams(**cached_data["agricultural_params"]),
                recommendations=[WeatherRecommendation(**r) for r in cached_data["recommendations"]]
            )
        except Exception as e:
            logger.error(f"Error building response from cache: {e}")
            # Fall back to fresh API call
            raise ValueError("Invalid cached data format")

    async def get_weather_for_ml(self, location: str) -> dict[str, Any]:
        """Get weather data specifically formatted for ML model input"""
        try:
            weather_data = await self.get_weather_intelligence(location)

            # Extract key parameters for ML models
            ml_weather = {
                "temperature": weather_data.current_temperature,
                "humidity": weather_data.current_humidity,
                "rainfall_7day": sum(f.rainfall for f in weather_data.forecast[:7]),
                "rainfall_today": weather_data.forecast[0].rainfall if weather_data.forecast else 0,
                "wind_speed": weather_data.forecast[0].wind_speed if weather_data.forecast else 10,
                "conditions": weather_data.current_conditions,
                "temp_max_7day": max(f.temp_max for f in weather_data.forecast) if weather_data.forecast else weather_data.current_temperature,
                "temp_min_7day": min(f.temp_min for f in weather_data.forecast) if weather_data.forecast else weather_data.current_temperature,
                "avg_humidity_7day": sum(f.humidity for f in weather_data.forecast) / len(weather_data.forecast) if weather_data.forecast else weather_data.current_humidity
            }

            logger.info(f"Generated ML weather data for {location}: temp={ml_weather['temperature']}°C, humidity={ml_weather['humidity']}%")
            return ml_weather

        except Exception as e:
            logger.error(f"Error getting weather data for ML: {e}")
            # Return fallback values
            return {
                "temperature": 27.0,
                "humidity": 65,
                "rainfall_7day": 25.0,
                "rainfall_today": 0.0,
                "wind_speed": 10.0,
                "conditions": "Partly Cloudy",
                "temp_max_7day": 32.0,
                "temp_min_7day": 22.0,
                "avg_humidity_7day": 65
            }

    def get_cache_stats(self) -> dict[str, Any]:
        """Get weather cache statistics"""
        if not self.cache:
            return {"caching": "disabled"}

        return self.cache.get_stats()

    async def clear_cache(self) -> dict[str, Any]:
        """Clear weather cache"""
        if not self.cache:
            return {"message": "Caching not enabled"}

        self.cache.clear_all()
        return {"message": "Weather cache cleared successfully"}
