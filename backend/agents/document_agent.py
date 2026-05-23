"""
agents/document_agent.py — Handles document upload and analysis.
Processes PDFs and images using Gemini Vision.
"""
from typing import Optional
from backend.modules.document_processor import document_processor
from backend.modules.rag_engine import rag_engine


# ── Document Agent ────────────────────────────────────────────────────────────

async def run(message: str, session_id: Optional[str] = None, file_id: Optional[str] = None) -> dict:
    """
    Main document agent handler.

    Args:
        message:    User message
        session_id: Session ID for context
        file_id:    ID of uploaded file to analyze
    Returns:
        Dict with response and tool calls
    """
    tool_calls = []

    # ── No file uploaded ──────────────────────────────────────────────────────
    if not file_id:
        return {
            "response": (
                "📄 I can analyze medical documents for you!\n\n"
                "Please upload a document using the upload button. I support:\n"
                "• 📋 PDF lab reports\n"
                "• 🖼️  Medical images (PNG, JPG)\n"
                "• 💊 Prescription documents\n"
                "• 📊 Test result reports\n\n"
                "Once uploaded, I'll extract key information and provide a summary."
            ),
            "agent":      "document_agent",
            "tool_calls": tool_calls,
        }

    # ── Process document ──────────────────────────────────────────────────────
    tool_calls.append({"tool": "process_document", "status": "calling"})
    result = document_processor.process_document(file_id)
    tool_calls[-1]["status"] = "done"

    if not result.get("success"):
        return {
            "response":   f"❌ Could not process document: {result.get('error')}",
            "agent":      "document_agent",
            "tool_calls": tool_calls,
        }

    # ── Add to knowledge base ─────────────────────────────────────────────────
    summary = result.get("summary", "")
    if summary and len(summary) > 50:
        tool_calls.append({"tool": "add_to_knowledge_base", "status": "calling"})
        chunks_added = rag_engine.add_document(summary)
        tool_calls[-1]["status"] = "done"
    else:
        chunks_added = 0

    # ── Build response ────────────────────────────────────────────────────────
    file_type = result.get("file_type", "Document")

    if file_type == "PDF":
        response = (
            f"📋 **PDF Analysis Complete**\n\n"
            f"• Pages: {result.get('pages', 'N/A')}\n"
            f"• Words: {result.get('word_count', 'N/A')}\n\n"
            f"**Summary:**\n{summary}\n\n"
            f"📚 Document added to knowledge base ({chunks_added} chunks)."
        )
    else:
        response = (
            f"🖼️  **Image Analysis Complete**\n\n"
            f"• Size: {result.get('size', 'N/A')}\n\n"
            f"**Analysis:**\n{summary}\n\n"
            f"📚 Analysis added to knowledge base ({chunks_added} chunks)."
        )

    return {
        "response":   response,
        "agent":      "document_agent",
        "tool_calls": tool_calls,
        "result":     result,
    }


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def test():
        print("🧪 Testing document agent...\n")

        # Test without file
        print("👤 User: Can you analyze my lab report?")
        result = await run("Can you analyze my lab report?")
        print(f"🤖 Agent: {result['response'][:200]}")
        print(f"🔧 Tools: {[t['tool'] for t in result['tool_calls']]}")
        print()

        # Test with invalid file_id
        print("👤 User: Analyze document (invalid ID)")
        result = await run("Analyze this document", file_id="invalid-id-123")
        print(f"🤖 Agent: {result['response'][:200]}")
        print(f"🔧 Tools: {[t['tool'] for t in result['tool_calls']]}")
        print()

        print("🎉 Document agent test complete!")

    asyncio.run(test())