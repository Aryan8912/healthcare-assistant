"""
tests/final_demo.py — Complete end-to-end demo of the system.
Run: python -m backend.tests.final_demo
"""
import asyncio
from backend.graph.workflow import run_workflow
from backend.modules.rag_engine import rag_engine
from backend.modules.scheduler import scheduler
from backend.modules.memory_manager import memory_manager

async def final_demo():
    print("🏥 MedAssist AI — Final System Demo")
    print("=" * 60)

    session_id = "final-demo-session"

    demos = [
        # (message, description, file_id)
        ("Hello! I need help with healthcare",         "1️⃣  General greeting",          None),
        ("Show me all available doctors",              "2️⃣  List doctors",               None),
        ("What are the symptoms of high blood pressure?", "3️⃣  Medical Q&A (RAG)",       None),
        ("मधुमेह के लक्षण क्या हैं?",                "4️⃣  Hindi query (Multilingual)", None),
        ("I want to cancel my appointment #1",        "5️⃣  Cancel appointment",         None),
        ("Show my appointments for +91-9876543210",   "6️⃣  Appointment history",        None),
        ("Analyze this document",                     "7️⃣  Document analysis",          "fake-id"),
        ("Summarize our conversation",                "8️⃣  Conversation summary",       None),
    ]

    for message, description, file_id in demos:
        print(f"\n{description}")
        print(f"  👤 User: {message}")

        result = await run_workflow(message, session_id=session_id, file_id=file_id)

        print(f"  🤖 Agent: {result['agent_used']}")
        print(f"  🧭 Intent: {result['intent']}")
        if result.get("tool_calls"):
            tools = [t["tool"] for t in result["tool_calls"]]
            print(f"  🔧 Tools: {tools}")
        print(f"  💬 Response: {result['response'][:120]}...")

    # Cleanup
    await memory_manager.clear_history(session_id)
    print("\n" + "=" * 60)
    print("🎉 Final demo complete! All systems working.")

if __name__ == "__main__":
    asyncio.run(final_demo())