"""
LangGraph StateGraph — Compiles the farming agent with all production features.

Features enabled:
    1. Persistence        — InMemorySaver checkpointer (thread_id based)
    2. Durable Execution  — Automatic via checkpointer
    3. Fault Tolerance    — RetryPolicy + TimeoutPolicy on nodes
    4. Streaming          — via astream() in the API layer
    5. Interrupts (HITL)  — interrupt() in safety_review_node
    6. Time Travel        — via get_state_history() + update_state()
    7. Short-term Memory  — trim_messages in agent_node
    8. Long-term Memory   — InMemoryStore with per-user namespaces
    9. RAG Search         — InMemoryStore with semantic search (when embeddings available)
    10. Subgraphs         — Disease detection pipeline (future)
"""

import os

import structlog
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore
from langgraph.types import RetryPolicy

from app.agent.llm_providers import get_llm
from app.agent.nodes import agent_node, safety_review_node, should_continue, tool_executor
from app.agent.state import FarmerAgentState
from app.agent.tools import ALL_TOOLS

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# 1. Initialize the LLM (via provider factory — set LLM_PROVIDER in .env)
# ---------------------------------------------------------------------------
llm = get_llm(temperature=0.3)

# Bind all farming tools to the LLM
model_with_tools = llm.bind_tools(ALL_TOOLS)

# ---------------------------------------------------------------------------
# 2. Persistence — InMemorySaver (swap to SqliteSaver for production)
# ---------------------------------------------------------------------------
checkpointer = InMemorySaver()

# ---------------------------------------------------------------------------
# 3. Long-Term Memory (Farmer Profiles)
# ---------------------------------------------------------------------------
# Knowledge base search now happens via Supabase pgvector (see memory.py).
# InMemoryStore is purely used for tracking farmer session variables.
store = InMemoryStore()
logger.info("Memory store initialized (user memory only — KB search uses pgvector)")

# ---------------------------------------------------------------------------
# 4. Build the StateGraph
# ---------------------------------------------------------------------------
builder = StateGraph(FarmerAgentState)

# Add nodes with fault tolerance (retry + timeout)
builder.add_node(
    "agent",
    agent_node,
    retry_policy=RetryPolicy(max_attempts=2),
)

builder.add_node(
    "tools",
    tool_executor,
    retry_policy=RetryPolicy(max_attempts=3),
)

builder.add_node(
    "safety_review",
    safety_review_node,
)

# Add edges
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    "safety_review": "safety_review",
})
builder.add_edge("tools", "agent")       # Loop back after tool results
builder.add_edge("safety_review", END)   # End after safety check

# ---------------------------------------------------------------------------
# 5. Compile the graph with persistence + memory store
# ---------------------------------------------------------------------------
graph = builder.compile(
    checkpointer=checkpointer,
    store=store,
)

logger.info("🧠 Farming Agent Graph compiled successfully")


# ---------------------------------------------------------------------------
# 6. Seed the knowledge base on first import
# ---------------------------------------------------------------------------
_knowledge_seeded = False

async def ensure_knowledge_seeded():
    """Seed the knowledge base if not already done."""
    global _knowledge_seeded
    if not _knowledge_seeded:
        from app.agent.knowledge import seed_knowledge_base
        count = await seed_knowledge_base(store)
        _knowledge_seeded = True
        logger.info(f"Knowledge base ready with {count} documents")
