"""
Graph Nodes — the core logic units of the farming agent.

Nodes:
    1. agent_node    — Calls the LLM with tools, memory, and RAG context
    2. tool_executor — Executes tool calls returned by the LLM
    3. safety_review — Human-in-the-loop interrupt for critical actions
"""

from typing import Literal

import structlog
from langchain_core.messages import ToolMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langgraph.types import interrupt

from app.agent.memory import load_farmer_profile, search_knowledge
from app.agent.prompts import build_system_prompt
from app.agent.state import FarmerAgentState
from app.agent.tools import TOOLS_BY_NAME

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Critical action keywords that trigger human-in-the-loop
# ---------------------------------------------------------------------------
CRITICAL_KEYWORDS = [
    "pesticide", "insecticide", "fungicide", "herbicide",
    "chemical spray", "chemical control", "poison",
    "mancozeb", "metalaxyl", "tricyclazole", "imidacloprid",
    "chlorpyrifos", "cypermethrin", "carbendazim",
]


def contains_critical_action(content: str | list) -> bool:
    """Check if a response contains chemical/pesticide recommendations."""
    if not content:
        return False
        
    text = ""
    if isinstance(content, list):
        text = "".join(
            block.get("text", "") 
            for block in content 
            if isinstance(block, dict) and block.get("type") == "text"
        )
    elif isinstance(content, str):
        text = content
    else:
        text = str(content)
        
    content_lower = text.lower()
    return any(kw in content_lower for kw in CRITICAL_KEYWORDS)


# ---------------------------------------------------------------------------
# Node 1: Agent (LLM reasoning)
# ---------------------------------------------------------------------------
async def agent_node(state: FarmerAgentState, store):
    """Main reasoning node — calls the LLM with tools, memory, and RAG.

    This node:
    1. Loads the farmer's long-term profile from the store
    2. Performs semantic search for relevant farming knowledge (RAG)
    3. Trims messages to prevent context overflow
    4. Calls the LLM with all tools bound
    """
    from app.agent.graph import model_with_tools

    user_id = state.get("user_id", "default")

    # 1. Load long-term farmer profile
    farmer_context = await load_farmer_profile(store, user_id)

    # 2. RAG: Semantic search for relevant knowledge
    last_human_msg = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, "type") and msg.type == "human":
            last_human_msg = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "human":
            last_human_msg = msg.get("content", "")
            break

    knowledge_context = await search_knowledge(store, last_human_msg) if last_human_msg else ""

    # 3. Build system prompt with dynamic context
    system_prompt = build_system_prompt(farmer_context, knowledge_context)

    # 4. Trim messages to prevent context overflow (keep last ~4000 tokens)
    trimmed = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=4000,
        start_on="human",
        allow_partial=False,
    )

    messages = [{"role": "system", "content": system_prompt}] + trimmed

    # 5. Call the LLM
    response = await model_with_tools.ainvoke(messages)

    logger.info(
        "Agent response generated",
        has_tool_calls=bool(response.tool_calls),
        num_tool_calls=len(response.tool_calls) if response.tool_calls else 0,
    )

    return {"messages": [response]}


# ---------------------------------------------------------------------------
# Node 2: Tool Executor
# ---------------------------------------------------------------------------
async def tool_executor(state: FarmerAgentState):
    """Execute tool calls from the LLM response.

    Iterates through all tool_calls in the last message and invokes
    the corresponding tool function. Returns ToolMessage results.
    """
    last_message = state["messages"][-1]
    results = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        logger.info("Executing tool", tool=tool_name, args=tool_args)

        tool = TOOLS_BY_NAME.get(tool_name)
        if tool is None:
            results.append(ToolMessage(
                content=f"Error: Unknown tool '{tool_name}'",
                tool_call_id=tool_call["id"],
            ))
            continue

        try:
            observation = await tool.ainvoke(tool_args)
            results.append(ToolMessage(
                content=str(observation),
                tool_call_id=tool_call["id"],
            ))
        except Exception as e:
            logger.error("Tool execution failed", tool=tool_name, error=str(e))
            results.append(ToolMessage(
                content=f"Error executing {tool_name}: {str(e)}",
                tool_call_id=tool_call["id"],
            ))

    return {"messages": results}


# ---------------------------------------------------------------------------
# Node 3: Safety Review (Human-in-the-Loop)
# ---------------------------------------------------------------------------
async def safety_review_node(state: FarmerAgentState):
    """Check if the agent's response contains critical chemical recommendations.

    If it does, pause execution using LangGraph's interrupt() primitive
    and wait for human approval before finalizing the response.
    """
    last_message = state["messages"][-1]
    content = last_message.content if hasattr(last_message, "content") else ""

    if contains_critical_action(content):
        logger.info("Critical action detected, requesting human approval")

        text_preview = ""
        if isinstance(content, list):
            text_preview = "".join(
                b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
            )
        elif isinstance(content, str):
            text_preview = content
        else:
            text_preview = str(content)

        # This pauses the graph and returns the interrupt payload to the caller
        decision = interrupt({
            "type": "safety_review",
            "question": "⚠️ This recommendation involves chemical/pesticide application. "
                        "Do you approve this advice?",
            "preview": text_preview[:500],  # First 500 chars as preview
        })

        # When resumed with Command(resume=False), cancel the recommendation
        if decision is False:
            from langchain_core.messages import AIMessage
            return {"messages": [AIMessage(
                content="I've cancelled that chemical recommendation. "
                        "Would you like me to suggest organic alternatives instead?"
            )]}

    # No critical action or approved — pass through
    return state


# ---------------------------------------------------------------------------
# Conditional edge: should we continue to tools or end?
# ---------------------------------------------------------------------------
def should_continue(state: FarmerAgentState) -> Literal["tools", "safety_review"]:
    """Route to tool executor if the LLM made tool calls, otherwise to safety review."""
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "safety_review"
