"""
api/appointments.py — Appointment CRUD endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime, timedelta

from backend.db.database import get_db
from backend.db.models import Appointment, Patient, Doctor, AppointmentStatus

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class BookAppointmentRequest(BaseModel):
    patient_name:  str
    patient_phone: str
    patient_email: Optional[str] = None
    doctor_id:     int
    date:          str        # YYYY-MM-DD
    time_slot:     str        # e.g. "10:00 AM"
    reason:        Optional[str] = None


class ModifyAppointmentRequest(BaseModel):
    date:      Optional[str] = None
    time_slot: Optional[str] = None
    reason:    Optional[str] = None


class AppointmentResponse(BaseModel):
    id:          int
    patient_name: str
    doctor_name:  str
    department:   str
    date:         str
    time_slot:    str
    status:       str
    reason:       Optional[str]

    class Config:
        from_attributes = True


# ── Helper: Get or Create Patient ─────────────────────────────────────────────

async def get_or_create_patient(
    db: AsyncSession,
    name: str,
    phone: str,
    email: Optional[str] = None
) -> Patient:
    result = await db.execute(
        select(Patient).where(Patient.phone == phone)
    )
    patient = result.scalars().first()

    if not patient:
        patient = Patient(name=name, phone=phone, email=email)
        db.add(patient)
        await db.flush()

    return patient


# ── Helper: Generate Time Slots ───────────────────────────────────────────────

def generate_time_slots(available_time: str) -> list[str]:
    """Generate 30-min slots from a time range like '09:00-13:00'."""
    try:
        start_str, end_str = available_time.split("-")
        start = datetime.strptime(start_str.strip(), "%H:%M")
        end   = datetime.strptime(end_str.strip(),   "%H:%M")
        slots = []
        current = start
        while current < end:
            slots.append(current.strftime("%I:%M %p").lstrip("0"))
            current += timedelta(minutes=30)
        return slots
    except Exception:
        return ["09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
                "11:00 AM", "11:30 AM", "02:00 PM", "02:30 PM",
                "03:00 PM", "03:30 PM"]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/appointments/slots")
async def fetch_slots(
    doctor_id: int,
    date:      str,
    db:        AsyncSession = Depends(get_db)
):
    """Fetch available time slots for a doctor on a given date."""

    # Get doctor
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Check doctor availability on this day
    day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%a")  # Mon, Tue...
    available_days = doctor.available_days.split(",") if doctor.available_days else []

    if day_name not in available_days:
        return {
            "doctor":          doctor.name,
            "date":            date,
            "available_slots": [],
            "message":         f"Dr. {doctor.name} is not available on {day_name}",
        }

    # Get all slots
    all_slots = generate_time_slots(doctor.available_time or "09:00-17:00")

    # Remove already booked slots
    booked = await db.execute(
        select(Appointment.time_slot).where(
            Appointment.doctor_id == doctor_id,
            Appointment.date      == date,
            Appointment.status    == AppointmentStatus.SCHEDULED,
        )
    )
    booked_slots = {row[0] for row in booked.fetchall()}
    available    = [s for s in all_slots if s not in booked_slots]

    return {
        "doctor":          doctor.name,
        "department":      doctor.department,
        "date":            date,
        "available_slots": available,
        "booked_slots":    list(booked_slots),
    }


@router.post("/appointments/book")
async def book_appointment(
    req: BookAppointmentRequest,
    db:  AsyncSession = Depends(get_db)
):
    """Book a new appointment."""

    # Get doctor
    result = await db.execute(select(Doctor).where(Doctor.id == req.doctor_id))
    doctor = result.scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Check slot is still available
    existing = await db.execute(
        select(Appointment).where(
            Appointment.doctor_id == req.doctor_id,
            Appointment.date      == req.date,
            Appointment.time_slot == req.time_slot,
            Appointment.status    == AppointmentStatus.SCHEDULED,
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="This slot is already booked")

    # Get or create patient
    patient = await get_or_create_patient(
        db, req.patient_name, req.patient_phone, req.patient_email
    )

    # Create appointment
    appointment = Appointment(
        patient_id = patient.id,
        doctor_id  = req.doctor_id,
        department = doctor.department,
        date       = req.date,
        time_slot  = req.time_slot,
        reason     = req.reason,
        status     = AppointmentStatus.SCHEDULED,
    )
    db.add(appointment)
    await db.flush()

    return {
        "message":        "✅ Appointment booked successfully!",
        "appointment_id": appointment.id,
        "patient":        patient.name,
        "doctor":         doctor.name,
        "department":     doctor.department,
        "date":           req.date,
        "time_slot":      req.time_slot,
        "status":         "scheduled",
    }


@router.get("/appointments/{appointment_id}")
async def get_appointment(
    appointment_id: int,
    db:             AsyncSession = Depends(get_db)
):
    """Get a single appointment by ID."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient = await db.get(Patient, appt.patient_id)
    doctor  = await db.get(Doctor,  appt.doctor_id)

    return {
        "id":         appt.id,
        "patient":    patient.name if patient else "Unknown",
        "doctor":     doctor.name  if doctor  else "Unknown",
        "department": appt.department,
        "date":       appt.date,
        "time_slot":  appt.time_slot,
        "status":     appt.status,
        "reason":     appt.reason,
        "notes":      appt.notes,
    }


