"""
tests/quick_start.py — Quick start guide and system check.
Run: python -m backend.tests.quick_start
"""
import asyncio
from backend.graph.workflow import run_workflow

async def quick_start():
    print("🚀 MedAssist Quick Start")
    print("=" * 50)
    print()

    test_cases = [
        ("Hello!",                              "General greeting"),
        ("Show me all available doctors",       "Appointment listing"),
        ("What are the symptoms of diabetes?",  "Medical Q&A"),
        ("मधुमेह के लक्षण क्या हैं?",          "Hindi query"),
        ("Summarize our conversation",          "Summary"),
    ]

    session_id = "quick-start-session"

    for message, description in test_cases:
        print(f"📝 Test: {description}")
        print(f"   Input: {message}")
        result = await run_workflow(message, session_id=session_id)
        print(f"   Agent: {result['agent_used']}")
        print(f"   Intent: {result['intent']}")
        print(f"   Response: {result['response'][:100]}...")
        print()

    print("✅ Quick start complete! System is working.")
    print("\n🌐 Open http://localhost:5173 to use the chat UI")
    print("📚 Open http://localhost:8000/docs for API documentation")

if __name__ == "__main__":
    asyncio.run(quick_start())