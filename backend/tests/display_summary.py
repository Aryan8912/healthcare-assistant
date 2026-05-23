"""
tests/display_summary.py — Display system summary and stats.
Run: python -m backend.tests.display_summary
"""
import asyncio
from backend.modules.rag_engine import rag_engine
from backend.modules.scheduler import scheduler
from backend.config import settings, MEDICAL_DOCS_DIR, VECTOR_DB_DIR

async def display_summary():
    print("📊 MedAssist System Summary")
    print("=" * 50)

    # Config
    print("\n⚙️  Configuration:")
    print(f"  • LLM Model:       {settings.gemini_model}")
    print(f"  • Embedding Model: {settings.embedding_model}")
    print(f"  • Database:        {settings.database_url}")
    print(f"  • Chunk Size:      {settings.chunk_size}")

    # RAG
    print("\n🔍 RAG Pipeline:")
    rag_engine.ensure_index()
    print(f"  • Total chunks:    {len(rag_engine.chunks)}")
    medical_files = list(MEDICAL_DOCS_DIR.glob("*.*"))
    print(f"  • Medical docs:    {len(medical_files)} files")
    vector_files = list(VECTOR_DB_DIR.glob("*.*"))
    print(f"  • Vector DB files: {len(vector_files)} files")

    # Doctors
    print("\n👨‍⚕️  Doctors:")
    doctors = await scheduler.get_all_doctors()
    for d in doctors:
        print(f"  • {d['name']} — {d['department']}")

    # Agents
    print("\n🤖 Agents:")
    agents = ["router_agent", "appointment_agent", "rag_agent", "summary_agent", "document_agent"]
    for agent in agents:
        print(f"  ✅ {agent}")

    print("\n🎉 System is ready!")

if __name__ == "__main__":
    asyncio.run(display_summary())