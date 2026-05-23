"""
api/documents.py — Document upload and analysis endpoints.
Supports PDF and image uploads for medical document analysis.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import os
import shutil
import uuid

from backend.db.database import get_db
from backend.config import MEDICAL_DOCS_DIR

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    file_id:   str
    filename:  str
    file_type: str
    size_kb:   float
    message:   str


# ── Allowed File Types ────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_SIZE_MB   = 10


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db:   AsyncSession = Depends(get_db),
):
    """Upload a medical document (PDF or image)."""

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()

    # Validate file size
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"
        )

    # Generate unique file ID and save
    file_id       = str(uuid.uuid4())
    save_filename = f"{file_id}{ext}"
    save_path     = MEDICAL_DOCS_DIR / save_filename

    with open(save_path, "wb") as f:
        f.write(content)

    return DocumentResponse(
        file_id   = file_id,
        filename  = file.filename,
        file_type = ext.lstrip(".").upper(),
        size_kb   = round(len(content) / 1024, 2),
        message   = "✅ Document uploaded successfully. Ready for analysis.",
    )


@router.post("/documents/analyze/{file_id}")
async def analyze_document(
    file_id: str,
    db:      AsyncSession = Depends(get_db),
):
    """Analyze an uploaded document and extract key information."""

    # Find the file
    matched_file = None
    for ext in ALLOWED_EXTENSIONS:
        path = MEDICAL_DOCS_DIR / f"{file_id}{ext}"
        if path.exists():
            matched_file = path
            break

    if not matched_file:
        raise HTTPException(status_code=404, detail="Document not found")

    ext = matched_file.suffix.lower()

    # ── PDF Analysis ───────────────────────────────────────────────────────
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader   = PdfReader(str(matched_file))
            text     = ""
            for page in reader.pages:
                text += page.extract_text() or ""

            word_count = len(text.split())
            preview    = text[:500] + "..." if len(text) > 500 else text

            return {
                "file_id":    file_id,
                "file_type":  "PDF",
                "pages":      len(reader.pages),
                "word_count": word_count,
                "preview":    preview,
                "message":    "✅ PDF analysed successfully.",
                "status":     "analyzed",
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF analysis failed: {str(e)}")

    # ── Image Analysis ─────────────────────────────────────────────────────
    elif ext in {".png", ".jpg", ".jpeg", ".webp"}:
        try:
            from PIL import Image
            img = Image.open(str(matched_file))

            return {
                "file_id":    file_id,
                "file_type":  "Image",
                "format":     img.format,
                "size":       f"{img.width}x{img.height}",
                "mode":       img.mode,
                "message":    "✅ Image analysed successfully. Use /documents/summarize/{file_id} for AI summary.",
                "status":     "analyzed",
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail="Unsupported file type for analysis")


@router.get("/documents/list")
async def list_documents():
    """List all uploaded documents."""
    files = []
    for f in MEDICAL_DOCS_DIR.iterdir():
        if f.suffix.lower() in ALLOWED_EXTENSIONS:
            size_kb = round(f.stat().st_size / 1024, 2)
            files.append({
                "file_id":   f.stem,
                "filename":  f.name,
                "file_type": f.suffix.lstrip(".").upper(),
                "size_kb":   size_kb,
            })

    return {
        "total":     len(files),
        "documents": files,
    }


@router.delete("/documents/{file_id}")
async def delete_document(file_id: str):
    """Delete an uploaded document."""
    deleted = False
    for ext in ALLOWED_EXTENSIONS:
        path = MEDICAL_DOCS_DIR / f"{file_id}{ext}"
        if path.exists():
            path.unlink()
            deleted = True
            break

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "✅ Document deleted successfully.", "file_id": file_id}