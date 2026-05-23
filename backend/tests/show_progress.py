"""
tests/show_progress.py — Show project progress and completion status.
Run: python -m backend.tests.show_progress
"""
from pathlib import Path

BASE = Path(__file__).parent.parent

def check_file(path: str) -> bool:
    return (BASE / path).exists() and (BASE / path).stat().st_size > 0

def show_progress():
    print("📊 MedAssist Project Progress")
    print("=" * 50)

    sections = {
        "Core Setup": [
            ("config.py",           "config.py"),
            ("main.py",             "main.py"),
            ("requirements.txt",    "requirements.txt"),
        ],
        "Database": [
            ("db/models.py",        "db/models.py"),
            ("db/database.py",      "db/database.py"),
            ("db/seed.py",          "db/seed.py"),
        ],
        "API": [
            ("api/chat.py",         "api/chat.py"),
            ("api/appointments.py", "api/appointments.py"),
            ("api/documents.py",    "api/documents.py"),
        ],
        "Modules": [
            ("modules/scheduler.py",          "modules/scheduler.py"),
            ("modules/memory_manager.py",     "modules/memory_manager.py"),
            ("modules/rag_engine.py",         "modules/rag_engine.py"),
            ("modules/document_processor.py", "modules/document_processor.py"),
        ],
        "Tools": [
            ("tools/appointment_tools.py", "tools/appointment_tools.py"),
            ("tools/rag_tools.py",         "tools/rag_tools.py"),
        ],
        "Agents": [
            ("agents/router_agent.py",      "agents/router_agent.py"),
            ("agents/appointment_agent.py", "agents/appointment_agent.py"),
            ("agents/rag_agent.py",         "agents/rag_agent.py"),
            ("agents/summary_agent.py",     "agents/summary_agent.py"),
            ("agents/document_agent.py",    "agents/document_agent.py"),
            ("agents/general_response.py",  "agents/general_response.py"),
        ],
        "Graph": [
            ("graph/workflow.py", "graph/workflow.py"),
        ],
        "Evaluation": [
            ("evaluation/benchmarks.py", "evaluation/benchmarks.py"),
        ],
    }

    total = 0
    done  = 0

    for section, files in sections.items():
        print(f"\n📁 {section}:")
        for label, path in files:
            exists = check_file(path)
            icon   = "✅" if exists else "❌"
            print(f"  {icon} {label}")
            total += 1
            if exists:
                done += 1

    pct = (done / total * 100) if total > 0 else 0
    print(f"\n{'=' * 50}")
    print(f"📈 Progress: {done}/{total} files ({pct:.0f}%)")
    print(f"{'🎉 Project complete!' if done == total else '⏳ Still in progress...'}")

if __name__ == "__main__":
    show_progress()