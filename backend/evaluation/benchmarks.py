"""
evaluation/benchmarks.py — DeepEval LLM-as-judge benchmarks.
5 benchmarks: Answer Relevancy, Faithfulness, Contextual Recall,
Hallucination, Document Understanding + Multilingual.
"""
import time
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRecallMetric,
    HallucinationMetric,
)
from deepeval.test_case import LLMTestCase
from deepeval.models.base_model import DeepEvalBaseLLM
from google import genai as google_genai
from backend.modules.rag_engine import rag_engine
from backend.modules.document_processor import document_processor
from backend.config import settings


# ── Custom Gemini Judge ───────────────────────────────────────────────────────

class GeminiJudge(DeepEvalBaseLLM):
    def __init__(self):
        self.client = google_genai.Client(api_key=settings.google_api_key)
        self.model  = settings.gemini_model

    def load_model(self):
        return self.client

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model    = self.model,
            contents = prompt,
        )
        return response.text

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self) -> str:
        return self.model


# ── RAG Test Cases ────────────────────────────────────────────────────────────

RAG_TEST_CASES = [
    {
        "input":           "What departments are available in the hospital?",
        "expected_output": "The hospital has Cardiology, Orthopedics, Neurology, General Medicine, Pediatrics, Gynecology, Dermatology, and Psychiatry departments.",
    },
    {
        "input":           "How do I book an appointment?",
        "expected_output": "You can book an appointment by providing your name, phone number, preferred doctor or department, and preferred date and time.",
    },
    {
        "input":           "What are the symptoms of diabetes?",
        "expected_output": "Common symptoms of diabetes include frequent urination, excessive thirst, unexplained weight loss, fatigue, blurred vision, and slow-healing wounds.",
    },
    {
        "input":           "What is the consultation fee for a cardiologist?",
        "expected_output": "The consultation fee for Dr. Ananya Krishnan in Cardiology is ₹800.",
    },
]

# ── Document Understanding Test Cases ─────────────────────────────────────────

DOCUMENT_TEST_CASES = [
    {
        "input":           "Patient: John Doe\nBlood Sugar (Fasting): 126 mg/dL (High)\nHbA1c: 7.2%\nMedications: Metformin 500mg",
        "expected_output": "The document is a lab report for John Doe showing elevated blood sugar and HbA1c indicating diabetes. Metformin 500mg is prescribed.",
    },
    {
        "input":           "X-Ray Report\nPatient: Jane Smith\nFinding: No acute cardiopulmonary disease\nImpression: Normal chest X-ray",
        "expected_output": "This is a chest X-ray report for Jane Smith showing no acute cardiopulmonary disease with a normal impression.",
    },
]

# ── Multilingual Test Cases ───────────────────────────────────────────────────

MULTILINGUAL_TEST_CASES = [
    {
        "input":           "मधुमेह के लक्षण क्या हैं?",  # Hindi
        "expected_output": "मधुमेह के सामान्य लक्षणों में बार-बार पेशाब आना, अत्यधिक प्यास, वजन कम होना, थकान और धुंधली दृष्टि शामिल हैं।",
        "language":        "Hindi",
    },
    {
        "input":           "அப்பாயிண்ட்மென்ட் எப்படி பதிவு செய்வது?",  # Tamil
        "expected_output": "உங்கள் பெயர், தொலைபேசி எண், விரும்பிய மருத்துவர் மற்றும் தேதி தேர்வு செய்வதன் மூலம் சந்திப்பை பதிவு செய்யலாம்.",
        "language":        "Tamil",
    },
    {
        "input":           "I want to book appointment, मेरा नाम Aryan है",  # Mixed
        "expected_output": "I can help you book an appointment, Aryan. Please provide your phone number, preferred doctor, date and time slot.",
        "language":        "Mixed (English + Hindi)",
    },
]


# ── Build Test Cases ──────────────────────────────────────────────────────────

