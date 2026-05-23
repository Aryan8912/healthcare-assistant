"""
agents/appointment_agent.py — Handles all appointment-related queries.
Extracts intent, patient info, and calls appointment tools.
"""
import re
from typing import Optional
from google import genai
from backend.config import settings, SCHEDULER_SYSTEM_PROMPT
from backend.tools.appointment_tools import (
    fetch_slots, book_appointment, cancel_appointment,
    modify_appointment, retrieve_appointments, get_doctors
)


# ── Info Extractor ────────────────────────────────────────────────────────────

def extract_appointment_info(message: str) -> dict:
    """Extract appointment details from user message using regex."""
    info = {}

    # Extract phone number
    phone = re.search(r'(\+?\d[\d\s\-]{9,})', message)
    if phone:
        info["phone"] = phone.group(1).strip()

    # Extract date (YYYY-MM-DD or DD/MM/YYYY)
    date = re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', message)
    if date:
        info["date"] = date.group(1)

    # Extract time slot
    time = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', message)
    if time:
        info["time_slot"] = time.group(1).upper()

    # Extract appointment ID
    apt_id = re.search(r'appointment\s+(?:id\s+)?#?(\d+)', message, re.IGNORECASE)
    if apt_id:
        info["appointment_id"] = int(apt_id.group(1))

    # Detect sub-intent
    msg = message.lower()
    if any(k in msg for k in ["cancel", "cancell"]):
        info["sub_intent"] = "cancel"
    elif any(k in msg for k in ["reschedule", "modify", "change", "move"]):
        info["sub_intent"] = "reschedule"
    elif any(k in msg for k in ["history", "my appointments", "past", "previous"]):
        info["sub_intent"] = "history"
    elif any(k in msg for k in ["available", "slots", "free", "open"]):
        info["sub_intent"] = "fetch_slots"
    elif any(k in msg for k in ["book", "schedule", "reserve", "make"]):
        info["sub_intent"] = "book"
    elif any(k in msg for k in ["doctor", "specialist", "physicians"]):
        info["sub_intent"] = "get_doctors"
    else:
        info["sub_intent"] = "book"

    return info


# ── Appointment Agent ─────────────────────────────────────────────────────────

