"""
Chat API — FastAPI endpoints for the LangGraph farming agent.

Endpoints:
    POST /chat/message     — Send a message and get a streaming SSE response
    POST /chat/invoke      — Send a message and get a full JSON response
    POST /chat/resume      — Resume after a human-in-the-loop interrupt
    GET  /chat/history      — Get conversation history for a thread
    GET  /chat/state        — Get current state of a thread (for time travel)
"""

import asyncio
import json
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import CurrentUser, get_current_user
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Pre-import at module level so the graph compiles ONCE when uvicorn starts,
# not on the first incoming request. This eliminates the cold-start delay.
from app.agent.graph import ensure_knowledge_seeded, graph
from app.db import crud
from app.db.database import get_db

logger = structlog.get_logger()
router = APIRouter()

# Lock to prevent concurrent seeding on simultaneous first requests
_seed_lock = asyncio.Lock()


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------
class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="The farmer's message")
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
    """Send a message to the farming agent and get a complete response."""
    # Seed knowledge base on first call (safe for concurrent requests via lock)
    async with _seed_lock:
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
async def chat_message_stream(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Send a message and receive a streaming Server-Sent Events response."""
    async with _seed_lock:
        await ensure_knowledge_seeded()

    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Ensure ChatSession exists and add user message to DB
    session = crud.get_chat_session_by_thread(db, thread_id)
    if not session:
        # Create a new session, derive a short title from the first message
        title = request.message[:50] + "..." if len(request.message) > 50 else request.message
        session = crud.create_chat_session(db, thread_id=thread_id, user_id=user.id, title=title)
    else:
        crud.touch_chat_session(db, thread_id)
    
    crud.add_chat_message(db, session_id=session.id, role="user", content=request.message)

    async def event_stream():
        # Send thread_id first (named event — frontend should ignore its data for display)
        yield f"event: thread_id\ndata: {thread_id}\n\n"
        
        final_ai_message = ""

        try:
            async for msg, metadata in graph.astream(
                {
                    "messages": [{"role": "user", "content": request.message}],
                    "user_id": user.id,
                },
                config=config,
                stream_mode="messages",
            ):
                # Only stream text from the agent node (not tool calls)
                if (
                    msg.content
                    and metadata.get("langgraph_node") == "agent"
                    and not getattr(msg, "tool_calls", None)
                ):
                    # Anthropic streams content as a LIST of content blocks:
                    # [{'type': 'text', 'text': 'Hello', 'index': 0}, ...]
                    # We must extract only the text; raw list repr must NOT be sent.
                    content = msg.content
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

                    if text:
                        final_ai_message += text
                        yield f"data: {json.dumps(text)}\n\n"

                # Stream tool status updates (named events — frontend ignores)
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
            
            # Save the final AI message to the DB
            if final_ai_message:
                # We need a new db session for the background task if the main one closed, but since event_stream is within the request scope, db might still be open. 
                # Better to use a fresh session or assume it's open until the stream closes. FastAPI streaming allows this.
                try:
                    crud.add_chat_message(db, session_id=session.id, role="assistant", content=final_ai_message)
                except Exception as db_err:
                    logger.error("Failed to save AI message to DB", error=str(db_err))

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
    """Resume a conversation that was interrupted for human approval."""
    from langgraph.types import Command

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
# GET /chat/sessions — List sessions for sidebar
# ---------------------------------------------------------------------------
@router.get("/sessions")
async def get_sessions(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Get all chat sessions for a user to display in the sidebar."""
    try:
        sessions = crud.get_chat_sessions(db, user_id=user.id, limit=50)
        return [
            {
                "id": s.id,
                "thread_id": s.thread_id,
                "title": s.title,
                "created_at": s.created_at,
                "last_active_at": s.last_active_at,
            }
            for s in sessions
        ]
    except Exception as e:
        logger.error("Failed to fetch sessions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /chat/sessions/{thread_id}/messages — Get chat history for UI
# ---------------------------------------------------------------------------
@router.get("/sessions/{thread_id}/messages")
async def get_session_messages(thread_id: str, db: Session = Depends(get_db)):
    """Get all messages for a specific session."""
    try:
        session = crud.get_chat_session_by_thread(db, thread_id)
        if not session:
            return []
            
        messages = crud.get_chat_messages(db, session_id=session.id, limit=100)
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in messages
        ]
    except Exception as e:
        logger.error("Failed to fetch messages", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


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
