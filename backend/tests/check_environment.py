"""
tests/check_environment.py — Check Python environment and dependencies.
Run: python -m backend.tests.check_environment
"""
import sys
import importlib

REQUIRED_PACKAGES = [
    "fastapi", "uvicorn", "sqlalchemy", "aiosqlite",
    "langgraph", "langchain", "faiss", "numpy",
    "google.genai", "pypdf", "PIL", "deepeval",
    "pydantic", "pydantic_settings",
]

def check_environment():
    print("🔍 Checking environment...\n")
    print(f"✅ Python version: {sys.version}")
    print()

    all_pass = True
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            print(f"✅ {pkg}")
        except ImportError:
            print(f"❌ {pkg} — NOT INSTALLED")
            all_pass = False

    print(f"\n{'✅ Environment ready!' if all_pass else '❌ Some packages missing. Run: pip install -r requirements.txt'}")
    return all_pass

if __name__ == "__main__":
    check_environment()