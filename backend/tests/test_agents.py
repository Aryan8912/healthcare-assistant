"""
tests/test_agents.py — Tests for all agents and workflow.
Run: pytest backend/tests/test_agents.py -v
"""
import pytest
import asyncio
from backend.agents.router_agent import route, keyword_intent
from backend.agents import appointment_agent, rag_agent, summary_agent, document_agent
from backend.graph.workflow import run_workflow


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Router Agent Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_router_appointment_intent():
    result = await route("I want to book an appointment")
    assert result["intent"] == "appointment"


@pytest.mark.asyncio
async def test_router_rag_intent():
    result = await route("What are the symptoms of diabetes?")
    assert result["intent"] == "rag"


@pytest.mark.asyncio
async def test_router_summary_intent():
    result = await route("Summarize our conversation")
    assert result["intent"] == "summary"


@pytest.mark.asyncio
async def test_router_document_intent():
    result = await route("I want to upload my lab report")
    assert result["intent"] == "document"


def test_keyword_intent_hindi():
    assert keyword_intent("मधुमेह के लक्षण क्या हैं?") == "rag"


def test_keyword_intent_appointment():
    assert keyword_intent("book appointment with cardiologist") == "appointment"


# ── Appointment Agent Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_appointment_agent_get_doctors():
    result = await appointment_agent.run("Show me all doctors")
    assert result["agent"] == "appointment_agent"
    assert len(result["tool_calls"]) > 0


@pytest.mark.asyncio
async def test_appointment_agent_history():
    result = await appointment_agent.run("Show my appointments for +91-9876543210")
    assert result["agent"] == "appointment_agent"


# ── RAG Agent Tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rag_agent_returns_response():
    result = await rag_agent.run("What departments are available?")
    assert result["agent"] == "rag_agent"
    assert len(result["response"]) > 0


# ── Document Agent Tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_document_agent_no_file():
    result = await document_agent.run("Analyze my document")
    assert result["agent"] == "document_agent"
    assert "upload" in result["response"].lower()


# ── Workflow Tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_workflow_general():
    result = await run_workflow("Hello!")
    assert "response" in result
    assert result["agent_used"] == "general"


@pytest.mark.asyncio
async def test_workflow_appointment():
    result = await run_workflow("Show me all available doctors")
    assert result["intent"] == "appointment"


@pytest.mark.asyncio
async def test_workflow_with_session():
    result1 = await run_workflow("Hello", session_id="test-wf-001")
    result2 = await run_workflow("What doctors are available?", session_id="test-wf-001")
    assert result1["response"] != ""
    assert result2["intent"] == "appointment"