"""
tests/check_config.py — Verify all configuration settings are correct.
Run: python -m backend.tests.check_config
"""
from backend.config import settings, SAMPLE_DOCTORS, DATA_DIR, MEDICAL_DOCS_DIR, VECTOR_DB_DIR, DATABASE_PATH

def check_config():
    print("🔍 Checking configuration...\n")

    checks = [
        ("Google API Key",     bool(settings.google_api_key),     settings.google_api_key[:20] + "..."),
        ("Gemini Model",       bool(settings.gemini_model),       settings.gemini_model),
        ("Embedding Model",    bool(settings.embedding_model),    settings.embedding_model),
        ("Database URL",       bool(settings.database_url),       settings.database_url),
        ("CORS Origins",       bool(settings.cors_origins),       settings.cors_origins),
        ("Data DIR exists",    DATA_DIR.exists(),                 str(DATA_DIR)),
        ("Medical Docs exists",MEDICAL_DOCS_DIR.exists(),         str(MEDICAL_DOCS_DIR)),
        ("Vector DB exists",   VECTOR_DB_DIR.exists(),            str(VECTOR_DB_DIR)),
        ("Sample Doctors",     len(SAMPLE_DOCTORS) > 0,          f"{len(SAMPLE_DOCTORS)} doctors"),
    ]

    all_pass = True
    for name, status, value in checks:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}: {value}")
        if not status:
            all_pass = False

    print(f"\n{'✅ All checks passed!' if all_pass else '❌ Some checks failed!'}")
    return all_pass

if __name__ == "__main__":
    check_config()