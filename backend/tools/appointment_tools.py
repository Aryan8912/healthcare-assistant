"""
tools/appointment_tools.py — Tool functions for appointment agent.
These are called by the LangGraph appointment agent.
"""
from typing import Optional
from backend.modules.scheduler import scheduler


# ── Tool 1: Fetch Available Slots ─────────────────────────────────────────────

async def fetch_slots(doctor_id: int, date: str) -> dict:
    """
    Fetch available appointment slots for a doctor on a given date.
    
    Args:
        doctor_id: Doctor's ID
        date: Date in YYYY-MM-DD format
    Returns:
        Dict with available slots
    """
    return await scheduler.get_available_slots(doctor_id, date)


# ── Tool 2: Book Appointment ──────────────────────────────────────────────────

async def book_appointment(
    patient_name:  str,
    patient_phone: str,
    doctor_id:     int,
    date:          str,
    time_slot:     str,
    reason:        Optional[str] = None,
    patient_email: Optional[str] = None,
) -> dict:
    """
    Book a new appointment.

    Args:
        patient_name:  Full name of patient
        patient_phone: Phone number of patient
        doctor_id:     Doctor's ID
        date:          Date in YYYY-MM-DD format
        time_slot:     Time slot e.g. "10:00 AM"
        reason:        Reason for appointment
        patient_email: Optional email
    Returns:
        Dict with booking confirmation
    """
    return await scheduler.book_appointment(
        patient_name  = patient_name,
        patient_phone = patient_phone,
        doctor_id     = doctor_id,
        date_str      = date,
        time_slot     = time_slot,
        reason        = reason,
        patient_email = patient_email,
    )


# ── Tool 3: Cancel Appointment ────────────────────────────────────────────────

async def cancel_appointment(appointment_id: int) -> dict:
    """
    Cancel an existing appointment.

    Args:
        appointment_id: ID of the appointment to cancel
    Returns:
        Dict with cancellation confirmation
    """
    return await scheduler.cancel_appointment(appointment_id)


# ── Tool 4: Modify Appointment ────────────────────────────────────────────────

async def modify_appointment(
    appointment_id: int,
    new_date:       str,
    new_time_slot:  str,
) -> dict:
    """
    Reschedule an existing appointment.

    Args:
        appointment_id: ID of the appointment to reschedule
        new_date:       New date in YYYY-MM-DD format
        new_time_slot:  New time slot e.g. "11:00 AM"
    Returns:
        Dict with reschedule confirmation
    """
    return await scheduler.reschedule_appointment(
        appointment_id = appointment_id,
        new_date       = new_date,
        new_time_slot  = new_time_slot,
    )


# ── Tool 5: Get Appointment History ──────────────────────────────────────────

async def retrieve_appointments(phone: str) -> dict:
    """
    Get appointment history for a patient by phone number.

    Args:
        phone: Patient's phone number
    Returns:
        Dict with appointment history
    """
    return await scheduler.get_patient_appointments(phone)


# ── Tool 6: Get All Doctors ───────────────────────────────────────────────────

async def get_doctors(department: Optional[str] = None) -> dict:
    """
    Get list of all doctors, optionally filtered by department.

    Args:
        department: Optional department name to filter
    Returns:
        Dict with list of doctors
    """
    if department:
        doctors = await scheduler.get_doctor_by_department(department)
    else:
        doctors = await scheduler.get_all_doctors()

    return {
        "total":   len(doctors),
        "doctors": doctors,
    }


# ── Tool Registry ─────────────────────────────────────────────────────────────

APPOINTMENT_TOOLS = {
    "fetch_slots":           fetch_slots,
    "book_appointment":      book_appointment,
    "cancel_appointment":    cancel_appointment,
    "modify_appointment":    modify_appointment,
    "retrieve_appointments": retrieve_appointments,
    "get_doctors":           get_doctors,
}


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def test():
        print("🧪 Testing appointment tools...")

        # Test get doctors
        result = await get_doctors()
        print(f"✅ get_doctors: {result['total']} doctors found")

        # Test get doctors by department
        result = await get_doctors("Cardiology")
        print(f"✅ get_doctors(Cardiology): {result['total']} doctors found")

        # Test fetch slots
        from datetime import datetime, timedelta
        next_monday = datetime.now()
        while next_monday.strftime("%a") != "Mon":
            next_monday += timedelta(days=1)
        date_str = next_monday.strftime("%Y-%m-%d")

        slots = await fetch_slots(1, date_str)
        print(f"✅ fetch_slots: {slots.get('total_available', 0)} slots on {date_str}")

        # Test retrieve appointments
        history = await retrieve_appointments("+91-9876543210")
        print(f"✅ retrieve_appointments: {history.get('total', 0)} appointments")

        print("\n🎉 Appointment tools test complete!")

    asyncio.run(test())