@router.put("/appointments/{appointment_id}")
async def modify_appointment(
    appointment_id: int,
    req:            ModifyAppointmentRequest,
    db:             AsyncSession = Depends(get_db)
):
    """Reschedule an appointment."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appt.status == AppointmentStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot modify a cancelled appointment")

    # Update fields
    if req.date:      appt.date      = req.date
    if req.time_slot: appt.time_slot = req.time_slot
    if req.reason:    appt.reason    = req.reason
    appt.status = AppointmentStatus.RESCHEDULED

    return {
        "message":        "✅ Appointment rescheduled successfully!",
        "appointment_id": appt.id,
        "new_date":       appt.date,
        "new_time_slot":  appt.time_slot,
        "status":         appt.status,
    }


@router.delete("/appointments/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    db:             AsyncSession = Depends(get_db)
):
    """Cancel an appointment."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appt = result.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appt.status == AppointmentStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Appointment is already cancelled")

    appt.status = AppointmentStatus.CANCELLED

    return {
        "message":        "✅ Appointment cancelled successfully!",
        "appointment_id": appt.id,
        "status":         "cancelled",
    }


@router.get("/appointments/history/{phone}")
async def get_appointment_history(
    phone: str,
    db:    AsyncSession = Depends(get_db)
):
    """Get appointment history by patient phone number."""

    # Find patient
    result = await db.execute(
        select(Patient).where(Patient.phone == phone)
    )
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get appointments
    appts = await db.execute(
        select(Appointment).where(Appointment.patient_id == patient.id)
        .order_by(Appointment.date.desc())
    )
    appointments = appts.scalars().all()

    history = []
    for appt in appointments:
        doctor = await db.get(Doctor, appt.doctor_id)
        history.append({
            "id":         appt.id,
            "doctor":     doctor.name if doctor else "Unknown",
            "department": appt.department,
            "date":       appt.date,
            "time_slot":  appt.time_slot,
            "status":     appt.status,
            "reason":     appt.reason,
        })

    return {
        "patient":      patient.name,
        "phone":        phone,
        "total":        len(history),
        "appointments": history,
    }


@router.get("/doctors")
async def get_all_doctors(db: AsyncSession = Depends(get_db)):
    """Get list of all doctors."""
    result = await db.execute(select(Doctor))
    doctors = result.scalars().all()

    return {
        "total": len(doctors),
        "doctors": [
            {
                "id":             d.id,
                "name":           d.name,
                "department":     d.department,
                "specialization": d.specialization,
                "experience":     d.experience,
                "available_days": d.available_days,
                "available_time": d.available_time,
                "fee":            d.fee,
                "languages":      d.languages,
            }
            for d in doctors
        ],
    }