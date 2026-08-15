import asyncio
from langchain_tavily import TavilySearch
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    api_key = os.getenv("TAVILY_API_KEY")
    print("Key length:", len(api_key))
    try:
        search = TavilySearch(
            tavily_api_key=api_key,
            max_results=3,
            search_depth="advanced",
            include_answer=True,
        )
        query = "current mandi price Potato Uttar Pradesh India per quintal today 2026"
        results = await search.ainvoke({"query": query})
        print(results)
    except Exception as e:
        print("Error:", str(e))

asyncio.run(main())
