"""
tools/rag_tools.py — Tool functions for RAG agent.
These are called by the LangGraph RAG agent.
"""
from typing import Optional
from backend.modules.rag_engine import rag_engine
from backend.modules.memory_manager import memory_manager


# ── Tool 1: Retrieve Documents ────────────────────────────────────────────────

async def retrieve_documents(query: str, top_k: int = 5) -> dict:
    """
    Retrieve relevant document chunks from FAISS index.

    Args:
        query: User's question
        top_k: Number of chunks to retrieve
    Returns:
        Dict with retrieved chunks
    """
    chunks = rag_engine.retrieve(query, top_k=top_k)

    return {
        "query":   query,
        "total":   len(chunks),
        "chunks":  chunks,
    }


# ── Tool 2: Search Knowledge Base ─────────────────────────────────────────────

async def search_knowledge_base(
    query:          str,
    session_id:     Optional[str] = None,
) -> dict:
    """
    Full RAG pipeline — retrieve + generate answer.

    Args:
        query:      User's medical question
        session_id: Optional session ID for conversation context
    Returns:
        Dict with generated answer
    """
    # Get session context if available
    session_context = ""
    if session_id:
        session_context = await memory_manager.format_context(session_id)

    # Generate answer
    answer = rag_engine.query(query, session_context=session_context)

    return {
        "query":   query,
        "answer":  answer,
        "source":  "knowledge_base",
    }


# ── Tool 3: Add Document to Knowledge Base ────────────────────────────────────

async def add_to_knowledge_base(text: str) -> dict:
    """
    Add new document text to the FAISS index.

    Args:
        text: Document text to add
    Returns:
        Dict with number of chunks added
    """
    count = rag_engine.add_document(text)

    return {
        "success":      True,
        "chunks_added": count,
        "message":      f"✅ Added {count} chunks to knowledge base",
    }


# ── Tool 4: Summarize Conversation ───────────────────────────────────────────

async def summarize_conversation(session_id: str) -> dict:
    """
    Summarize the conversation history for a session.

    Args:
        session_id: Session ID to summarize
    Returns:
        Dict with summary
    """
    summary = await memory_manager.get_summary(session_id)
    context = await memory_manager.format_context(session_id)

    if not context:
        return {
            "session_id": session_id,
            "summary":    "No conversation history found.",
        }

    # Use Gemini to generate summary
    try:
        from google import genai
        from backend.config import settings

        client = genai.Client(api_key=settings.google_api_key)
        prompt = f"""Summarize this healthcare conversation in 3-5 bullet points:

{context}

Focus on:
- Main health concerns discussed
- Appointments mentioned
- Key medical information shared
- Action items or next steps
"""
        response = client.models.generate_content(
            model    = settings.gemini_model,
            contents = prompt,
        )
        summary_text = response.text

    except Exception:
        summary_text = f"Conversation with {summary.get('total', 0)} messages using agents: {', '.join(summary.get('agents_used', []))}"

    return {
        "session_id":  session_id,
        "summary":     summary_text,
        "stats":       summary,
    }


# ── Tool Registry ─────────────────────────────────────────────────────────────

RAG_TOOLS = {
    "retrieve_documents":    retrieve_documents,
    "search_knowledge_base": search_knowledge_base,
    "add_to_knowledge_base": add_to_knowledge_base,
    "summarize_conversation": summarize_conversation,
}


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def test():
        print("🧪 Testing RAG tools...")

        # Test retrieve documents
        result = await retrieve_documents("What departments are available?")
        print(f"✅ retrieve_documents: {result['total']} chunks retrieved")
        if result['chunks']:
            print(f"   Preview: {result['chunks'][0][:100]}...")

        # Test summarize conversation (empty session)
        result = await summarize_conversation("test-session-999")
        print(f"✅ summarize_conversation: {result['summary'][:100]}")

        print("\n🎉 RAG tools test complete!")

    asyncio.run(test())