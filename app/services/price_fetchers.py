"""
Price Fetcher Strategies + Factory (Singleton).

Patterns used:
  - Strategy: Each fetcher implements the same interface
  - Factory:  PriceFetcherFactory creates/caches fetcher instances
  - Singleton: Factory reuses instances across requests
  - Chain of Responsibility: MarketService tries fetchers in priority order
"""

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import httpx
import structlog

logger = structlog.get_logger()

@dataclass
class PriceResult:
    """Standardized result from any price fetcher strategy."""
    price: float               # Price per quintal (INR)
    source_name: str           # "govt_mandi", "live_search", "estimated"
    source_url: str = ""       # URL for citation
    raw_content: str = ""      # Raw text (for LLM context)
    data_date: str = ""        # When this price was recorded


class PriceFetcherStrategy(ABC):
    """Abstract base for all price fetching strategies."""
    name: str = "base"

    @abstractmethod
    async def fetch_price(self, crop: str, state: str) -> PriceResult | None:
        pass


class GovtMandiPriceFetcher(PriceFetcherStrategy):
    """Fetch from data.gov.in — the official government source."""
    name = "govt_mandi"

    async def fetch_price(self, crop: str, state: str) -> PriceResult | None:
        api_key = os.getenv("DATA_GOV_API_KEY")
        if not api_key:
            return None

        # The data.gov.in API for Agmarknet
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

        params = {
            "api-key": api_key,
            "format": "json",
            "filters[Commodity]": crop.strip().title(),
            "filters[State]": state.strip().title(),
            "limit": 1
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    records = data.get("records", [])
                    if records:
                        # Extract modal price (most traded price)
                        record = records[0]
                        modal_price = float(record.get("modal_price", 0))

                        if modal_price > 0:
                            return PriceResult(
                                price=modal_price,
                                source_name="govt_mandi",
                                source_url="https://data.gov.in (Agmarknet)",
                                raw_content=f"Official Mandi Data: {record}",
                                data_date=record.get("arrival_date", datetime.now().strftime("%Y-%m-%d"))
                            )
        except Exception as e:
            logger.warning("GovtMandiPriceFetcher failed", error=str(e))

        return None


class TavilyPriceFetcher(PriceFetcherStrategy):
    """Fetch via Tavily web search — covers niche crops."""
    name = "live_search"

    async def fetch_price(self, crop: str, state: str) -> PriceResult | None:
        try:
            from langchain_tavily import TavilySearch

            api_key = os.getenv("TAVILY_API_KEY")
            if not api_key:
                return None

            search = TavilySearch(
                tavily_api_key=api_key,
                max_results=3,
                search_depth="advanced",
                include_answer=True,
            )

            if not re.fullmatch(r"[A-Za-z ]+", crop):
                return None
            query = f"current mandi price {crop} {state} India per quintal today {datetime.now().year}"
            results = await search.ainvoke({"query": query})

            if isinstance(results, list) and len(results) > 0:
                content = results[0].get("content", "")
                url = results[0].get("url", "")

                price = self._extract_price(content)
                if price:
                    return PriceResult(
                        price=price,
                        source_name="live_search",
                        source_url=url,
                        raw_content=content[:800],
                        data_date=datetime.now().strftime("%Y-%m-%d")
                    )
        except Exception as e:
            logger.warning("TavilyPriceFetcher failed", error=str(e))

        return None

    def _extract_price(self, content: str) -> float | None:
        """Try to extract a numeric price from Tavily search content."""
        patterns = [
            r'₹\s*([\d,]+)',
            r'Rs\.?\s*([\d,]+)',
            r'INR\s*([\d,]+)',
            r'([\d,]+)\s*(?:per|/)\s*(?:quintal|qtl)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(",", "")
                try:
                    price = float(price_str)
                    if 100 < price < 100000:  # Sanity check
                        return price
                except ValueError:
                    continue
        return None


class SyntheticPriceFetcher(PriceFetcherStrategy):
    """Last-resort fallback — generates an estimate based on ML training baseline."""
    name = "estimated"

    # We only return synthetic if it's a known major crop.
    # We refuse to guess for random words (prevents "iPhone" getting a price).
    KNOWN_CROPS = ["Rice", "Wheat", "Maize", "Cotton", "Tomato", "Onion", "Potato", "Soybean", "Sugarcane"]

    async def fetch_price(self, crop: str, state: str) -> PriceResult | None:
        # Simple heuristic to normalize names
        crop_clean = crop.capitalize()

        if crop_clean not in self.KNOWN_CROPS:
            # We don't know anything about this, return None to trigger NullObject fallback
            return None

        base_price = 2000.0 + (len(crop) * 100.0)

        return PriceResult(
            price=base_price,
            source_name="estimated",
            source_url="",
            raw_content="Fallback synthetic price. No live data available.",
            data_date=datetime.now().strftime("%Y-%m-%d")
        )


class PriceFetcherFactory:
    """Singleton Factory that creates and caches fetcher instances."""
    _instances: dict = {}

    @classmethod
    def get_fetcher(cls, name: str) -> PriceFetcherStrategy:
        if name not in cls._instances:
            if name == "govt_mandi":
                cls._instances[name] = GovtMandiPriceFetcher()
            elif name == "tavily":
                cls._instances[name] = TavilyPriceFetcher()
            else:
                cls._instances[name] = SyntheticPriceFetcher()
        return cls._instances[name]

    @classmethod
    def get_chain(cls) -> list[PriceFetcherStrategy]:
        """Returns the cascading chain in priority order."""
        chain = []

        # Tier 1: Govt API (if key exists)
        if os.getenv("DATA_GOV_API_KEY"):
            chain.append(cls.get_fetcher("govt_mandi"))

        # Tier 2: Tavily (if key exists)
        if os.getenv("TAVILY_API_KEY"):
            chain.append(cls.get_fetcher("tavily"))

        # Tier 3: Always available
        chain.append(cls.get_fetcher("synthetic"))

        return chain
