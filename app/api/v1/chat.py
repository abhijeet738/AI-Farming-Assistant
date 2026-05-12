"""
Chat API — FastAPI endpoints for the LangGraph farming agent.

Endpoints:
    POST /chat/message     — Send a message and get a streaming SSE response
    POST /chat/invoke      — Send a message and get a full JSON response
    POST /chat/resume      — Resume after a human-in-the-loop interrupt
    GET  /chat/history      — Get conversation history for a thread
    GET  /chat/state        — Get current state of a thread (for time travel)
"""

import json
import uuid

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = structlog.get_logger()
router = APIRouter()


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------
class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="The farmer's message")
    user_id: str = Field(default="default", description="Unique farmer identifier")
    thread_id: str | None = Field(
        default=None,
        description="Conversation thread ID. Auto-generated if not provided."
    )

class ChatResumeRequest(BaseModel):
    thread_id: str = Field(..., description="Thread ID of the interrupted conversation")
    approved: bool = Field(..., description="Whether the farmer approves the action")

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    interrupted: bool = False
    interrupt_payload: dict | None = None


# ---------------------------------------------------------------------------
# POST /chat/invoke — Full response (non-streaming)
# ---------------------------------------------------------------------------
@router.post("/invoke", response_model=ChatResponse)
async def chat_invoke(request: ChatMessageRequest):
    """Send a message to the farming agent and get a complete response.
    
    This is the simpler, non-streaming endpoint. Use /chat/message for
    streaming responses.
    """
    from app.agent.graph import ensure_knowledge_seeded, graph

    # Seed knowledge base on first call
    await ensure_knowledge_seeded()

    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await graph.ainvoke(
            {
                "messages": [{"role": "user", "content": request.message}],
                "user_id": request.user_id,
            },
            config=config,
        )

        # Check if the graph was interrupted (HITL)
        state = graph.get_state(config)
        if state.next:
            # Graph is paused at an interrupt
            interrupt_data = None
            if state.tasks:
                for task in state.tasks:
                    if hasattr(task, "interrupts") and task.interrupts:
                        interrupt_data = task.interrupts[0].value
                        break

            return ChatResponse(
                response="⏸️ Awaiting your approval (see interrupt details).",
                thread_id=thread_id,
                interrupted=True,
                interrupt_payload=interrupt_data,
            )

        # Extract the final AI message
        last_ai_msg = ""
        for msg in reversed(result["messages"]):
            if hasattr(msg, "type") and msg.type == "ai" and msg.content:
                last_ai_msg = msg.content
                break

        return ChatResponse(
            response=last_ai_msg or "I processed your request but have no additional response.",
            thread_id=thread_id,
        )

    except Exception as e:
        logger.error("Chat invoke failed", error=str(e), thread_id=thread_id)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# ---------------------------------------------------------------------------
# POST /chat/message — Streaming SSE response
# ---------------------------------------------------------------------------
@router.post("/message")
async def chat_message_stream(request: ChatMessageRequest):
    """Send a message and receive a streaming Server-Sent Events response.
    
    Tokens appear word-by-word as the LLM generates them.
    """
    from app.agent.graph import ensure_knowledge_seeded, graph

    await ensure_knowledge_seeded()

    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    async def event_stream():
        # Send thread_id first so the client knows it
        yield f"event: thread_id\ndata: {thread_id}\n\n"

        try:
            async for msg, metadata in graph.astream(
                {
                    "messages": [{"role": "user", "content": request.message}],
                    "user_id": request.user_id,
                },
                config=config,
                stream_mode="messages",
            ):
                # Only stream content from the agent node (not tool calls)
                if (
                    msg.content
                    and metadata.get("langgraph_node") == "agent"
                    and not getattr(msg, "tool_calls", None)
                ):
                    yield f"data: {msg.content}\n\n"

                # Stream tool execution status updates
                if metadata.get("langgraph_node") == "tools":
                    if hasattr(msg, "name"):
                        yield f"event: tool_status\ndata: {json.dumps({'tool': msg.name, 'status': 'completed'})}\n\n"

            # Check for interrupt
            state = graph.get_state(config)
            if state.next:
                interrupt_data = {}
                if state.tasks:
                    for task in state.tasks:
                        if hasattr(task, "interrupts") and task.interrupts:
                            interrupt_data = task.interrupts[0].value
                            break
                yield f"event: interrupt\ndata: {json.dumps(interrupt_data)}\n\n"

            yield "event: done\ndata: {}\n\n"

        except Exception as e:
            logger.error("Streaming failed", error=str(e))
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Thread-ID": thread_id,
        },
    )


# ---------------------------------------------------------------------------
# POST /chat/resume — Resume after human-in-the-loop interrupt
# ---------------------------------------------------------------------------
@router.post("/resume", response_model=ChatResponse)
async def chat_resume(request: ChatResumeRequest):
    """Resume a conversation that was interrupted for human approval.
    
    Used after the agent pauses for safety review of chemical recommendations.
    """
    from langgraph.types import Command

    from app.agent.graph import graph

    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        # Check that the thread actually has a pending interrupt
        state = graph.get_state(config)
        if not state.next:
            raise HTTPException(
                status_code=400,
                detail="No pending interrupt found for this thread."
            )

        # Resume the graph with the farmer's decision
        result = await graph.ainvoke(
            Command(resume=request.approved),
            config=config,
        )

        # Extract the final response
        last_ai_msg = ""
        for msg in reversed(result["messages"]):
            if hasattr(msg, "type") and msg.type == "ai" and msg.content:
                last_ai_msg = msg.content
                break

        return ChatResponse(
            response=last_ai_msg or "Action processed.",
            thread_id=request.thread_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Resume failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Resume error: {str(e)}")


# ---------------------------------------------------------------------------
# GET /chat/history — Get checkpoint history (Time Travel)
# ---------------------------------------------------------------------------
@router.get("/history/{thread_id}")
async def get_thread_history(thread_id: str):
    """Get the checkpoint history for a conversation thread.
    
    Useful for debugging and time travel — replaying or forking
    from a past checkpoint.
    """
    from app.agent.graph import graph

    config = {"configurable": {"thread_id": thread_id}}

    try:
        history = list(graph.get_state_history(config))

        return {
            "thread_id": thread_id,
            "checkpoints": [
                {
                    "checkpoint_id": s.config["configurable"].get("checkpoint_id"),
                    "next_nodes": list(s.next) if s.next else [],
                    "num_messages": len(s.values.get("messages", [])),
                }
                for s in history[:20]  # Limit to last 20 checkpoints
            ],
        }
    except Exception as e:
        logger.error("History fetch failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /chat/state — Get current state of a thread
# ---------------------------------------------------------------------------
@router.get("/state/{thread_id}")
async def get_thread_state(thread_id: str):
    """Get the current state of a conversation thread.
    
    Shows the latest messages, pending interrupts, and user context.
    """
    from app.agent.graph import graph

    config = {"configurable": {"thread_id": thread_id}}

    try:
        state = graph.get_state(config)

        if not state.values:
            raise HTTPException(status_code=404, detail="Thread not found")

        messages = []
        for msg in state.values.get("messages", []):
            messages.append({
                "type": getattr(msg, "type", "unknown"),
                "content": getattr(msg, "content", ""),
            })

        return {
            "thread_id": thread_id,
            "messages": messages[-10:],  # Last 10 messages
            "next_nodes": list(state.next) if state.next else [],
            "has_pending_interrupt": bool(state.next),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("State fetch failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
