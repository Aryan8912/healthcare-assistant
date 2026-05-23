"""
tests/demo_qa.py — Demo medical Q&A using RAG pipeline.
Run: python -m backend.tests.demo_qa
"""
import asyncio
from backend.modules.rag_engine import rag_engine

DEMO_QUESTIONS = [
    "What departments are available in the hospital?",
    "What are the symptoms of diabetes?",
    "How do I book an appointment?",
    "What is the consultation fee for a cardiologist?",
    "What should I do in a medical emergency?",
    "मधुमेह के लक्षण क्या हैं?",  # Hindi
]

def demo_qa():
    print("🎯 Demo: Medical Q&A using RAG Pipeline")
    print("=" * 50)

    rag_engine.ensure_index()
    print(f"✅ Knowledge base loaded: {len(rag_engine.chunks)} chunks\n")

    for question in DEMO_QUESTIONS:
        print(f"❓ Question: {question}")
        chunks = rag_engine.retrieve(question)
        print(f"📄 Retrieved {len(chunks)} relevant chunks")

        try:
            answer = rag_engine.query(question)
            print(f"💬 Answer: {answer[:200]}...")
        except Exception as e:
            print(f"⚠️  Gemini quota exceeded. Showing raw chunks:")
            for i, chunk in enumerate(chunks[:2], 1):
                print(f"   [{i}] {chunk[:150]}...")
        print()

    print("🎉 Demo complete!")

if __name__ == "__main__":
    demo_qa()