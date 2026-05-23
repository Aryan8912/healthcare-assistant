"""
modules/document_processor.py — PDF and image processing module.
Extracts text, summarizes content, and analyzes medical documents.
"""
import base64
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types

from backend.config import settings, MEDICAL_DOCS_DIR


class DocumentProcessor:
    """
    Processes uploaded medical documents.
    Supports PDF text extraction and image analysis using Gemini Vision.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.google_api_key)

    # ── PDF Processing ────────────────────────────────────────────────────────

    def extract_text_from_pdf(self, file_path: Path) -> dict:
        """Extract text content from a PDF file."""
        try:
            from pypdf import PdfReader
            reader     = PdfReader(str(file_path))
            pages_text = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append({
                        "page":    i + 1,
                        "content": text.strip(),
                    })

            full_text  = "\n\n".join([p["content"] for p in pages_text])
            word_count = len(full_text.split())

            return {
                "success":    True,
                "file_type":  "PDF",
                "pages":      len(reader.pages),
                "word_count": word_count,
                "text":       full_text,
                "pages_data": pages_text,
                "preview":    full_text[:500] + "..." if len(full_text) > 500 else full_text,
            }

        except Exception as e:
            return {
                "success": False,
                "error":   str(e),
            }

    # ── Image Processing ──────────────────────────────────────────────────────

    def analyze_image(self, file_path: Path, prompt: Optional[str] = None) -> dict:
        """Analyze a medical image using Gemini Vision."""
        try:
            from PIL import Image as PILImage
            img = PILImage.open(str(file_path))

            # Read image bytes
            with open(str(file_path), "rb") as f:
                image_bytes = f.read()

            # Determine media type
            ext = file_path.suffix.lower()
            media_type_map = {
                ".jpg":  "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png":  "image/png",
                ".webp": "image/webp",
            }
            media_type = media_type_map.get(ext, "image/jpeg")

            # Build prompt
            analysis_prompt = prompt or (
                "You are a medical document analyzer. "
                "Analyze this medical image and provide:\n"
                "1. Type of document (lab report, prescription, X-ray, etc.)\n"
                "2. Key findings or information\n"
                "3. Any medications mentioned\n"
                "4. Any test results with values\n"
                "5. Doctor/patient information if visible\n"
                "6. Recommendations or notes\n\n"
                "Be concise and structured."
            )

            # Call Gemini Vision
            response = self.client.models.generate_content(
                model    = settings.gemini_model,
                contents = [
                    types.Part.from_bytes(
                        data      = image_bytes,
                        mime_type = media_type,
                    ),
                    analysis_prompt,
                ],
            )

            return {
                "success":   True,
                "file_type": "Image",
                "format":    img.format,
                "size":      f"{img.width}x{img.height}",
                "analysis":  response.text,
            }

        except Exception as e:
            return {
                "success": False,
                "error":   str(e),
            }

    # ── Document Summarization ────────────────────────────────────────────────

    def summarize_document(self, text: str, doc_type: str = "medical") -> dict:
        """Summarize extracted document text using Gemini."""
        if not text.strip():
            return {
                "success": False,
                "error":   "No text to summarize",
            }

        prompt = (
            f"You are a medical document summarizer.\n\n"
            f"Summarize this {doc_type} document in a clear, structured format:\n\n"
            f"Document Content:\n{text[:3000]}\n\n"
            f"Provide:\n"
            f"1. 📋 Document Type\n"
            f"2. 🔑 Key Information (bullet points)\n"
            f"3. 💊 Medications (if any)\n"
            f"4. 📊 Test Results (if any)\n"
            f"5. ⚠️  Important Alerts or Concerns\n"
            f"6. 📝 Summary in 2-3 sentences\n"
        )

        try:
            response = self.client.models.generate_content(
                model    = settings.gemini_model,
                contents = prompt,
            )
            return {
                "success": True,
                "summary": response.text,
            }
        except Exception as e:
            return {
                "success": False,
                "error":   str(e),
                "summary": (
                    f"Document contains {len(text.split())} words. "
                    f"Preview: {text[:300]}..."
                ),
            }

    # ── Full Pipeline ─────────────────────────────────────────────────────────

    def process_document(self, file_id: str) -> dict:
        """
        Full document processing pipeline.
        Finds file, extracts content, and generates summary.
        """
        # Find file
        ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
        file_path = None

        for ext in ALLOWED_EXTENSIONS:
            path = MEDICAL_DOCS_DIR / f"{file_id}{ext}"
            if path.exists():
                file_path = path
                break

        if not file_path:
            return {
                "success": False,
                "error":   "File not found",
            }

        ext = file_path.suffix.lower()

        # Process based on type
        if ext == ".pdf":
            extraction = self.extract_text_from_pdf(file_path)
            if not extraction["success"]:
                return extraction

            summary = self.summarize_document(extraction["text"])
            return {
                "success":    True,
                "file_id":    file_id,
                "file_type":  "PDF",
                "pages":      extraction["pages"],
                "word_count": extraction["word_count"],
                "preview":    extraction["preview"],
                "summary":    summary.get("summary", "Summary not available"),
            }

        elif ext in {".png", ".jpg", ".jpeg", ".webp"}:
            analysis = self.analyze_image(file_path)
            return {
                "success":   True,
                "file_id":   file_id,
                "file_type": "Image",
                "size":      analysis.get("size"),
                "summary":   analysis.get("analysis", "Analysis not available"),
            }

        return {
            "success": False,
            "error":   "Unsupported file type",
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

document_processor = DocumentProcessor()


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🧪 Testing document processor...")

    # Test with existing txt file as mock
    test_text = """
    Patient: John Doe
    Date: 2026-05-24
    Doctor: Dr. Ananya Krishnan

    Lab Results:
    - Blood Sugar (Fasting): 126 mg/dL (High)
    - HbA1c: 7.2% (Elevated)
    - Blood Pressure: 138/88 mmHg (Pre-hypertension)

    Medications Prescribed:
    - Metformin 500mg twice daily
    - Amlodipine 5mg once daily

    Notes: Patient advised to follow low-sugar diet and exercise 30 min daily.
    Follow-up in 3 months.
    """

    print("✅ Testing summarize_document...")
    result = document_processor.summarize_document(test_text)
    if result["success"]:
        print(f"✅ Summary generated:\n{result['summary'][:300]}...")
    else:
        print(f"⚠️  Summary failed (quota): {result['error'][:100]}")
        print(f"✅ Fallback summary: {result.get('summary', 'N/A')[:200]}")

    print("\n🎉 Document processor test complete!")