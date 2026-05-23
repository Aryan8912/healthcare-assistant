"""
modules/memory_manager.py — Conversation memory and context management.
Stores, retrieves, and summarizes conversation history per session.
"""
import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import ConversationHistory
from backend.db.database import AsyncSessionLocal
from backend.config import settings


class MemoryManager:
    """
    Manages conversation memory per session.
    Used by agents to maintain context across turns.
    """

    # ── Save Message ──────────────────────────────────────────────────────────

    async def save_message(
        self,
        session_id: str,
        role:       str,
        content:    str,
        agent_used: Optional[str] = None,
    ) -> None:
        """Save a single message to conversation history."""
        async with AsyncSessionLocal() as db:
            msg = ConversationHistory(
                session_id = session_id,
                role       = role,
                content    = content,
                agent_used = agent_used,
            )
            db.add(msg)
            await db.commit()

    # ── Get History ───────────────────────────────────────────────────────────

    async def get_history(
        self,
        session_id: str,
        limit:      int = None,
    ) -> list[dict]:
        """Get conversation history for a session."""
        limit = limit or settings.context_window_messages

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ConversationHistory)
                .where(ConversationHistory.session_id == session_id)
                .order_by(ConversationHistory.created_at.asc())
                .limit(limit)
            )
            rows = result.scalars().all()

            return [
                {
                    "role":       r.role,
                    "content":    r.content,
                    "agent_used": r.agent_used,
                    "timestamp":  r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]

    # ── Get Messages for LLM ─────────────────────────────────────────────────

    async def get_messages_for_llm(
        self,
        session_id: str,
        limit:      int = None,
    ) -> list[dict]:
        """
        Get history formatted for OpenAI messages array.
        Returns [{"role": "user/assistant", "content": "..."}]
        """
        history = await self.get_history(session_id, limit)
        return [
            {"role": h["role"], "content": h["content"]}
            for h in history
        ]

    # ── Clear History ─────────────────────────────────────────────────────────

    async def clear_history(self, session_id: str) -> int:
        """Clear all messages for a session. Returns count deleted."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ConversationHistory)
                .where(ConversationHistory.session_id == session_id)
            )
            rows = result.scalars().all()
            count = len(rows)

            await db.execute(
                delete(ConversationHistory)
                .where(ConversationHistory.session_id == session_id)
            )
            await db.commit()
            return count

    # ── Get Summary ───────────────────────────────────────────────────────────

    async def get_summary(self, session_id: str) -> dict:
        """Get a summary of conversation stats for a session."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ConversationHistory)
                .where(ConversationHistory.session_id == session_id)
                .order_by(ConversationHistory.created_at.asc())
            )
            rows = result.scalars().all()

            if not rows:
                return {
                    "session_id": session_id,
                    "total":      0,
                    "message":    "No conversation history found.",
                }

            agents_used = list({r.agent_used for r in rows if r.agent_used})
            user_msgs   = [r for r in rows if r.role == "user"]
            start_time  = rows[0].created_at
            end_time    = rows[-1].created_at

            return {
                "session_id":  session_id,
                "total":       len(rows),
                "user_msgs":   len(user_msgs),
                "agents_used": agents_used,
                "started_at":  start_time.isoformat() if start_time else None,
                "last_active": end_time.isoformat()   if end_time   else None,
            }

    # ── Format for Context ────────────────────────────────────────────────────

    async def format_context(
        self,
        session_id: str,
        max_chars:  int = 2000,
    ) -> str:
        """
        Format recent conversation as a string for LLM context.
        Truncates to max_chars to stay within token limits.
        """
        history = await self.get_history(session_id)
        if not history:
            return ""

        lines = []
        for h in history:
            role = "Patient" if h["role"] == "user" else "Assistant"
            lines.append(f"{role}: {h['content']}")

        context = "\n".join(lines)

        # Truncate if too long
        if len(context) > max_chars:
            context = context[-max_chars:]
            context = "...\n" + context

        return context


# ── Singleton ─────────────────────────────────────────────────────────────────

memory_manager = MemoryManager()


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    async def test():
        print("🧪 Testing memory manager...")

        session_id = "test-session-001"

        # Save messages
        await memory_manager.save_message(session_id, "user",      "I want to book an appointment")
        await memory_manager.save_message(session_id, "assistant", "Sure! Which doctor would you like?", "appointment_agent")
        await memory_manager.save_message(session_id, "user",      "Dr. Ananya Krishnan please")
        await memory_manager.save_message(session_id, "assistant", "Great! What date works for you?",    "appointment_agent")

        print("✅ Messages saved")

        # Get history
        history = await memory_manager.get_history(session_id)
        print(f"✅ History retrieved: {len(history)} messages")

        # Get LLM messages
        llm_msgs = await memory_manager.get_messages_for_llm(session_id)
        print(f"✅ LLM messages: {len(llm_msgs)}")

        # Get summary
        summary = await memory_manager.get_summary(session_id)
        print(f"✅ Summary: {summary}")

        # Format context
        context = await memory_manager.format_context(session_id)
        print(f"✅ Context:\n{context}")

        # Clear history
        count = await memory_manager.clear_history(session_id)
        print(f"✅ Cleared {count} messages")

        print("\n🎉 Memory manager test complete!")

    asyncio.run(test())