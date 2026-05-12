import math
from datetime import datetime
from typing import Any

from app.core.logging import logger
from app.models.weather import AgriculturalParams, WeatherForecast


class WeatherDataProcessor:
    """Process raw weather API data into agricultural intelligence"""

    @staticmethod
    def process_current_weather(raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform OpenWeatherMap current weather to our format"""
        try:
            main = raw_data["main"]
            weather = raw_data["weather"][0]
            wind = raw_data.get("wind", {})

            processed = {
                "temperature": round(main["temp"], 1),
                "humidity": main["humidity"],
                "pressure": main["pressure"],
                "feels_like": round(main["feels_like"], 1),
                "temp_min": round(main["temp_min"], 1),
                "temp_max": round(main["temp_max"], 1),
                "conditions": weather["main"],
                "description": weather["description"],
                "wind_speed": round(wind.get("speed", 0) * 3.6, 1),  # Convert m/s to km/h
                "wind_direction": wind.get("deg", 0),
                "visibility": round(raw_data.get("visibility", 10000) / 1000, 1),  # Convert to km
                "uv_index": raw_data.get("uvi", 0),
                "timestamp": datetime.fromtimestamp(raw_data["dt"]),
                "sunrise": datetime.fromtimestamp(raw_data["sys"]["sunrise"]),
                "sunset": datetime.fromtimestamp(raw_data["sys"]["sunset"])
            }

            logger.info(f"Processed current weather: {processed['temperature']}°C, {processed['humidity']}% humidity")
            return processed

        except KeyError as e:
            logger.error(f"Missing key in weather data: {e}")
            raise ValueError(f"Invalid weather data format: missing {e}")
        except Exception as e:
            logger.error(f"Error processing current weather data: {e}")
            raise

    @staticmethod
    def process_forecast(raw_data: dict[str, Any]) -> list[WeatherForecast]:
        """Transform forecast data to our format"""
        try:
            forecasts = []

            # Group by date (OpenWeatherMap gives 3-hour intervals)
            daily_data = {}

            for item in raw_data["list"]:
                date = datetime.fromtimestamp(item["dt"]).date()

                if date not in daily_data:
                    daily_data[date] = {
                        "temps": [],
                        "humidity": [],
                        "rainfall": 0,
                        "wind_speeds": [],
                        "conditions": [],
                        "pressure": []
                    }

                daily_data[date]["temps"].append(item["main"]["temp"])
                daily_data[date]["humidity"].append(item["main"]["humidity"])
                daily_data[date]["wind_speeds"].append(item["wind"].get("speed", 0) * 3.6)
                daily_data[date]["conditions"].append(item["weather"][0]["main"])
                daily_data[date]["pressure"].append(item["main"]["pressure"])

                # Accumulate rainfall (3-hour precipitation)
                rain = item.get("rain", {}).get("3h", 0)
                snow = item.get("snow", {}).get("3h", 0)
                daily_data[date]["rainfall"] += (rain + snow)

            # Convert to daily forecasts
            for date, data in daily_data.items():
                if not data["temps"]:  # Skip if no data
                    continue

                # Determine most common condition
                most_common_condition = max(set(data["conditions"]), key=data["conditions"].count)

                forecast = WeatherForecast(
                    date=date.strftime("%Y-%m-%d"),
                    temp_max=round(max(data["temps"]), 1),
                    temp_min=round(min(data["temps"]), 1),
                    humidity=round(sum(data["humidity"]) / len(data["humidity"])),
                    rainfall=round(data["rainfall"], 1),
                    wind_speed=round(sum(data["wind_speeds"]) / len(data["wind_speeds"]), 1),
                    conditions=most_common_condition
                )
                forecasts.append(forecast)

            # Sort by date and limit to 7 days
            forecasts.sort(key=lambda x: x.date)
            result = forecasts[:7]

            logger.info(f"Processed {len(result)} days of forecast data")
            return result

        except KeyError as e:
            logger.error(f"Missing key in forecast data: {e}")
            raise ValueError(f"Invalid forecast data format: missing {e}")
        except Exception as e:
            logger.error(f"Error processing forecast data: {e}")
            raise

    @staticmethod
    def calculate_agricultural_params(current: dict[str, Any], forecast: list[WeatherForecast]) -> AgriculturalParams:
        """Calculate agricultural parameters from weather data"""
        try:
            # Growing Degree Days (base temperature 10°C for general crops)
            avg_temp = (current["temp_max"] + current["temp_min"]) / 2
            gdd_today = max(0, avg_temp - 10)

            # Evapotranspiration (simplified Hargreaves method)
            temp_range = current["temp_max"] - current["temp_min"]
            if temp_range > 0:
                # Simplified ET calculation (mm/day)
                et = 0.0023 * (avg_temp + 17.8) * math.sqrt(temp_range) * 2.45
            else:
                et = 3.0  # Default value

            # Delta T (wet bulb depression) - approximation
            # More accurate calculation would require wet bulb temperature
            delta_t = current["temperature"] - (current["temperature"] -
                      (100 - current["humidity"]) / 5)  # Simplified calculation

            # Spray suitability assessment
            spray_suitable = (
                2 <= abs(delta_t) <= 8 and
                current["wind_speed"] < 15 and
                current["humidity"] < 85 and
                current["conditions"] not in ["Rain", "Thunderstorm", "Drizzle"]
            )

            # Soil temperature estimation (typically 2-5°C lower than air temp)
            soil_temp = current["temperature"] - 3

            # Soil moisture estimation (very rough approximation based on recent rainfall)
            recent_rainfall = sum(f.rainfall for f in forecast[:3])  # Last 3 days
            if recent_rainfall > 50:
                soil_moisture = 60  # High
            elif recent_rainfall > 20:
                soil_moisture = 40  # Medium
            else:
                soil_moisture = 25  # Low

            params = AgriculturalParams(
                gdd_today=round(gdd_today, 1),
                gdd_cumulative=None,  # Would need historical data
                evapotranspiration=round(et, 1),
                soil_temperature_0_10cm=round(soil_temp, 1),
                soil_moisture_0_10cm=round(soil_moisture, 1),
                delta_t=round(abs(delta_t), 1),
                spray_suitability="optimal" if spray_suitable else "poor"
            )

            logger.info(f"Calculated agricultural params: GDD={params.gdd_today}, ET={params.evapotranspiration}, Spray={params.spray_suitability}")
            return params

        except Exception as e:
            logger.error(f"Error calculating agricultural parameters: {e}")
            # Return default values on error
            return AgriculturalParams(
                gdd_today=15.0,
                evapotranspiration=5.0,
                soil_temperature_0_10cm=current.get("temperature", 25) - 3,
                soil_moisture_0_10cm=35.0,
                delta_t=5.0,
                spray_suitability="poor"
            )

    @staticmethod
    def calculate_heat_index(temperature: float, humidity: float) -> float:
        """Calculate heat index for heat stress assessment"""
        try:
            if temperature < 27:  # Heat index only relevant for high temperatures
                return temperature

            # Simplified heat index calculation
            T = temperature
            H = humidity

            heat_index = (
                -8.78469475556 +
                1.61139411 * T +
                2.33854883889 * H +
                -0.14611605 * T * H +
                -0.012308094 * T * T +
                -0.0164248277778 * H * H +
                0.002211732 * T * T * H +
                0.00072546 * T * H * H +
                -0.000003582 * T * T * H * H
            )

            return round(heat_index, 1)

        except Exception as e:
            logger.error(f"Error calculating heat index: {e}")
            return temperature

    @staticmethod
    def assess_crop_stress_risk(current: dict[str, Any], forecast: list[WeatherForecast], crop: str = None) -> dict[str, Any]:
        """Assess crop stress risk based on weather conditions"""
        try:
            risks = {
                "heat_stress": "low",
                "cold_stress": "low",
                "water_stress": "low",
                "wind_damage": "low",
                "disease_risk": "low"
            }

            # Heat stress assessment
            if current["temperature"] > 35:
                risks["heat_stress"] = "high"
            elif current["temperature"] > 30:
                risks["heat_stress"] = "medium"

            # Cold stress assessment
            if current["temp_min"] < 5:
                risks["cold_stress"] = "high"
            elif current["temp_min"] < 10:
                risks["cold_stress"] = "medium"

            # Water stress (drought conditions)
            recent_rainfall = sum(f.rainfall for f in forecast[:7])
            if recent_rainfall < 10:
                risks["water_stress"] = "high"
            elif recent_rainfall < 25:
                risks["water_stress"] = "medium"

            # Wind damage risk
            if current["wind_speed"] > 40:
                risks["wind_damage"] = "high"
            elif current["wind_speed"] > 25:
                risks["wind_damage"] = "medium"

            # Disease risk (high humidity + moderate temperature)
            if current["humidity"] > 85 and 20 <= current["temperature"] <= 30:
                risks["disease_risk"] = "high"
            elif current["humidity"] > 70 and 15 <= current["temperature"] <= 35:
                risks["disease_risk"] = "medium"

            return risks

        except Exception as e:
            logger.error(f"Error assessing crop stress risk: {e}")
            return {
                "heat_stress": "low",
                "cold_stress": "low",
                "water_stress": "low",
                "wind_damage": "low",
                "disease_risk": "low"
            }
