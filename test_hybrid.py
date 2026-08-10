import asyncio
import os
import json
from dotenv import load_dotenv

# Load env variables
load_dotenv()

from app.agent.graph import graph

async def main():
    print("==================================================")
    print("Krishi Mitra Hybrid Intelligence Test")
    print("==================================================")
    
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ ERROR: TAVILY_API_KEY is missing from your .env file!")
        print("Get a free key from https://app.tavily.com and add it.")
        return
        
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY is missing from your .env file!")
        return
        
    print("✅ API keys found. Agent ready.\n")

    # Test 1: Time-sensitive question (Should use Tavily)
    print("\n--- Test 1: Recent Events (Should use search_web_live) ---")
    query1 = "What is the latest news about PM-KISAN scheme in August 2026?"
    print(f"Farmer: {query1}")
    
    inputs1 = {"messages": [("user", query1)]}
    async for event in graph.astream(inputs1, {"configurable": {"thread_id": "test_1"}}):
        for key, value in event.items():
            if key == "tools":
                print(f"🔧 Tool Executed: {value['messages'][-1].name}")
        if "agent" in event and "messages" in event["agent"]:
            last_message = event["agent"]["messages"][-1]
            if last_message.content:
                print(f"🤖 Agent Response:\n{last_message.content}")

    # Test 2: Safety-Critical question (Should use search_farming_knowledge)
    print("\n--- Test 2: Safety-Critical (Should use Static KB) ---")
    query2 = "How much Mancozeb should I mix per liter of water for tomato blight? A blog said 10g."
    print(f"Farmer: {query2}")
    
    inputs2 = {"messages": [("user", query2)]}
    async for event in graph.astream(inputs2, {"configurable": {"thread_id": "test_2"}}):
        for key, value in event.items():
            if key == "tools":
                print(f"🔧 Tool Executed: {value['messages'][-1].name}")
        if "agent" in event and "messages" in event["agent"]:
            last_message = event["agent"]["messages"][-1]
            if last_message.content:
                print(f"🤖 Agent Response:\n{last_message.content}")

if __name__ == "__main__":
    asyncio.run(main())
