---
title: AI Farming Assistant Backend
emoji: 🌱
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# 🌱 AI Farming Assistant Backend

An enterprise-grade, ML-powered smart farming API built with FastAPI, LangGraph, and 6 trained machine learning models. This system provides real-time crop recommendations, disease detection, market price forecasting, and a conversational agricultural agent.

## 🚀 Features

- **6 Predictive ML Models**: Crop recommendation, yield prediction, disease detection, fertilizer recommendation, pest risk assessment, and market price forecasting
- **Live Weather Intelligence**: Real-time agricultural weather data from OpenWeatherMap API
- **Conversational AI Agent**: LangGraph-powered assistant with RAG capabilities for Indian farming context
- **Production Ready**: Rate limiting, authentication, comprehensive logging, and error handling
- **Comprehensive Data**: 5 populated knowledge bases with Indian agricultural information

## 🔌 API Endpoints

### Core ML Services
- `POST /api/v1/crop/recommend` - Get crop recommendations based on soil and weather
- `POST /api/v1/yield/predict` - Predict crop yield for planning
- `POST /api/v1/fertilizer/recommend` - Get fertilizer recommendations with NPK analysis
- `POST /api/v1/disease/detect` - Upload leaf images for disease detection
- `POST /api/v1/pest/risk` - Assess pest risk based on weather conditions
- `GET /api/v1/market/{crop}` - Get market price forecasts

### Weather Intelligence
- `GET /api/v1/weather/{location}` - Comprehensive agricultural weather data
- `GET /api/v1/weather/ml/{location}` - ML-formatted weather data for models

### Conversational Agent
- `POST /api/v1/chat/invoke` - Chat with AI agricultural expert
- `GET /api/v1/chat/history` - Retrieve conversation history

### System
- `GET /api/v1/health` - System health and model status
- `GET /ping` - Simple health check

## 🧪 Try It Out

### 1. Crop Recommendation
```bash
curl -X POST "https://abhijeetraj-farming-assistant-backend.hf.space/api/v1/crop/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "nitrogen": 90, "phosphorus": 42, "potassium": 43,
    "temperature": 28.5, "humidity": 78, "ph": 6.5, "rainfall": 45
  }'
```

### 2. Live Weather Data
```bash
curl "https://abhijeetraj-farming-assistant-backend.hf.space/api/v1/weather/Maharashtra?crop=rice"
```

### 3. Chat with AI Agent
```bash
curl -X POST "https://abhijeetraj-farming-assistant-backend.hf.space/api/v1/chat/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should I plant this season in Punjab?",
    "location": "Punjab"
  }'
```

## 📊 Model Performance

- **Crop Recommendation**: 99.1% accuracy (Stacking Ensemble)
- **Disease Detection**: 92%+ accuracy (EfficientNetV2-S)
- **Yield Prediction**: R² 0.94+ (XGBoost/LightGBM)
- **Market Forecasting**: Time-series analysis (Prophet + LSTM)
- **Fertilizer Recommendation**: Rule-based + ML (XGBoost)
- **Pest Risk Assessment**: Dual-model system

## 🌾 Agricultural Knowledge Base

The system includes comprehensive Indian agricultural data:
- **Crop Calendar**: Sowing/harvesting windows for major crops across Indian states
- **Disease Treatments**: Treatment protocols for 6+ major crop diseases
- **Fertilizer Database**: NPK compositions, brands, and application guidelines
- **Government Schemes**: PM-Kisan, PMFBY, and other agricultural subsidies
- **Carbon Factors**: IPCC-based emission factors for sustainable farming

## 🔧 Technical Stack

- **Backend**: FastAPI with async/await
- **ML Models**: XGBoost, LightGBM, PyTorch, Scikit-learn
- **AI Agent**: LangGraph with Google Gemini
- **Database**: Supabase PostgreSQL
- **Weather API**: OpenWeatherMap
- **Authentication**: Supabase JWT
- **Rate Limiting**: SlowAPI
- **Deployment**: Docker on Hugging Face Spaces

## 📈 System Status

Check real-time system health and model loading status:
- **Health Endpoint**: `/api/v1/health`
- **Model Registry**: All 6 ML models loaded in memory for fast inference
- **Weather Cache**: 1-hour TTL for optimal API usage
- **Database**: Live PostgreSQL connection for user data and prediction logging

## 🚀 Getting Started

1. **Explore the API**: Visit the interactive documentation at `/docs`
2. **Test Endpoints**: Use the examples above or the built-in API explorer
3. **Chat with AI**: Try the conversational agent for agricultural advice
4. **Check Health**: Monitor system status via `/api/v1/health`

## 📞 Support

For technical support or agricultural questions, the AI agent is available 24/7 through the chat endpoint. The system provides expert advice on:
- Crop selection and planning
- Disease identification and treatment
- Fertilizer recommendations
- Weather-based farming decisions
- Government scheme guidance
- Sustainable farming practices

---

**Built with ❤️ for Indian farmers using cutting-edge AI and agricultural science.**