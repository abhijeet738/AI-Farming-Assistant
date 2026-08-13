import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from app.agent.nodes import agent_node, should_continue, tool_executor
from app.agent.state import FarmerAgentState


async def main():
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=os.environ["GOOGLE_API_KEY"])
    print("Testing gemini streaming...")

    async for chunk in llm.astream("hi"):
        print(repr(chunk.content))

if __name__ == "__main__":
    asyncio.run(main())
