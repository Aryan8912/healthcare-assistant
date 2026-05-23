"""
agents/summary_agent.py — Summarizes conversation history for a session.
"""
from typing import Optional
from backend.modules.memory_manager import memory_manager
from backend.tools.rag_tools import summarize_conversation


# ── Summary Agent ─────────────────────────────────────────────────────────────

async def run(message: str, session_id: Optional[str] = None) -> dict:
    """
    Main summary agent handler.

    Args:
        message:    User message
        session_id: Session ID to summarize
    Returns:
        Dict with summary response and tool calls
    """
    tool_calls = []

    if not session_id:
        return {
            "response":   "No active session found to summarize.",
            "agent":      "summary_agent",
            "tool_calls": tool_calls,
        }

    # Step 1 — Get conversation stats
    tool_calls.append({"tool": "summarize_conversation", "status": "calling"})
    result = await summarize_conversation(session_id)
    tool_calls[-1]["status"] = "done"

    summary  = result.get("summary", "")
    stats    = result.get("stats", {})
    total    = stats.get("total", 0)

    if total == 0:
        response = "No conversation history found for this session."
    else:
        response = (
            f"📋 **Conversation Summary**\n\n"
            f"{summary}\n\n"
            f"---\n"
            f"📊 Stats: {total} messages | "
            f"Agents used: {', '.join(stats.get('agents_used', ['general']))}"
        )

    return {
        "response":   response,
        "agent":      "summary_agent",
        "tool_calls": tool_calls,
        "stats":      stats,
    }


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    from backend.modules.memory_manager import memory_manager

    async def test():
        print("🧪 Testing summary agent...\n")

        # Create a test session with messages
        session_id = "summary-test-001"

        await memory_manager.save_message(session_id, "user",      "I want to book an appointment with a cardiologist",  "appointment_agent")
        await memory_manager.save_message(session_id, "assistant", "I can help! Please provide your name and phone.",    "appointment_agent")
        await memory_manager.save_message(session_id, "user",      "What are symptoms of high blood pressure?",          "rag_agent")
        await memory_manager.save_message(session_id, "assistant", "High BP symptoms include headache, dizziness...",    "rag_agent")

        print(f"👤 User: Summarize our conversation")
        result = await run("Summarize our conversation", session_id=session_id)
        print(f"🤖 Agent: {result['response'][:300]}")
        print(f"🔧 Tools: {[t['tool'] for t in result['tool_calls']]}")

        # Cleanup
        await memory_manager.clear_history(session_id)
        print("\n🎉 Summary agent test complete!")

    asyncio.run(test())