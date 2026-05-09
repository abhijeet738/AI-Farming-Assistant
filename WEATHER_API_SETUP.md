# Weather API Integration Setup Guide

## 🎯 Overview

This guide helps you set up live weather API integration for the Farming Assistant backend. The system now fetches real weather data instead of using mock/random values.

## 🔑 API Key Setup

### 1. Get OpenWeatherMap API Key (Free)

1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Navigate to "API Keys" section
4. Copy your API key

**Free Tier Limits:**
- 1,000 API calls per day
- 60 calls per minute
- Current weather + 5-day forecast

### 2. Configure Environment Variables

Create or update your `.env` file:

```bash
# Copy from .env.example
cp .env.example .env

# Edit .env file
OPENWEATHER_API_KEY=your_actual_api_key_here
WEATHER_CACHE_TTL_HOURS=1
ENABLE_WEATHER_CACHING=true
```

## 🚀 Installation & Testing

### 1. Install Dependencies

```bash
cd farming-assistant/backend
pip install -r requirements.txt
```

### 2. Test Weather API

```bash
# Test the weather service
python test_weather_api.py
```

Expected output:
```
🌤️  Testing Weather API Integration
==================================================

🌍 Testing location: Mumbai
------------------------------
✅ Location: Mumbai, Maharashtra, India
🌡️  Temperature: 28.5°C
💧 Humidity: 72%
☁️  Conditions: Partly Cloudy
📊 Forecast days: 7
⚠️  Alerts: 1
💡 Recommendations: 3
🌱 GDD Today: 18.5
💨 Evapotranspiration: 5.2 mm/day
🚿 Spray Suitability: optimal
🤖 ML Data - Temp: 28.5°C, 7-day Rain: 15.2mm
```

### 3. Start the Server

```bash
# Start development server
python run.py
```

### 4. Test API Endpoints

```bash
# Test weather intelligence
curl "http://localhost:8000/api/v1/weather/Mumbai"

# Test with crop context
curl "http://localhost:8000/api/v1/weather/Maharashtra?crop=rice"

# Test coordinates
curl "http://localhost:8000/api/v1/weather/19.0760,72.8777"

# Test ML weather data
curl "http://localhost:8000/api/v1/weather/ml/Delhi"

# Check cache stats
curl "http://localhost:8000/api/v1/weather/cache/stats"
```

## 📊 API Endpoints

### Weather Intelligence
```
GET /api/v1/weather/{location}?crop={crop_name}
```

**Supported Location Formats:**
- City names: `Mumbai`, `Delhi`, `Bangalore`
- State names: `Maharashtra`, `Punjab`, `Gujarat`
- Coordinates: `19.0760,72.8777`
- Full addresses: `Mumbai, Maharashtra, India`

**Response includes:**
- Current weather conditions
- 7-day forecast
- Agricultural parameters (GDD, ET, spray conditions)
- Weather alerts (heat wave, frost, heavy rain)
- Crop-specific recommendations

### ML Weather Data
```
GET /api/v1/weather/ml/{location}
```

Returns weather data formatted for ML models:
```json
{
  "temperature": 28.5,
  "humidity": 72,
  "rainfall_7day": 25.3,
  "wind_speed": 12.5,
  "conditions": "Partly Cloudy"
}
```

### Cache Management
```
GET /api/v1/weather/cache/stats    # Get cache statistics
DELETE /api/v1/weather/cache       # Clear cache
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENWEATHER_API_KEY` | Required | OpenWeatherMap API key |
| `WEATHER_CACHE_TTL_HOURS` | 1 | Cache expiry time in hours |
| `ENABLE_WEATHER_CACHING` | true | Enable/disable caching |
| `VISUAL_CROSSING_API_KEY` | Optional | For future enhanced features |
| `WEATHERBIT_API_KEY` | Optional | For future enhanced features |

### Caching Strategy