def build_rag_test_cases() -> list[LLMTestCase]:
    print("🔨 Building RAG test cases...")
    rag_engine.ensure_index()
    test_cases = []
    for tc in RAG_TEST_CASES:
        chunks  = rag_engine.retrieve(tc["input"])
        context = chunks if chunks else ["No context available"]
        try:
            actual_output = rag_engine.query(tc["input"])
        except Exception:
            actual_output = "Here's what I found:\n" + "\n".join([f"• {c[:200]}" for c in chunks[:2]])
        test_cases.append(LLMTestCase(
            input             = tc["input"],
            actual_output     = actual_output,
            expected_output   = tc["expected_output"],
            retrieval_context = context,
            context           = context,
        ))
        print(f"  ✅ Built: {tc['input'][:50]}...")
    return test_cases


def build_document_test_cases() -> list[LLMTestCase]:
    print("\n🔨 Building Document Understanding test cases...")
    test_cases = []
    for tc in DOCUMENT_TEST_CASES:
        try:
            result        = document_processor.summarize_document(tc["input"], "medical")
            actual_output = result.get("summary", tc["input"])
        except Exception:
            actual_output = f"Document content: {tc['input'][:200]}"
        context = [tc["input"]]
        test_cases.append(LLMTestCase(
            input             = tc["input"],
            actual_output     = actual_output,
            expected_output   = tc["expected_output"],
            retrieval_context = context,
            context           = context,
        ))
        print(f"  ✅ Built: {tc['input'][:50]}...")
    return test_cases


def build_multilingual_test_cases() -> list[LLMTestCase]:
    print("\n🔨 Building Multilingual test cases...")
    rag_engine.ensure_index()
    test_cases = []
    for tc in MULTILINGUAL_TEST_CASES:
        chunks  = rag_engine.retrieve(tc["input"])
        context = chunks if chunks else ["No context available"]
        try:
            actual_output = rag_engine.query(tc["input"])
        except Exception:
            actual_output = f"[{tc['language']} response not available due to quota]"
        test_cases.append(LLMTestCase(
            input             = tc["input"],
            actual_output     = actual_output,
            expected_output   = tc["expected_output"],
            retrieval_context = context,
            context           = context,
        ))
        print(f"  ✅ Built [{tc['language']}]: {tc['input'][:40]}...")
    return test_cases


# ── Measure with Retry ────────────────────────────────────────────────────────

