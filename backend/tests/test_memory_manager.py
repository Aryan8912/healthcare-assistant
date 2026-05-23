"""
tests/test_memory_manager.py — Tests for conversation memory.
Run: pytest backend/tests/test_memory_manager.py -v
"""
import pytest
import asyncio
from backend.modules.memory_manager import memory_manager


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

SESSION_ID = "test-memory-session-001"


@pytest.mark.asyncio
async def test_save_message():
    await memory_manager.save_message(SESSION_ID, "user", "Hello doctor")
    history = await memory_manager.get_history(SESSION_ID)
    assert len(history) >= 1


@pytest.mark.asyncio
async def test_get_history():
    await memory_manager.save_message(SESSION_ID, "assistant", "Hello! How can I help?", "general")
    history = await memory_manager.get_history(SESSION_ID)
    assert len(history) >= 2
    assert history[0]["role"] in ["user", "assistant"]


@pytest.mark.asyncio
async def test_get_messages_for_llm():
    msgs = await memory_manager.get_messages_for_llm(SESSION_ID)
    assert isinstance(msgs, list)
    assert all("role" in m and "content" in m for m in msgs)


@pytest.mark.asyncio
async def test_get_summary():
    summary = await memory_manager.get_summary(SESSION_ID)
    assert "total" in summary
    assert summary["total"] >= 2


@pytest.mark.asyncio
async def test_format_context():
    context = await memory_manager.format_context(SESSION_ID)
    assert isinstance(context, str)
    assert len(context) > 0


@pytest.mark.asyncio
async def test_clear_history():
    count = await memory_manager.clear_history(SESSION_ID)
    assert count >= 2
    history = await memory_manager.get_history(SESSION_ID)
    assert len(history) == 0