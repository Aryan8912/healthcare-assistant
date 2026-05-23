"""
config.py — Centralised settings for Healthcare Assistant.
Uses Google Gemini for LLM and embeddings.
"""
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Base Paths ────────────────────────────────────────────────────────────────

BASE_DIR         = Path(__file__).parent
DATA_DIR         = BASE_DIR / "rag" / "data"
MEDICAL_DOCS_DIR = DATA_DIR / "medical_docs"
VECTOR_DB_DIR    = DATA_DIR / "vector_db"
DATABASE_PATH    = BASE_DIR / "healthcare.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDICAL_DOCS_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)


# ── Settings ──────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM — Gemini
    google_api_key:  str = ""
    gemini_model:    str = "models/gemini-2.0-flash-lite"
    embedding_model: str = "models/gemini-embedding-001"
    temperature:     float = 0.1

    # Database
    database_url: str = f"sqlite+aiosqlite:///{DATABASE_PATH}"

    # RAG
    faiss_index_path: str = str(VECTOR_DB_DIR)
    chunk_size:       int = 500
    chunk_overlap:    int = 50
    top_k_results:    int = 5

    # App
    app_env:      str = "development"
    log_level:    str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # Appointment
    default_appointment_duration: int = 30
    timezone:                     str = "Asia/Kolkata"
    booking_advance_days:         int = 30

    # Conversation
    max_conversation_history: int = 50
    context_window_messages:  int = 10

    # Admin
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # Feature Flags
    enable_notifications: bool = False
    enable_analytics:     bool = True
    debug_mode:           bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


# ── System Prompts ────────────────────────────────────────────────────────────

RAG_SYSTEM_PROMPT = """You are a medical education assistant for a healthcare clinic.

Your role is to:
1. Answer questions using ONLY the provided medical documents
2. Always cite sources using [1], [2] format
3. Be clear, accurate, and compassionate
4. If information is not in the documents, say so clearly
5. Never provide medical diagnosis or treatment advice
6. Encourage users to consult healthcare professionals

Format your answers:
- Clear, concise explanation
- Bullet points when appropriate
- Inline citations [1], [2]
- List sources at the end

Remember: Educational only, not a replacement for medical professionals.
"""

SCHEDULER_SYSTEM_PROMPT = """You are an appointment scheduling assistant for a healthcare clinic.

Your role is to:
1. Help patients find available appointment slots
2. Check for scheduling conflicts before booking
3. Confirm booking details clearly
4. Be helpful and empathetic
5. Extract: patient name, phone, date, time, department, doctor

Standard appointment duration: 30 minutes
"""

ROUTER_SYSTEM_PROMPT = """You are a healthcare assistant router.

Classify the user query into ONE of these categories:
- appointment  : booking, cancelling, rescheduling, viewing appointments
- rag          : medical questions, health information, FAQs
- summary      : summarize conversation or history
- document     : upload, analyze PDF or image
- general      : greetings, small talk, out of scope

Respond with ONLY the category word.
"""


# ── Sample Doctors (Seed Data) ────────────────────────────────────────────────

SAMPLE_DOCTORS = [
    {
        "name":           "Dr. Ananya Krishnan",
        "department":     "Cardiology",
        "specialization": "Interventional Cardiology, Heart Failure",
        "experience":     18,
        "available_days": "Mon,Wed,Fri",
        "available_time": "09:00-13:00",
        "fee":            800,
        "languages":      "English,Hindi,Malayalam",
    },
    {
        "name":           "Dr. Rajesh Gupta",
        "department":     "Orthopedics",
        "specialization": "Knee & Hip Replacement, Sports Injuries",
        "experience":     20,
        "available_days": "Mon,Tue,Wed,Thu,Fri,Sat",
        "available_time": "10:00-12:30",
        "fee":            900,
        "languages":      "English,Hindi",
    },
    {
        "name":           "Dr. Meera Pillai",
        "department":     "Neurology",
        "specialization": "Epilepsy, Stroke, Headache",
        "experience":     15,
        "available_days": "Tue,Thu,Sat",
        "available_time": "09:00-12:00",
        "fee":            850,
        "languages":      "English,Hindi,Malayalam",
    },
    {
        "name":           "Dr. Priya Iyer",
        "department":     "General Medicine",
        "specialization": "Diabetes, Hypertension, Thyroid",
        "experience":     11,
        "available_days": "Mon,Tue,Wed,Thu,Fri,Sat",
        "available_time": "09:00-17:00",
        "fee":            500,
        "languages":      "English,Hindi,Tamil",
    },
    {
        "name":           "Dr. Arjun Nambiar",
        "department":     "Pediatrics",
        "specialization": "Newborn Care, Childhood Infections, Vaccination",
        "experience":     14,
        "available_days": "Mon,Tue,Wed,Thu,Fri,Sat",
        "available_time": "09:00-11:30",
        "fee":            600,
        "languages":      "English,Hindi,Malayalam",
    },
    {
        "name":           "Dr. Nalini Krishnamurthy",
        "department":     "Gynecology",
        "specialization": "High-Risk Pregnancy, PCOS, Infertility",
        "experience":     17,
        "available_days": "Mon,Wed,Fri",
        "available_time": "10:00-14:00",
        "fee":            800,
        "languages":      "English,Hindi,Kannada",
    },
    {
        "name":           "Dr. Rohan Shah",
        "department":     "Dermatology",
        "specialization": "Acne, Psoriasis, Hair Loss, Laser Treatments",
        "experience":     8,
        "available_days": "Tue,Thu,Sat",
        "available_time": "11:00-16:00",
        "fee":            650,
        "languages":      "English,Hindi,Gujarati",
    },
    {
        "name":           "Dr. Arun Nair",
        "department":     "Psychiatry",
        "specialization": "Depression, Anxiety, Bipolar Disorder",
        "experience":     12,
        "available_days": "Mon,Wed,Fri",
        "available_time": "14:00-18:00",
        "fee":            900,
        "languages":      "English,Hindi,Malayalam",
    },
]


# ── Validate Config ───────────────────────────────────────────────────────────

def validate_config():
    """Validate required environment variables."""
    missing = []
    if not settings.google_api_key:
        missing.append("GOOGLE_API_KEY")
    if missing:
        raise ValueError(f"Missing required env variables: {', '.join(missing)}")
    print("✅ Configuration validated successfully")
    return True


if __name__ == "__main__":
    validate_config()
    print(f"📁 Data directory   : {DATA_DIR}")
    print(f"📚 Medical docs     : {MEDICAL_DOCS_DIR}")
    print(f"🗄️  Database         : {DATABASE_PATH}")
    print(f"🔍 Vector DB        : {VECTOR_DB_DIR}")
    print(f"🤖 Gemini model     : {settings.gemini_model}")
    print(f"🔢 Embedding model  : {settings.embedding_model}")


# ── Multilingual Support ──────────────────────────────────────────────────────

MULTILINGUAL_INSTRUCTION = """
🌐 MULTILINGUAL SUPPORT:
- Detect the language of the user's message automatically
- Always respond in the SAME language the user used
- If the user mixes languages (e.g. Hindi + English), respond in the dominant language
- Supported languages include: English, Hindi, Tamil, Telugu, Malayalam, Kannada, Gujarati, Bengali, Marathi, Punjabi, and others
- For medical terms, you may keep them in English even when responding in another language
- Be natural and fluent in the detected language
"""