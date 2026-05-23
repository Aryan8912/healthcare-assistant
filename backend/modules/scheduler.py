"""
modules/scheduler.py — Core appointment scheduling logic.
Handles slot generation, conflict checking, booking, and patient management.
"""
import asyncio
from datetime import datetime, timedelta, date
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import (
    Appointment, Patient, Doctor, AppointmentStatus
)
from backend.db.database import AsyncSessionLocal
from backend.config import settings


# ── Time Slot Generator ───────────────────────────────────────────────────────

def generate_time_slots(available_time: str, duration: int = 30) -> list[str]:
    """
    Generate time slots from a range string like '09:00-13:00'.
    Returns list of slots like ['9:00 AM', '9:30 AM', ...]
    """
    try:
        start_str, end_str = available_time.split("-")
        start   = datetime.strptime(start_str.strip(), "%H:%M")
        end     = datetime.strptime(end_str.strip(),   "%H:%M")
        slots   = []
        current = start
        while current < end:
            slots.append(current.strftime("%I:%M %p").lstrip("0"))
            current += timedelta(minutes=duration)
        return slots
    except Exception:
        # Default slots if parsing fails
        return [
            "9:00 AM",  "9:30 AM",  "10:00 AM", "10:30 AM",
            "11:00 AM", "11:30 AM", "2:00 PM",  "2:30 PM",
            "3:00 PM",  "3:30 PM",  "4:00 PM",  "4:30 PM",
        ]


# ── Scheduler Class ───────────────────────────────────────────────────────────

