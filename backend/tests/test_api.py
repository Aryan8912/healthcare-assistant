"""
tests/test_api.py — Tests for FastAPI endpoints.
Run: pytest backend/tests/test_api.py -v
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_health_check(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_get_doctors(client):
    res = await client.get("/api/doctors")
    assert res.status_code == 200
    data = res.json()
    assert "doctors" in data
    assert data["total"] > 0


@pytest.mark.asyncio
async def test_chat_endpoint(client):
    res = await client.post("/api/chat", json={"message": "Hello"})
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert "response" in data
    assert "agent_used" in data


@pytest.mark.asyncio
async def test_chat_appointment_intent(client):
    res = await client.post("/api/chat", json={"message": "I want to book an appointment"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "appointment"


@pytest.mark.asyncio
async def test_chat_rag_intent(client):
    res = await client.post("/api/chat", json={"message": "What are the symptoms of diabetes?"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "rag"


@pytest.mark.asyncio
async def test_get_slots(client):
    res = await client.get("/api/appointments/slots?doctor_id=1&date=2026-06-02")
    assert res.status_code == 200
    data = res.json()
    assert "available_slots" in data


@pytest.mark.asyncio
async def test_book_appointment(client):
    res = await client.post("/api/appointments/book", json={
        "patient_name":  "Test Patient",
        "patient_phone": "+91-9999999999",
        "doctor_id":     1,
        "date":          "2026-06-02",
        "time_slot":     "9:00 AM",
        "reason":        "Test booking",
    })
    assert res.status_code == 200
    data = res.json()
    assert "appointment_id" in data


@pytest.mark.asyncio
async def test_document_list(client):
    res = await client.get("/api/documents/list")
    assert res.status_code == 200
    assert "documents" in res.json()