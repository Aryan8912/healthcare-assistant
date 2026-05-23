"""
api/chat.py — Main AI chat endpoint using LangGraph workflow.
Supports text chat and document analysis.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid

from backend.db.database import get_db
from backend.db.models import ConversationHistory
from backend.config import settings
from backend.graph.workflow import run_workflow

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:    str
    session_id: Optional[str] = None
    file_id:    Optional[str] = None  # ← for document analysis


class ChatResponse(BaseModel):
    session_id: str
    response:   str
    agent_used: str
    intent:     str
    tool_calls: list[dict] = []


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Main chat endpoint using LangGraph multi-agent workflow."""

    session_id = req.session_id or str(uuid.uuid4())

    result = await run_workflow(
        message    = req.message,
        session_id = session_id,
        file_id    = req.file_id,
    )

    return ChatResponse(
        session_id = session_id,
        response   = result["response"],
        agent_used = result["agent_used"],
        intent     = result["intent"],
        tool_calls = result["tool_calls"],
    )


@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db:         AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ConversationHistory)
        .where(ConversationHistory.session_id == session_id)
        .order_by(ConversationHistory.created_at.asc())
        .limit(settings.context_window_messages)
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "total":      len(rows),
        "messages":   [{"role": r.role, "content": r.content} for r in rows],
    }


@router.delete("/chat/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    db:         AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ConversationHistory)
        .where(ConversationHistory.session_id == session_id)
    )
    rows = result.scalars().all()
    for row in rows:
        await db.delete(row)
    return {"message": f"✅ Cleared {len(rows)} messages.", "session_id": session_id}