"""
tests/test_scheduler.py — Tests for appointment scheduler.
Run: pytest backend/tests/test_scheduler.py -v
"""
import pytest
import asyncio
from backend.modules.scheduler import scheduler


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_get_all_doctors():
    doctors = await scheduler.get_all_doctors()
    assert len(doctors) > 0
    assert "name" in doctors[0]
    assert "department" in doctors[0]


@pytest.mark.asyncio
async def test_get_doctor_by_department():
    doctors = await scheduler.get_doctor_by_department("Cardiology")
    assert len(doctors) > 0
    assert doctors[0]["department"] == "Cardiology"


@pytest.mark.asyncio
async def test_get_available_slots():
    result = await scheduler.get_available_slots(1, "2026-06-02")
    assert "available_slots" in result or "message" in result


@pytest.mark.asyncio
async def test_get_or_create_patient():
    patient = await scheduler.get_or_create_patient(
        name  = "Test User",
        phone = "+91-8888888888",
        email = "test@test.com"
    )
    assert patient["name"] == "Test User"
    assert patient["phone"] == "+91-8888888888"


@pytest.mark.asyncio
async def test_book_and_cancel_appointment():
    # Book
    result = await scheduler.book_appointment(
        patient_name  = "Test Patient",
        patient_phone = "+91-7777777777",
        doctor_id     = 1,
        date_str      = "2026-06-03",
        time_slot     = "9:30 AM",
        reason        = "Test",
    )
    assert result["success"] is True
    apt_id = result["appointment_id"]

    # Cancel
    cancel = await scheduler.cancel_appointment(apt_id)
    assert cancel["success"] is True


@pytest.mark.asyncio
async def test_patient_appointments():
    result = await scheduler.get_patient_appointments("+91-9876543210")
    assert result["success"] is True
    assert "appointments" in result