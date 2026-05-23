"""
tests/test_rag.py — Tests for RAG pipeline.
Run: pytest backend/tests/test_rag.py -v
"""
import pytest
from backend.modules.rag_engine import rag_engine


def test_index_loads():
    rag_engine.ensure_index()
    assert rag_engine.index is not None
    assert len(rag_engine.chunks) > 0


def test_chunk_text():
    text   = "A" * 1000
    chunks = rag_engine.chunk_text(text)
    assert len(chunks) > 0
    assert all(len(c) <= 500 for c in chunks)


def test_retrieve_returns_chunks():
    chunks = rag_engine.retrieve("What departments are available?")
    assert isinstance(chunks, list)
    assert len(chunks) > 0


def test_retrieve_relevant_content():
    chunks = rag_engine.retrieve("diabetes symptoms treatment")
    assert len(chunks) > 0
    # At least one chunk should mention health-related content
    all_text = " ".join(chunks).lower()
    assert any(word in all_text for word in ["diabetes", "health", "medical", "doctor", "hospital"])


def test_add_document():
    test_text  = "This is a test medical document about headaches and migraines."
    chunks_added = rag_engine.add_document(test_text)
    assert chunks_added > 0