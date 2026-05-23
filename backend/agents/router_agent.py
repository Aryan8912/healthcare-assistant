"""
agents/router_agent.py — Routes user queries to the correct agent.
Uses Gemini to classify intent, falls back to keyword matching.
Supports multilingual queries.
"""
from typing import Literal
from google import genai
from backend.config import settings, ROUTER_SYSTEM_PROMPT

Intent = Literal["appointment", "rag", "summary", "document", "general"]

# ── Keyword Fallback ──────────────────────────────────────────────────────────

KEYWORDS = {
    "appointment": [
        # English
        "book", "appointment", "schedule", "cancel", "reschedule",
        "slot", "available", "doctor", "visit", "reserve", "consult",
        "checkup", "check-up", "cardiologist", "neurologist", "pediatrician",
        "gynecologist", "dermatologist", "orthopedic", "psychiatrist",
        # Hindi
        "अपॉइंटमेंट", "डॉक्टर", "बुक", "मिलना", "इलाज",
        # Tamil
        "சந்திப்பு", "மருத்துவர்",
        # Malayalam
        "അപ്പോയിന്റ്മെന്റ്", "ഡോക്ടർ",
    ],
    "rag": [
        # English
        "what is", "how to", "symptoms", "treatment", "medicine",
        "disease", "health", "medical", "pain", "fever", "diabetes",
        "blood pressure", "heart", "explain", "tell me", "cause",
        "prevent", "cure", "diet", "faq", "information about",
        # Hindi
        "क्या है", "लक्षण", "बीमारी", "दवा", "स्वास्थ्य", "दर्द", "इलाज",
        "मधुमेह", "बुखार", "कैसे", "जानकारी",
        # Tamil
        "என்ன", "அறிகுறிகள்", "நோய்", "மருந்து",
        # Malayalam
        "എന്താണ്", "രോഗം", "മരുന്ന്",
    ],
    "summary": [
        # English
        "summarize", "summary", "recap", "history", "what did we discuss",
        # Hindi
        "सारांश", "संक्षेप", "बताओ क्या बात हुई",
    ],
    "document": [
        # English
        "upload", "pdf", "document", "report", "analyze", "scan",
        "prescription", "lab report", "image",
        # Hindi
        "दस्तावेज़", "रिपोर्ट", "अपलोड",
    ],
}


def keyword_intent(message: str) -> Intent:
    """Detect intent using keyword matching — works for multilingual."""
    msg = message.lower()
    for intent, keywords in KEYWORDS.items():
        if any(k in msg for k in keywords):
            return intent
    return "general"


# ── Gemini Router ─────────────────────────────────────────────────────────────

async def route(message: str) -> dict:
    """
    Route a user message to the correct agent.
    Supports multilingual queries via Gemini classification.
    """
    try:
        client = genai.Client(api_key=settings.google_api_key)
        prompt = (
            f"{ROUTER_SYSTEM_PROMPT}\n\n"
            "Note: The message may be in any language including Hindi, Tamil, "
            "Malayalam, Telugu, Kannada, Gujarati, Bengali, or mixed languages. "
            "Still classify into one of the 5 categories.\n\n"
            f"User message: {message}"
        )

        response = client.models.generate_content(
            model    = settings.gemini_model,
            contents = prompt,
        )

        intent = response.text.strip().lower()
        valid_intents = ["appointment", "rag", "summary", "document", "general"]

        if intent not in valid_intents:
            intent = keyword_intent(message)
            source = "keyword_fallback"
        else:
            source = "gemini"

    except Exception:
        intent = keyword_intent(message)
        source = "keyword_fallback"

    return {
        "intent":  intent,
        "source":  source,
        "message": message,
    }


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def test():
        print("🧪 Testing router agent with multilingual support...\n")

        test_messages = [
            "I want to book an appointment with a cardiologist",
            "What are the symptoms of diabetes?",
            "मधुमेह के लक्षण क्या हैं?",          # Hindi
            "டாக்டரை பார்க்க வேண்டும்",           # Tamil
            "ഡോക்ടറെ കാണണം",                      # Malayalam
            "Summarize our conversation",
            "Hello, how are you?",
            "नमस्ते, मुझे मदद चाहिए",              # Hindi greeting
        ]

        for msg in test_messages:
            result = await route(msg)
            print(f"✅ '{msg[:40]}' → {result['intent']} ({result['source']})")

        print("\n🎉 Router agent multilingual test complete!")

    asyncio.run(test())