- **Cache Duration:** 1 hour (configurable)
- **Cache Key:** Based on location + coordinates
- **Cache Size:** Limited to 100 entries (auto-cleanup)
- **Benefits:** Reduces API calls, improves response time

## 🌟 Features

### ✅ Location Intelligence
- Automatic location normalization
- Support for Indian states/cities
- Coordinate parsing
- Location validation

### ✅ Agricultural Parameters
- **Growing Degree Days (GDD)** - Crop development tracking
- **Evapotranspiration (ET)** - Irrigation scheduling
- **Spray Suitability** - Optimal pesticide application timing
- **Soil Temperature** - Seed germination conditions

### ✅ Smart Alerts
- Heat wave warnings (>35°C for 3+ days)
- Frost alerts (<2°C)
- Heavy rain warnings (>50mm)
- Drought indicators (<10mm in 7 days)
- Disease risk (high humidity + moderate temp)

### ✅ Crop-Specific Recommendations
- **Rice:** Heat stress, blast disease risk
- **Wheat:** Frost protection, grain filling conditions
- **Cotton:** Heat stress, boll shedding risk
- **Vegetables:** Late blight risk, humidity management

## 🔄 Integration with ML Models

ML services can now get real weather data:

```python
# In your ML services (pest_service.py, yield_service.py, etc.)
from app.services.weather_service import WeatherService

async def predict_with_real_weather(location: str):
    weather_service = WeatherService()
    weather_data = await weather_service.get_weather_for_ml(location)
    
    # Use real weather data in ML model
    prediction = ml_model.predict([
        weather_data["temperature"],    # Real temperature
        weather_data["humidity"],       # Real humidity  
        weather_data["rainfall_7day"]   # Real rainfall
    ])
    
    return prediction
```

## 🚨 Error Handling

### Fallback Strategy
If API fails, the system automatically falls back to reasonable default values for India:
- Temperature: 27°C
- Humidity: 65%
- Conditions: Partly Cloudy

### Common Issues

1. **API Key Invalid**
   ```
   Error: HTTP 401 - Invalid API key
   Solution: Check your OpenWeatherMap API key
   ```

2. **Location Not Found**
   ```
   Error: Location 'XYZ' not found
   Solution: Use standard city/state names or coordinates
   ```

3. **Rate Limit Exceeded**
   ```
   Error: HTTP 429 - Too many requests
   Solution: Enable caching or upgrade API plan
   ```

## 📈 Monitoring

### Cache Performance
```bash
curl "http://localhost:8000/api/v1/weather/cache/stats"
```

Response:
```json
{
  "cache_size": 15,
  "hits": 45,
  "misses": 12,
  "hit_rate_percent": 78.9,
  "ttl_hours": 1
}
```

### API Usage Tracking
Monitor your OpenWeatherMap usage at: https://home.openweathermap.org/statistics

## 🔮 Future Enhancements

1. **Multi-Source Weather Data**
   - IMD (India Meteorological Department) integration
   - Visual Crossing for agricultural parameters
   - Weatherbit for soil moisture data

2. **Advanced Features**
   - Historical weather analysis
   - Weather-yield correlation
   - Seasonal forecasting
   - Hyperlocal weather (1km resolution)

3. **Performance Optimizations**
   - Redis caching for production
   - Background weather updates
   - Batch location processing

## ✅ Success Criteria

After setup, you should have:

- ✅ Real weather data instead of mock values
- ✅ Location resolution working for Indian cities/states
- ✅ Agricultural parameters calculated from real data
- ✅ Weather alerts generated based on actual conditions
- ✅ ML models receiving real weather inputs
- ✅ Caching reducing API calls
- ✅ Fallback handling API failures gracefully

## 🆘 Support

If you encounter issues:

1. Check the logs for detailed error messages
2. Verify your API key is valid and has quota remaining
3. Test with the provided test script
4. Check the OpenWeatherMap API status page

The weather API integration is now complete and ready for production use!