class AppointmentScheduler:
    """
    Core scheduling engine.
    Used by appointment tools and agents.
    """

    # ── Doctors ───────────────────────────────────────────────────────────────

    async def get_all_doctors(self) -> list[dict]:
        """Return all doctors from DB."""
        async with AsyncSessionLocal() as db:
            result  = await db.execute(select(Doctor))
            doctors = result.scalars().all()
            return [
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
            ]

    async def get_doctor_by_id(self, doctor_id: int) -> Optional[dict]:
        """Return a single doctor by ID."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Doctor).where(Doctor.id == doctor_id)
            )
            d = result.scalars().first()
            if not d:
                return None
            return {
                "id":             d.id,
                "name":           d.name,
                "department":     d.department,
                "specialization": d.specialization,
                "available_days": d.available_days,
                "available_time": d.available_time,
                "fee":            d.fee,
            }

    async def get_doctor_by_department(self, department: str) -> list[dict]:
        """Return doctors by department name."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Doctor).where(
                    Doctor.department.ilike(f"%{department}%")
                )
            )
            doctors = result.scalars().all()
            return [
                {
                    "id":         d.id,
                    "name":       d.name,
                    "department": d.department,
                    "fee":        d.fee,
                }
                for d in doctors
            ]

    # ── Availability ──────────────────────────────────────────────────────────

    async def get_available_slots(
        self,
        doctor_id: int,
        date_str:  str,
    ) -> dict:
        """
        Get available time slots for a doctor on a given date.
        Removes already booked slots.
        """
        async with AsyncSessionLocal() as db:

            # Get doctor
            result = await db.execute(
                select(Doctor).where(Doctor.id == doctor_id)
            )
            doctor = result.scalars().first()
            if not doctor:
                return {"error": "Doctor not found"}

            # Check if doctor works on this day
            day_name       = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a")
            available_days = doctor.available_days.split(",") if doctor.available_days else []

            if day_name not in available_days:
                return {
                    "doctor":          doctor.name,
                    "date":            date_str,
                    "available_slots": [],
                    "message":         f"Dr. {doctor.name} is not available on {day_name}s",
                }

            # Generate all slots
            all_slots = generate_time_slots(
                doctor.available_time or "09:00-17:00",
                settings.default_appointment_duration,
            )

            # Get booked slots
            booked_result = await db.execute(
                select(Appointment.time_slot).where(
                    and_(
                        Appointment.doctor_id == doctor_id,
                        Appointment.date      == date_str,
                        Appointment.status    == AppointmentStatus.SCHEDULED,
                    )
                )
            )
            booked_slots = {row[0] for row in booked_result.fetchall()}

            # Available = all - booked
            available = [s for s in all_slots if s not in booked_slots]

            return {
                "doctor":          doctor.name,
                "department":      doctor.department,
                "date":            date_str,
                "day":             day_name,
                "available_slots": available,
                "booked_slots":    list(booked_slots),
                "total_available": len(available),
            }

    # ── Patient ───────────────────────────────────────────────────────────────

    async def get_or_create_patient(
        self,
        name:  str,
        phone: str,
        email: Optional[str] = None,
    ) -> dict:
        """Get existing patient by phone or create new one."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Patient).where(Patient.phone == phone)
            )
            patient = result.scalars().first()

            if not patient:
                patient = Patient(name=name, phone=phone, email=email)
                db.add(patient)
                await db.commit()
                await db.refresh(patient)

            return {
                "id":    patient.id,
                "name":  patient.name,
                "phone": patient.phone,
                "email": patient.email,
            }

    # ── Book Appointment ──────────────────────────────────────────────────────

    async def book_appointment(
        self,
        patient_name:  str,
        patient_phone: str,
        doctor_id:     int,
        date_str:      str,
        time_slot:     str,
        reason:        Optional[str] = None,
        patient_email: Optional[str] = None,
    ) -> dict:
        """Book an appointment after checking availability."""
        async with AsyncSessionLocal() as db:

            # Get doctor
            result = await db.execute(
                select(Doctor).where(Doctor.id == doctor_id)
            )
            doctor = result.scalars().first()
            if not doctor:
                return {"success": False, "message": "Doctor not found"}

            # Check slot availability
            existing = await db.execute(
                select(Appointment).where(
                    and_(
                        Appointment.doctor_id == doctor_id,
                        Appointment.date      == date_str,
                        Appointment.time_slot == time_slot,
                        Appointment.status    == AppointmentStatus.SCHEDULED,
                    )
                )
            )
            if existing.scalars().first():
                return {"success": False, "message": "This slot is already booked"}

            # Get or create patient
            patient_result = await db.execute(
                select(Patient).where(Patient.phone == patient_phone)
            )
            patient = patient_result.scalars().first()
            if not patient:
                patient = Patient(
                    name=patient_name, phone=patient_phone, email=patient_email
                )
                db.add(patient)
                await db.flush()

            # Create appointment
            appointment = Appointment(
                patient_id = patient.id,
                doctor_id  = doctor_id,
                department = doctor.department,
                date       = date_str,
                time_slot  = time_slot,
                reason     = reason,
                status     = AppointmentStatus.SCHEDULED,
            )
            db.add(appointment)
            await db.commit()
            await db.refresh(appointment)

            return {
                "success":        True,
                "appointment_id": appointment.id,
                "patient":        patient.name,
                "doctor":         doctor.name,
                "department":     doctor.department,
                "date":           date_str,
                "time_slot":      time_slot,
                "status":         "scheduled",
                "message":        f"✅ Appointment booked with {doctor.name} on {date_str} at {time_slot}",
            }

    # ── Cancel Appointment ────────────────────────────────────────────────────

    async def cancel_appointment(self, appointment_id: int) -> dict:
        """Cancel an appointment by ID."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Appointment).where(Appointment.id == appointment_id)
            )
            appt = result.scalars().first()

            if not appt:
                return {"success": False, "message": "Appointment not found"}

            if appt.status == AppointmentStatus.CANCELLED:
                return {"success": False, "message": "Appointment is already cancelled"}

            appt.status = AppointmentStatus.CANCELLED
            await db.commit()

            return {
                "success":        True,
                "appointment_id": appointment_id,
                "message":        "✅ Appointment cancelled successfully",
            }

    # ── Reschedule Appointment ────────────────────────────────────────────────

    async def reschedule_appointment(
        self,
        appointment_id: int,
        new_date:       str,
        new_time_slot:  str,
    ) -> dict:
        """Reschedule an appointment to a new date and time."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Appointment).where(Appointment.id == appointment_id)
            )
            appt = result.scalars().first()

            if not appt:
                return {"success": False, "message": "Appointment not found"}

            if appt.status == AppointmentStatus.CANCELLED:
                return {"success": False, "message": "Cannot reschedule a cancelled appointment"}

            # Check new slot is available
            conflict = await db.execute(
                select(Appointment).where(
                    and_(
                        Appointment.doctor_id == appt.doctor_id,
                        Appointment.date      == new_date,
                        Appointment.time_slot == new_time_slot,
                        Appointment.status    == AppointmentStatus.SCHEDULED,
                    )
                )
            )
            if conflict.scalars().first():
                return {"success": False, "message": "New slot is already booked"}

            appt.date      = new_date
            appt.time_slot = new_time_slot
            appt.status    = AppointmentStatus.RESCHEDULED
            await db.commit()

            return {
                "success":        True,
                "appointment_id": appointment_id,
                "new_date":       new_date,
                "new_time_slot":  new_time_slot,
                "message":        f"✅ Appointment rescheduled to {new_date} at {new_time_slot}",
            }

    # ── Patient History ───────────────────────────────────────────────────────

    async def get_patient_appointments(self, phone: str) -> dict:
        """Get all appointments for a patient by phone number."""
        async with AsyncSessionLocal() as db:
            patient_result = await db.execute(
                select(Patient).where(Patient.phone == phone)
            )
            patient = patient_result.scalars().first()

            if not patient:
                return {"success": False, "message": "Patient not found"}

            appts_result = await db.execute(
                select(Appointment)
                .where(Appointment.patient_id == patient.id)
                .order_by(Appointment.date.desc())
            )
            appointments = appts_result.scalars().all()

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
                "success":      True,
                "patient":      patient.name,
                "phone":        phone,
                "total":        len(history),
                "appointments": history,
            }


# ── Singleton ─────────────────────────────────────────────────────────────────

scheduler = AppointmentScheduler()