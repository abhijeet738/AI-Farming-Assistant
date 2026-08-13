"""Manual async smoke test for market pricing (not collected by pytest)."""

__test__ = False  # pytest: ignore this module

import asyncio

from app.services.market_service import MarketService


async def main():
    service = MarketService()

    print("\n--- Test 1: Wheat in Punjab (ML Supported) ---")
    res1 = await service.get_market_price("Wheat", "Punjab")
    print(f"Price: {res1.current_price_per_quintal}")
    print(f"Source: {res1.data_source}")
    print(f"URL: {res1.source_url}")
    print(f"Success: {res1.success}")
    if res1.forecast_7_days:
        print("ML Forecast: YES")
    else:
        print("ML Forecast: NO")

    print("\n--- Test 2: Dragon Fruit in Kerala (Live Only, No ML) ---")
    res2 = await service.get_market_price("Dragon Fruit", "Kerala")
    print(f"Price: {res2.current_price_per_quintal}")
    print(f"Source: {res2.data_source}")
    print(f"URL: {res2.source_url}")
    print(f"Success: {res2.success}")
    if res2.forecast_7_days:
        print("ML Forecast: YES")
    else:
        print("ML Forecast: NO")

    print("\n--- Test 3: Saffron in Manipur (Null Object) ---")
    res3 = await service.get_market_price("Saffron", "Manipur")
    print(f"Price: {res3.current_price_per_quintal}")
    print(f"Source: {res3.data_source}")
    print(f"Success: {res3.success}")
    print(f"Message: {res3.message}")
    print(f"Suggestions: {res3.suggestions}")

if __name__ == "__main__":
    asyncio.run(main())
