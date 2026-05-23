"""
db/seed.py — Seeds the database with sample doctors and patients.
Runs automatically on first startup.
"""
import asyncio
from sqlalchemy import select
from backend.db.database import AsyncSessionLocal, init_db
from backend.db.models import Patient, Doctor, Appointment, AppointmentStatus
from backend.config import SAMPLE_DOCTORS
from datetime import date, timedelta


# ── Sample Patients ───────────────────────────────────────────────────────────

SAMPLE_PATIENTS = [
    {
        "name":          "Aarav Sharma",
        "phone":         "+91-9876543210",
        "email":         "aarav@example.com",
        "date_of_birth": "1990-05-15",
    },
    {
        "name":          "Priya Nair",
        "phone":         "+91-9876543211",
        "email":         "priya@example.com",
        "date_of_birth": "1985-08-22",
    },
    {
        "name":          "Rohit Mehta",
        "phone":         "+91-9876543212",
        "email":         "rohit@example.com",
        "date_of_birth": "1995-03-10",
    },
    {
        "name":          "Sunita Verma",
        "phone":         "+91-9876543213",
        "email":         "sunita@example.com",
        "date_of_birth": "1978-11-30",
    },
    {
        "name":          "Kiran Patel",
        "phone":         "+91-9876543214",
        "email":         "kiran@example.com",
        "date_of_birth": "2000-07-04",
    },
]


# ── Sample Appointments ───────────────────────────────────────────────────────

SAMPLE_APPOINTMENTS = [
    {
        "patient_index": 0,
        "doctor_index":  0,
        "date":          str(date.today() + timedelta(days=2)),
        "time_slot":     "10:00 AM",
        "status":        AppointmentStatus.SCHEDULED,
        "reason":        "Routine cardiac check-up",
    },
    {
        "patient_index": 1,
        "doctor_index":  1,
        "date":          str(date.today() + timedelta(days=3)),
        "time_slot":     "11:30 AM",
        "status":        AppointmentStatus.SCHEDULED,
        "reason":        "Knee pain follow-up",
    },
    {
        "patient_index": 2,
        "doctor_index":  2,
        "date":          str(date.today() - timedelta(days=5)),
        "time_slot":     "09:00 AM",
        "status":        AppointmentStatus.COMPLETED,
        "reason":        "Migraine evaluation",
    },
    {
        "patient_index": 3,
        "doctor_index":  3,
        "date":          str(date.today() + timedelta(days=7)),
        "time_slot":     "02:00 PM",
        "status":        AppointmentStatus.SCHEDULED,
        "reason":        "Diabetes management",
    },
    {
        "patient_index": 4,
        "doctor_index":  4,
        "date":          str(date.today() - timedelta(days=10)),
        "time_slot":     "09:30 AM",
        "status":        AppointmentStatus.CANCELLED,
        "reason":        "Child vaccination",
    },
]


# ── Seed Function ─────────────────────────────────────────────────────────────

async def seed() -> None:
    """Insert sample data if DB is empty."""
    await init_db()

    async with AsyncSessionLocal() as session:

        # ── Check if already seeded ────────────────────────────────────────
        result = await session.execute(select(Doctor))
        if result.scalars().first():
            print("ℹ️  Database already seeded — skipping.")
            return

        # ── Insert Doctors ─────────────────────────────────────────────────
        doctor_objs = []
        for d in SAMPLE_DOCTORS:
            doctor = Doctor(**d)
            session.add(doctor)
            doctor_objs.append(doctor)

        await session.flush()   # get doctor IDs
        print(f"✅ Inserted {len(doctor_objs)} doctors.")

        # ── Insert Patients ────────────────────────────────────────────────
        patient_objs = []
        for p in SAMPLE_PATIENTS:
            patient = Patient(**p)
            session.add(patient)
            patient_objs.append(patient)

        await session.flush()   # get patient IDs
        print(f"✅ Inserted {len(patient_objs)} patients.")

        # ── Insert Appointments ────────────────────────────────────────────
        for appt_data in SAMPLE_APPOINTMENTS:
            patient_idx = appt_data.pop("patient_index")
            doctor_idx  = appt_data.pop("doctor_index")

            appt = Appointment(
                patient_id = patient_objs[patient_idx].id,
                doctor_id  = doctor_objs[doctor_idx].id,
                department = doctor_objs[doctor_idx].department,
                **appt_data,
            )
            session.add(appt)

        await session.commit()
        print(f"✅ Inserted {len(SAMPLE_APPOINTMENTS)} appointments.")
        print("🎉 Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())