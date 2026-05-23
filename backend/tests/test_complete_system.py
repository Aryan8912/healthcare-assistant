"""
tests/test_complete_system.py — End-to-end system tests.
Run: pytest backend/tests/test_complete_system.py -v
"""
import pytest
import asyncio
from backend.graph.workflow import run_workflow
from backend.modules.memory_manager import memory_manager
from backend.modules.rag_engine import rag_engine


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_full_conversation_flow():
    """Test a complete multi-turn conversation."""
    session_id = "e2e-test-001"

    # Turn 1: Greeting
    r1 = await run_workflow("Hello!", session_id=session_id)
    assert r1["response"] != ""

    # Turn 2: Medical question
    r2 = await run_workflow("What are the symptoms of diabetes?", session_id=session_id)
    assert r2["intent"] == "rag"

    # Turn 3: Appointment
    r3 = await run_workflow("Show me all available doctors", session_id=session_id)
    assert r3["intent"] == "appointment"

    # Turn 4: Summary
    r4 = await run_workflow("Summarize our conversation", session_id=session_id)
    assert r4["intent"] == "summary"

    # Cleanup
    await memory_manager.clear_history(session_id)


@pytest.mark.asyncio
async def test_rag_pipeline_end_to_end():
    """Test complete RAG pipeline."""
    rag_engine.ensure_index()
    chunks = rag_engine.retrieve("What departments are available?")
    assert len(chunks) > 0


@pytest.mark.asyncio
async def test_multilingual_routing():
    """Test multilingual message routing."""
    # Hindi
    r1 = await run_workflow("मधुमेह के लक्षण क्या हैं?")
    assert r1["intent"] == "rag"

    # Hindi appointment
    r2 = await run_workflow("डॉक्टर से मिलना है")
    assert r2["intent"] in ["appointment", "general"]


@pytest.mark.asyncio
async def test_document_agent_flow():
    """Test document agent with invalid file."""
    result = await run_workflow("Analyze this document", file_id="invalid-123")
    assert result["agent_used"] == "document_agent"
    assert result["response"] != ""