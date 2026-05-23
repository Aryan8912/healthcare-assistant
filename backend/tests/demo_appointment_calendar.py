"""
tests/demo_appointment_calendar.py — Demo appointment booking workflow.
Run: python -m backend.tests.demo_appointment_calendar
"""
import asyncio
from datetime import datetime, timedelta
from backend.modules.scheduler import scheduler

async def demo():
    print("🎯 Demo: Appointment Booking Workflow")
    print("=" * 50)

    # Step 1: Get doctors
    print("\n📋 Step 1: Available Doctors")
    doctors = await scheduler.get_all_doctors()
    for d in doctors[:3]:
        print(f"  • {d['name']} — {d['department']} (₹{d['fee']})")

    # Step 2: Check slots
    print("\n📅 Step 2: Available Slots")
    next_monday = datetime.now()
    while next_monday.strftime("%a") != "Mon":
        next_monday += timedelta(days=1)
    date_str = next_monday.strftime("%Y-%m-%d")

    slots = await scheduler.get_available_slots(1, date_str)
    print(f"  Doctor: {slots.get('doctor')}")
    print(f"  Date: {date_str}")
    print(f"  Available: {slots.get('total_available', 0)} slots")
    if slots.get("available_slots"):
        print(f"  Slots: {', '.join(slots['available_slots'][:5])}")

    # Step 3: Book appointment
    print("\n📝 Step 3: Book Appointment")
    result = await scheduler.book_appointment(
        patient_name  = "Demo Patient",
        patient_phone = "+91-9000000001",
        doctor_id     = 1,
        date_str      = date_str,
        time_slot     = slots.get("available_slots", ["9:00 AM"])[0],
        reason        = "Demo consultation",
    )
    if result["success"]:
        print(f"  ✅ {result['message']}")
        apt_id = result["appointment_id"]

        # Step 4: Cancel
        print("\n❌ Step 4: Cancel Appointment")
        cancel = await scheduler.cancel_appointment(apt_id)
        print(f"  ✅ {cancel['message']}")
    else:
        print(f"  ❌ {result['message']}")

    print("\n🎉 Demo complete!")

if __name__ == "__main__":
    asyncio.run(demo())