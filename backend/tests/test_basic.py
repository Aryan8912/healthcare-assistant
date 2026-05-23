"""
tests/test_basic.py — Basic sanity checks.
Run: pytest backend/tests/test_basic.py -v
"""
import pytest
from backend.config import settings
from backend.db.models import Patient, Doctor, Appointment, AppointmentStatus


def test_settings_loaded():
    assert settings.gemini_model is not None
    assert settings.database_url is not None
    assert settings.embedding_model is not None


def test_appointment_status_enum():
    assert AppointmentStatus.SCHEDULED   == "scheduled"
    assert AppointmentStatus.CANCELLED   == "cancelled"
    assert AppointmentStatus.COMPLETED   == "completed"
    assert AppointmentStatus.RESCHEDULED == "rescheduled"


def test_config_paths_exist():
    from backend.config import DATA_DIR, MEDICAL_DOCS_DIR, VECTOR_DB_DIR
    assert DATA_DIR.exists()
    assert MEDICAL_DOCS_DIR.exists()
    assert VECTOR_DB_DIR.exists()


def test_sample_doctors_loaded():
    from backend.config import SAMPLE_DOCTORS
    assert len(SAMPLE_DOCTORS) > 0
    assert all("name" in d for d in SAMPLE_DOCTORS)
    assert all("department" in d for d in SAMPLE_DOCTORS)