async def run(message: str, session_id: Optional[str] = None) -> dict:
    """
    Main appointment agent handler.

    Args:
        message:    User message
        session_id: Session ID for context
    Returns:
        Dict with response, tool_calls used
    """
    tool_calls = []
    response   = ""

    # Extract info from message
    info = extract_appointment_info(message)
    sub_intent = info.get("sub_intent", "book")

    # ── Get Doctors ───────────────────────────────────────────────────────────
    if sub_intent == "get_doctors":
        tool_calls.append({"tool": "get_doctors", "status": "calling"})
        result = await get_doctors()
        tool_calls[-1]["status"] = "done"

        doctors_list = "\n".join([
            f"• Dr. {d['name']} — {d['department']} (Fee: ₹{d['fee']})"
            for d in result["doctors"]
        ])
        response = f"Here are our available doctors:\n\n{doctors_list}\n\nWhich doctor would you like to book with?"

    # ── Fetch Slots ───────────────────────────────────────────────────────────
    elif sub_intent == "fetch_slots":
        if "doctor_id" in info and "date" in info:
            tool_calls.append({"tool": "fetch_slots", "status": "calling"})
            result = await fetch_slots(info["doctor_id"], info["date"])
            tool_calls[-1]["status"] = "done"

            slots = result.get("available_slots", [])
            if slots:
                slots_str = ", ".join(slots)
                response  = f"Available slots for {result.get('doctor')} on {info['date']}:\n{slots_str}\n\nWhich slot would you like?"
            else:
                response = f"No available slots on {info['date']}. Please try another date."
        else:
            tool_calls.append({"tool": "get_doctors", "status": "calling"})
            result = await get_doctors()
            tool_calls[-1]["status"] = "done"
            response = (
                "I can check available slots for you! Please provide:\n"
                "• Doctor name or department\n"
                "• Preferred date (YYYY-MM-DD)\n\n"
                "Available doctors:\n" +
                "\n".join([f"• {d['name']} (ID: {d['id']}) — {d['department']}" for d in result["doctors"]])
            )

    # ── Book Appointment ──────────────────────────────────────────────────────
    elif sub_intent == "book":
        if all(k in info for k in ["phone"]) and "doctor_id" in info and "date" in info and "time_slot" in info:
            tool_calls.append({"tool": "book_appointment", "status": "calling"})
            result = await book_appointment(
                patient_name  = info.get("name", "Patient"),
                patient_phone = info["phone"],
                doctor_id     = info["doctor_id"],
                date          = info["date"],
                time_slot     = info["time_slot"],
                reason        = info.get("reason"),
            )
            tool_calls[-1]["status"] = "done"

            if result.get("success"):
                response = (
                    f"✅ Appointment booked successfully!\n\n"
                    f"• Doctor: {result['doctor']}\n"
                    f"• Department: {result['department']}\n"
                    f"• Date: {result['date']}\n"
                    f"• Time: {result['time_slot']}\n"
                    f"• Appointment ID: {result['appointment_id']}\n\n"
                    f"Please arrive 15 minutes early."
                )
            else:
                response = f"❌ Booking failed: {result.get('message')}"
        else:
            tool_calls.append({"tool": "get_doctors", "status": "calling"})
            result = await get_doctors()
            tool_calls[-1]["status"] = "done"
            response = (
                "I'd love to help you book an appointment! Please provide:\n\n"
                "• Your full name\n"
                "• Phone number\n"
                "• Preferred doctor or department\n"
                "• Preferred date (YYYY-MM-DD)\n"
                "• Preferred time slot\n\n"
                "Available departments:\n" +
                "\n".join(list(set([f"• {d['department']}" for d in result["doctors"]])))
            )

    # ── Cancel Appointment ────────────────────────────────────────────────────
    elif sub_intent == "cancel":
        if "appointment_id" in info:
            tool_calls.append({"tool": "cancel_appointment", "status": "calling"})
            result = await cancel_appointment(info["appointment_id"])
            tool_calls[-1]["status"] = "done"

            if result.get("success"):
                response = f"✅ Appointment #{info['appointment_id']} has been cancelled successfully."
            else:
                response = f"❌ Cancellation failed: {result.get('message')}"
        else:
            response = "Please provide your appointment ID to cancel. Example: 'Cancel appointment #6'"

    # ── Reschedule ────────────────────────────────────────────────────────────
    elif sub_intent == "reschedule":
        if all(k in info for k in ["appointment_id", "date", "time_slot"]):
            tool_calls.append({"tool": "modify_appointment", "status": "calling"})
            result = await modify_appointment(
                appointment_id = info["appointment_id"],
                new_date       = info["date"],
                new_time_slot  = info["time_slot"],
            )
            tool_calls[-1]["status"] = "done"

            if result.get("success"):
                response = (
                    f"✅ Appointment rescheduled!\n\n"
                    f"• New Date: {result['new_date']}\n"
                    f"• New Time: {result['new_time_slot']}"
                )
            else:
                response = f"❌ Reschedule failed: {result.get('message')}"
        else:
            response = (
                "To reschedule, please provide:\n"
                "• Appointment ID\n"
                "• New date (YYYY-MM-DD)\n"
                "• New time slot"
            )

    # ── History ───────────────────────────────────────────────────────────────
    elif sub_intent == "history":
        if "phone" in info:
            tool_calls.append({"tool": "retrieve_appointments", "status": "calling"})
            result = await retrieve_appointments(info["phone"])
            tool_calls[-1]["status"] = "done"

            if result.get("success") and result.get("total", 0) > 0:
                apts = result["appointments"]
                apts_str = "\n".join([
                    f"• #{a['id']} — {a['doctor']} on {a['date']} at {a['time_slot']} ({str(a['status']).split('.')[-1].lower()})"
                    for a in apts
                ])
                response = f"Here are your appointments, {result['patient']}:\n\n{apts_str}"
            else:
                response = "No appointments found for this phone number."
        else:
            response = "Please provide your phone number to view your appointment history."

    return {
        "response":   response,
        "agent":      "appointment_agent",
        "tool_calls": tool_calls,
        "info":       info,
    }


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def test():
        print("🧪 Testing appointment agent...\n")

        tests = [
            "Show me all available doctors",
            "I want to book an appointment",
            "Cancel appointment #6",
            "Show my appointments for +91-9876543210",
        ]

        for msg in tests:
            print(f"👤 User: {msg}")
            result = await run(msg)
            print(f"🤖 Agent: {result['response'][:150]}")
            print(f"🔧 Tools: {[t['tool'] for t in result['tool_calls']]}")
            print()

        print("🎉 Appointment agent test complete!")

    asyncio.run(test())