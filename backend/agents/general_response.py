"""
agents/general_response.py — Multilingual general response handler.
"""
from typing import Optional
from backend.config import settings, MULTILINGUAL_INSTRUCTION


async def get_general_response(message: str) -> str:
    """Generate a general response in the user's language using Gemini."""
    try:
        from google import genai
        client = genai.Client(api_key=settings.google_api_key)

        prompt = (
            f"{MULTILINGUAL_INSTRUCTION}\n\n"
            "You are MedAssist, a friendly healthcare assistant.\n"
            "You can help with:\n"
            "• Booking appointments\n"
            "• Answering medical questions\n"
            "• Analyzing medical documents\n"
            "• Summarizing conversations\n\n"
            f"Respond to this message in the same language it was written in:\n{message}"
        )

        response = client.models.generate_content(
            model    = settings.gemini_model,
            contents = prompt,
        )
        return response.text

    except Exception:
        return (
            "Hello! I'm MedAssist, your healthcare assistant. "
            "I can help you:\n"
            "• 📅 Book, cancel, or reschedule appointments\n"
            "• 💊 Answer medical questions\n"
            "• 📋 Summarize your conversation\n"
            "• 📄 Analyze medical documents & images\n\n"
            "How can I help you today?"
        )