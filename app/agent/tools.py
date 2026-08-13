"""
LangChain @tool wrappers around existing farming services.

Each tool wraps an existing service class and exposes it to the LLM
with a clear description so the agent knows when to call it.
"""

import json

import structlog
from langchain_core.tools import tool

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# 1. Weather Intelligence Tool
# ---------------------------------------------------------------------------
@tool("get_weather_intelligence")
async def get_weather_intelligence(location: str) -> str:
    """Get current weather conditions, 7-day forecast, and agricultural
    alerts for a location in India. Use this for irrigation scheduling,
    spray timing, harvest decisions, and frost/heat warnings.

    Args:
        location: City or district name (e.g., "Patna", "Nagpur", "Ludhiana")
    """
    try:
        from app.services.weather_service import WeatherService
        service = WeatherService()
        result = await service.get_weather(location)
        return result.model_dump_json()
    except Exception as e:
        logger.error("Weather tool failed", error=str(e))
        return json.dumps({"error": f"Weather data unavailable: {str(e)}"})


# ---------------------------------------------------------------------------
# 2. Crop Recommendation Tool
# ---------------------------------------------------------------------------
@tool("recommend_crop")
async def recommend_crop(
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    temperature: float,
    humidity: float,
    ph: float,
    rainfall: float,
) -> str:
    """Recommend the best crops to grow based on soil nutrients and climate.
    Uses a trained ML model (XGBoost/LightGBM stacking ensemble).

    Args:
        nitrogen: Soil nitrogen content in kg/ha (0-200)
        phosphorus: Soil phosphorus content in kg/ha (0-200)
        potassium: Soil potassium content in kg/ha (0-300)
        temperature: Average temperature in °C
        humidity: Average humidity percentage (0-100)
        ph: Soil pH value (0-14)
        rainfall: Annual rainfall in mm
    """
    try:
        from app.models.crop_recommend import CropRecommendRequest
        from app.services.crop_service import CropService

        service = CropService()
        request = CropRecommendRequest(
            nitrogen=nitrogen, phosphorus=phosphorus, potassium=potassium,
            temperature=temperature, humidity=humidity, ph=ph, rainfall=rainfall,
        )
        result = await service.predict(request)
        return result.model_dump_json()
    except Exception as e:
        logger.error("Crop recommendation failed", error=str(e))
        return json.dumps({"error": f"Crop recommendation unavailable: {str(e)}"})


# ---------------------------------------------------------------------------
# 3. Yield Prediction Tool
# ---------------------------------------------------------------------------
@tool("predict_crop_yield")
async def predict_crop_yield(
    crop: str,
    state: str,
    district: str,
    season: str,
    area_hectares: float,
) -> str:
    """Predict expected crop yield in tonnes/hectare using ML ensemble model.

    Args:
        crop: Crop name (e.g., "Rice", "Wheat", "Maize", "Cotton")
        state: Indian state name (e.g., "Bihar", "Punjab", "Maharashtra")
        district: District name (e.g., "Patna", "Ludhiana")
        season: Growing season — "Kharif", "Rabi", or "Summer"
        area_hectares: Area of land in hectares
    """
    try:
        from app.models.yield_predict import YieldPredictRequest
        from app.services.yield_service import YieldService

        service = YieldService()
        request = YieldPredictRequest(
            crop=crop, state=state, district=district,
            season=season, area_hectares=area_hectares,
        )
        result = await service.predict_yield(request)
        return result.model_dump_json()
    except Exception as e:
        logger.error("Yield prediction failed", error=str(e))
        return json.dumps({"error": f"Yield prediction unavailable: {str(e)}"})


# ---------------------------------------------------------------------------
# 4. Market Price Tool
# ---------------------------------------------------------------------------
@tool("get_market_prices")
async def get_market_prices(crop: str, state: str = "Maharashtra") -> str:
    """Get current market prices, price trends, and best sell timing for a crop.

    IMPORTANT: The response includes a 'data_source' field.
    - If "govt_mandi", tell the farmer this is official verified data from data.gov.in.
    - If "live_search", tell the farmer this was fetched from the live web.
    - If "estimated", clearly warn the farmer that this is a model estimate and they should check their local mandi.
    - If success=False, provide the farmer with the suggested next steps returned in the 'suggestions' field.

    Args:
        crop: Crop name (e.g., "Rice", "Wheat", "Tomato", "Onion")
        state: Indian state for regional pricing (default: Maharashtra)
    """
    try:
        from app.services.market_service import MarketService

        service = MarketService()
        result = await service.get_market_price(crop, state)
        return result.model_dump_json()
    except Exception as e:
        logger.error("Market price failed", error=str(e))
        return json.dumps({"error": f"Market data unavailable: {str(e)}"})


