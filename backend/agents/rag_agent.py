"""
agents/rag_agent.py — Handles medical Q&A using RAG pipeline.
Supports multilingual responses.
"""
from typing import Optional
from backend.tools.rag_tools import retrieve_documents, search_knowledge_base
from backend.modules.memory_manager import memory_manager
from backend.config import MULTILINGUAL_INSTRUCTION


async def run(message: str, session_id: Optional[str] = None) -> dict:
    tool_calls = []

    # Step 1 — Retrieve relevant documents
    tool_calls.append({"tool": "retrieve_documents", "status": "calling"})
    retrieval = await retrieve_documents(message)
    tool_calls[-1]["status"] = "done"

    chunks = retrieval.get("chunks", [])

    if not chunks:
        return {
            "response":   (
                "I couldn't find relevant information in our knowledge base. "
                "Please consult a healthcare professional for medical advice."
            ),
            "agent":      "rag_agent",
            "tool_calls": tool_calls,
            "sources":    [],
        }

    # Step 2 — Generate answer with multilingual support
    tool_calls.append({"tool": "search_knowledge_base", "status": "calling"})
    try:
        # Build multilingual prompt
        context = "\n\n".join([f"[{i+1}] {chunk}" for i, chunk in enumerate(chunks)])
        session_context = ""
        if session_id:
            session_context = await memory_manager.format_context(session_id)

        from google import genai
        from backend.config import settings, RAG_SYSTEM_PROMPT

        client = genai.Client(api_key=settings.google_api_key)
        prompt = (
            f"{RAG_SYSTEM_PROMPT}\n\n"
            f"{MULTILINGUAL_INSTRUCTION}\n\n"
        )
        if session_context:
            prompt += f"Recent conversation:\n{session_context}\n\n"
        prompt += f"Context:\n{context}\n\nQuestion: {message}"

        response = client.models.generate_content(
            model    = settings.gemini_model,
            contents = prompt,
        )
        answer = response.text
        tool_calls[-1]["status"] = "done"

    except Exception:
        tool_calls[-1]["status"] = "failed"
        answer = (
            "Here's what I found in our knowledge base:\n\n" +
            "\n\n".join([f"• {chunk[:300]}" for chunk in chunks[:3]])
        )

    if session_id:
        await memory_manager.save_message(
            session_id = session_id,
            role       = "assistant",
            content    = answer,
            agent_used = "rag_agent",
        )

    return {
        "response":   answer,
        "agent":      "rag_agent",
        "tool_calls": tool_calls,
        "sources":    chunks[:3],
    }