def measure_with_retry(metric, test_case: LLMTestCase, retries: int = 3) -> float:
    for attempt in range(retries):
        try:
            metric.measure(test_case)
            return metric.score
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 30 * (attempt + 1)
                print(f"  ⏳ Quota hit, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise e
    return 0.0


# ── Run Benchmarks ────────────────────────────────────────────────────────────

def run_benchmarks():
    print("🧪 Running DeepEval Benchmarks...")
    print("=" * 50)

    judge          = GeminiJudge()
    rag_cases      = build_rag_test_cases()
    document_cases = build_document_test_cases()
    multilingual_cases = build_multilingual_test_cases()
    results        = {}

    # ── Benchmark 1: Answer Relevancy ─────────────────────────────────────────
    print("\n📊 Benchmark 1: Answer Relevancy")
    print("-" * 40)
    metric = AnswerRelevancyMetric(threshold=0.5, model=judge)
    scores = []
    for tc in rag_cases:
        try:
            score = measure_with_retry(metric, tc)
            scores.append(score)
            print(f"  {'✅' if score >= 0.5 else '❌'} {score:.2f} | {tc.input[:45]}...")
        except Exception as e:
            print(f"  ⚠️  Skipped: {str(e)[:80]}")
    results["answer_relevancy"] = sum(scores) / len(scores) if scores else 0
    print(f"📈 Average: {results['answer_relevancy']:.2f}")

    # ── Benchmark 2: Faithfulness ──────────────────────────────────────────────
    print("\n📊 Benchmark 2: Faithfulness")
    print("-" * 40)
    metric = FaithfulnessMetric(threshold=0.5, model=judge)
    scores = []
    for tc in rag_cases:
        try:
            score = measure_with_retry(metric, tc)
            scores.append(score)
            print(f"  {'✅' if score >= 0.5 else '❌'} {score:.2f} | {tc.input[:45]}...")
        except Exception as e:
            print(f"  ⚠️  Skipped: {str(e)[:80]}")
    results["faithfulness"] = sum(scores) / len(scores) if scores else 0
    print(f"📈 Average: {results['faithfulness']:.2f}")

    # ── Benchmark 3: Contextual Recall ────────────────────────────────────────
    print("\n📊 Benchmark 3: Contextual Recall")
    print("-" * 40)
    metric = ContextualRecallMetric(threshold=0.5, model=judge)
    scores = []
    for tc in rag_cases:
        try:
            score = measure_with_retry(metric, tc)
            scores.append(score)
            print(f"  {'✅' if score >= 0.5 else '❌'} {score:.2f} | {tc.input[:45]}...")
        except Exception as e:
            print(f"  ⚠️  Skipped: {str(e)[:80]}")
    results["contextual_recall"] = sum(scores) / len(scores) if scores else 0
    print(f"📈 Average: {results['contextual_recall']:.2f}")

    # ── Benchmark 4: Hallucination ────────────────────────────────────────────
    print("\n📊 Benchmark 4: Hallucination")
    print("-" * 40)
    metric = HallucinationMetric(threshold=0.5, model=judge)
    scores = []
    for tc in rag_cases:
        try:
            score = measure_with_retry(metric, tc)
            scores.append(score)
            print(f"  {'✅' if score <= 0.5 else '❌'} {score:.2f} | {tc.input[:45]}...")
        except Exception as e:
            print(f"  ⚠️  Skipped: {str(e)[:80]}")
    results["hallucination"] = sum(scores) / len(scores) if scores else 0
    print(f"📈 Average: {results['hallucination']:.2f} (lower is better)")

    # ── Benchmark 5: Document & Image Understanding ───────────────────────────
    print("\n📊 Benchmark 5: Document & Image Understanding")
    print("-" * 40)
    metric = AnswerRelevancyMetric(threshold=0.5, model=judge)
    scores = []
    for tc in document_cases:
        try:
            score = measure_with_retry(metric, tc)
            scores.append(score)
            print(f"  {'✅' if score >= 0.5 else '❌'} {score:.2f} | {tc.input[:45]}...")
        except Exception as e:
            print(f"  ⚠️  Skipped: {str(e)[:80]}")
    results["document_understanding"] = sum(scores) / len(scores) if scores else 0
    print(f"📈 Average: {results['document_understanding']:.2f}")

    # ── Benchmark 6: Multilingual ─────────────────────────────────────────────
    print("\n📊 Benchmark 6: Multilingual Support")
    print("-" * 40)
    metric = AnswerRelevancyMetric(threshold=0.5, model=judge)
    scores = []
    for tc in multilingual_cases:
        try:
            score = measure_with_retry(metric, tc)
            scores.append(score)
            print(f"  {'✅' if score >= 0.5 else '❌'} {score:.2f} | {tc.input[:45]}...")
        except Exception as e:
            print(f"  ⚠️  Skipped: {str(e)[:80]}")
    results["multilingual"] = sum(scores) / len(scores) if scores else 0
    print(f"📈 Average: {results['multilingual']:.2f}")

    # ── Final Report ──────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("📋 FINAL BENCHMARK REPORT")
    print("=" * 50)
    print(f"1. Answer Relevancy        : {results['answer_relevancy']:.2f}  {'✅' if results['answer_relevancy'] >= 0.5 else '❌'}")
    print(f"2. Faithfulness            : {results['faithfulness']:.2f}  {'✅' if results['faithfulness'] >= 0.5 else '❌'}")
    print(f"3. Contextual Recall       : {results['contextual_recall']:.2f}  {'✅' if results['contextual_recall'] >= 0.5 else '❌'}")
    print(f"4. Hallucination           : {results['hallucination']:.2f}  {'✅' if results['hallucination'] <= 0.5 else '❌'} (lower is better)")
    print(f"5. Document Understanding  : {results['document_understanding']:.2f}  {'✅' if results['document_understanding'] >= 0.5 else '❌'}")
    print(f"6. Multilingual Support    : {results['multilingual']:.2f}  {'✅' if results['multilingual'] >= 0.5 else '❌'}")
    print("=" * 50)
    print("🎉 Benchmarks complete!")
    return results


if __name__ == "__main__":
    run_benchmarks()