# ---------------------------------------------------------------------------
# 5. Fertilizer Recommendation Tool
# ---------------------------------------------------------------------------
@tool("get_fertilizer_plan")
async def get_fertilizer_plan(
    crop: str,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
    area_hectares: float,
) -> str:
    """Get fertilizer recommendations with NPK deficit analysis,
    product suggestions, application schedule, and cost estimates.

    Args:
        crop: Crop name (e.g., "Rice", "Wheat")
        nitrogen: Current soil nitrogen in kg/ha (0-200)
        phosphorus: Current soil phosphorus in kg/ha (0-200)
        potassium: Current soil potassium in kg/ha (0-300)
        ph: Soil pH (0-14)
        area_hectares: Area in hectares
    """
    try:
        from app.models.fertilizer import FertilizerRequest
        from app.services.fertilizer_service import FertilizerService

        service = FertilizerService()
        request = FertilizerRequest(
            crop=crop, nitrogen=nitrogen, phosphorus=phosphorus,
            potassium=potassium, ph=ph, area_hectares=area_hectares,
        )
        result = await service.recommend(request)
        return result.model_dump_json()
    except Exception as e:
        logger.error("Fertilizer recommendation failed", error=str(e))
        return json.dumps({"error": f"Fertilizer recommendation unavailable: {str(e)}"})


# ---------------------------------------------------------------------------
# 6. Pest Risk Assessment Tool
# ---------------------------------------------------------------------------
@tool("assess_pest_risk")
async def assess_pest_risk(
    crop: str,
    state: str,
    growth_stage: str,
    district: str = None,
) -> str:
    """Assess pest and disease risk for a crop based on location,
    growth stage, and current weather conditions.

    Args:
        crop: Crop name (e.g., "Rice", "Tomato", "Cotton")
        state: Indian state name
        growth_stage: Current stage — "seedling", "vegetative", "flowering", "fruiting", "maturity"
        district: Optional district name for more precise assessment
    """
    try:
        from app.models.pest_risk import PestRiskRequest
        from app.services.pest_service import PestService

        service = PestService()
        request = PestRiskRequest(
            crop=crop, state=state, growth_stage=growth_stage, district=district,
        )
        result = await service.assess_risk(request)
        return result.model_dump_json()
    except Exception as e:
        logger.error("Pest risk assessment failed", error=str(e))
        return json.dumps({"error": f"Pest risk assessment unavailable: {str(e)}"})


# ---------------------------------------------------------------------------
# 7. Farming Knowledge Search (RAG) Tool
# ---------------------------------------------------------------------------
@tool("search_farming_knowledge")
def search_farming_knowledge(query: str) -> str:
    """Search the agricultural knowledge base for information about crop
    management, disease treatment, government schemes, organic farming,
    and best practices. Use this when the farmer asks 'how to' questions
    or needs specific agricultural guidance.

    Args:
        query: Natural language search query (e.g., "how to treat late blight in tomato")
    """
    # This tool is handled specially in the agent node — the store is
    # injected there. This is a placeholder that returns a message
    # indicating the search should be handled by the agent node.
    return json.dumps({
        "note": "Knowledge search is performed inline in the agent node via store.search()"
    })


# ---------------------------------------------------------------------------
# 8. Live Web Search Tool (Tavily)
# ---------------------------------------------------------------------------
@tool("search_web_live")
async def search_web_live(query: str) -> str:
    """Search the live internet for real-time agricultural information.

    USE THIS TOOL WHEN:
    - The farmer asks about CURRENT events (outbreaks, weather disasters, policy changes)
    - The farmer asks about a crop or technique NOT in the knowledge base
    - You need to verify or update information you're unsure about
    - The farmer asks about very recent government scheme updates

    DO NOT USE THIS TOOL WHEN:
    - You already have verified information from the knowledge base
    - The farmer asks about standard pesticide dosages (use knowledge base instead)
    - The question is about basic crop cultivation that you already know

    Args:
        query: Search query in English (e.g., "latest tomato blight outbreak Maharashtra 2026")
    """
    try:
        import os

        from langchain_tavily import TavilySearch

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return json.dumps({"error": "Web search not configured (TAVILY_API_KEY missing)"})

        search = TavilySearch(
            tavily_api_key=api_key,
            max_results=3,
            search_depth="advanced",
            include_answer=True,
        )
        results = await search.ainvoke({"query": f"India agriculture {query}"})

        # Format results for the LLM
        if isinstance(results, list):
            formatted = []
            for r in results[:3]:
                formatted.append({
                    "title": r.get("title", ""),
                    "content": r.get("content", "")[:500],
                    "url": r.get("url", ""),
                })
            return json.dumps({"results": formatted, "source": "live_web_search"})

        return json.dumps({"results": str(results)[:1500], "source": "live_web_search"})

    except Exception as e:
        logger.error("Web search failed", error=str(e))
        return json.dumps({"error": f"Web search unavailable: {str(e)}"})


# ---------------------------------------------------------------------------
# Collect all tools for binding to the LLM
# ---------------------------------------------------------------------------
ALL_TOOLS = [
    get_weather_intelligence,
    recommend_crop,
    predict_crop_yield,
    get_market_prices,
    get_fertilizer_plan,
    assess_pest_risk,
    search_farming_knowledge,
    search_web_live,
]

TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}
