"""
modules/rag_engine.py — RAG pipeline using FAISS + Gemini embeddings.
Uses google-genai (new SDK) with REST transport.
"""
import pickle
from pathlib import Path

import faiss
import numpy as np
from google import genai
from google.genai import types

from backend.config import settings, MEDICAL_DOCS_DIR, VECTOR_DB_DIR, RAG_SYSTEM_PROMPT


class RAGEngine:
    """
    Retrieval-Augmented Generation engine.
    1. Loads documents from data/
    2. Chunks and embeds them with Gemini
    3. Stores in FAISS index
    4. Retrieves relevant chunks on query
    5. Generates answer with Gemini
    """

    def __init__(self):
        self.client      = genai.Client(api_key=settings.google_api_key)
        self.index       = None
        self.chunks      = []
        self.index_path  = VECTOR_DB_DIR / "faiss.index"
        self.chunks_path = VECTOR_DB_DIR / "chunks.pkl"

    # ── Document Loading ──────────────────────────────────────────────────────

    def load_documents(self) -> list[str]:
        """Load all .txt and .pdf files from data directory."""
        docs = []

        # Load .txt from rag/data/
        data_dir = Path(__file__).parent.parent / "rag" / "data"
        for file in data_dir.glob("*.txt"):
            try:
                text = file.read_text(encoding="utf-8")
                docs.append(text)
                print(f"  📄 Loaded: {file.name}")
            except Exception as e:
                print(f"  ⚠️  Error loading {file.name}: {e}")

        # Load .txt from medical_docs/
        for file in MEDICAL_DOCS_DIR.glob("*.txt"):
            try:
                text = file.read_text(encoding="utf-8")
                docs.append(text)
                print(f"  📄 Loaded: {file.name}")
            except Exception as e:
                print(f"  ⚠️  Error loading {file.name}: {e}")

        # Load PDFs
        for file in MEDICAL_DOCS_DIR.glob("*.pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(file))
                text   = "".join(page.extract_text() or "" for page in reader.pages)
                if text.strip():
                    docs.append(text)
                    print(f"  📄 Loaded PDF: {file.name}")
            except Exception as e:
                print(f"  ⚠️  Error loading PDF {file.name}: {e}")

        return docs

    # ── Chunking ──────────────────────────────────────────────────────────────

    def chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start  = 0
        while start < len(text):
            end   = min(start + settings.chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += settings.chunk_size - settings.chunk_overlap
        return chunks

    # ── Embeddings ────────────────────────────────────────────────────────────

    def get_embedding(self, text: str) -> list[float]:
        """Get Gemini embedding for a single text."""
        result = self.client.models.embed_content(
            model   = settings.embedding_model,
            contents = text,
        )
        return result.embeddings[0].values

    def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Get Gemini embeddings for a list of texts."""
        return [self.get_embedding(text) for text in texts]

    # ── Build Index ───────────────────────────────────────────────────────────

    def build_index(self) -> None:
        """Build FAISS index from all documents."""
        print("🔨 Building FAISS index...")

        docs = self.load_documents()
        if not docs:
            print("⚠️  No documents found. Add files to rag/data/")
            return

        all_chunks = []
        for doc in docs:
            all_chunks.extend(self.chunk_text(doc))

        print(f"  📝 Total chunks: {len(all_chunks)}")

        all_embeddings = []
        for i, chunk in enumerate(all_chunks):
            embedding = self.get_embedding(chunk)
            all_embeddings.append(embedding)
            if (i + 1) % 10 == 0 or (i + 1) == len(all_chunks):
                print(f"  🔢 Embedded {i + 1}/{len(all_chunks)} chunks")

        # Build FAISS index
        dim    = len(all_embeddings[0])
        index  = faiss.IndexFlatL2(dim)
        matrix = np.array(all_embeddings, dtype=np.float32)
        index.add(matrix)

        # Save to disk
        faiss.write_index(index, str(self.index_path))
        with open(self.chunks_path, "wb") as f:
            pickle.dump(all_chunks, f)

        self.index  = index
        self.chunks = all_chunks
        print(f"✅ FAISS index built with {len(all_chunks)} chunks")

    # ── Load Index ────────────────────────────────────────────────────────────

    def load_index(self) -> bool:
        """Load existing FAISS index from disk."""
        if self.index_path.exists() and self.chunks_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.chunks_path, "rb") as f:
                self.chunks = pickle.load(f)
            print(f"✅ FAISS index loaded: {len(self.chunks)} chunks")
            return True
        return False

    def ensure_index(self) -> None:
        if self.index is None:
            if not self.load_index():
                self.build_index()

    # ── Retrieve ──────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = None) -> list[str]:
        """Retrieve top-k relevant chunks for a query."""
        self.ensure_index()
        if not self.index or not self.chunks:
            return []

        top_k     = top_k or settings.top_k_results
        embedding = self.get_embedding(query)
        vector    = np.array([embedding], dtype=np.float32)

        _, indices = self.index.search(vector, top_k)
        return [
            self.chunks[idx]
            for idx in indices[0]
            if idx != -1 and idx < len(self.chunks)
        ]

    # ── Query ─────────────────────────────────────────────────────────────────

    def query(self, question: str, session_context: str = "") -> str:
        """Full RAG pipeline: retrieve + generate."""
        chunks = self.retrieve(question)

        if not chunks:
            return (
                "I couldn't find relevant information in the knowledge base. "
                "Please consult a healthcare professional for medical advice."
            )

        context = "\n\n".join([f"[{i+1}] {chunk}" for i, chunk in enumerate(chunks)])

        prompt = f"{RAG_SYSTEM_PROMPT}\n\n"
        if session_context:
            prompt += f"Recent conversation:\n{session_context}\n\n"
        prompt += f"Context:\n{context}\n\nQuestion: {question}"

        response = self.client.models.generate_content(
            model    = settings.gemini_model,
            contents = prompt,
        )
        return response.text

    # ── Add Document ──────────────────────────────────────────────────────────

    def add_document(self, text: str) -> int:
        """Add a new document to the existing index."""
        new_chunks = self.chunk_text(text)
        if not new_chunks:
            return 0

        embeddings = self.get_embeddings_batch(new_chunks)
        matrix     = np.array(embeddings, dtype=np.float32)

        self.ensure_index()
        self.index.add(matrix)
        self.chunks.extend(new_chunks)

        faiss.write_index(self.index, str(self.index_path))
        with open(self.chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)

        return len(new_chunks)


# ── Singleton ─────────────────────────────────────────────────────────────────

rag_engine = RAGEngine()


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🧪 Testing RAG engine with Gemini...")

    rag_engine.build_index()

    print("\n🔍 Testing retrieval...")
    chunks = rag_engine.retrieve("What are the symptoms of diabetes?")
    print(f"✅ Retrieved {len(chunks)} chunks")
    if chunks:
        print(f"   Preview: {chunks[0][:200]}...")

    print("\n💬 Testing full RAG query...")
    answer = rag_engine.query("What departments are available in the hospital?")
    print(f"✅ Answer:\n{answer[:500]}")

    print("\n🎉 RAG engine test complete!")