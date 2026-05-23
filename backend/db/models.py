"""
db/models.py — SQLAlchemy ORM models for the healthcare assistant.
Tables: Patient, Doctor, Appointment, ConversationHistory
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime,
    ForeignKey, Enum as SAEnum, Text, Boolean
)
from sqlalchemy.orm import relationship, DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────────────────────────

class AppointmentStatus(str, enum.Enum):
    SCHEDULED   = "scheduled"
    CANCELLED   = "cancelled"
    COMPLETED   = "completed"
    RESCHEDULED = "rescheduled"


class Department(str, enum.Enum):
    GENERAL_MEDICINE = "General Medicine"
    CARDIOLOGY       = "Cardiology"
    ORTHOPEDICS      = "Orthopedics"
    NEUROLOGY        = "Neurology"
    PEDIATRICS       = "Pediatrics"
    GYNECOLOGY       = "Gynecology"
    DERMATOLOGY      = "Dermatology"
    OPHTHALMOLOGY    = "Ophthalmology"
    ENT              = "ENT"
    PSYCHIATRY       = "Psychiatry"


# ── Models ─────────────────────────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(120), nullable=False)
    phone         = Column(String(20),  unique=True, index=True)
    email         = Column(String(120), unique=True, index=True, nullable=True)
    date_of_birth = Column(String(20),  nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    appointments  = relationship("Appointment", back_populates="patient")


class Doctor(Base):
    __tablename__ = "doctors"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(120), nullable=False)
    department     = Column(String(80),  nullable=False)
    specialization = Column(String(200), nullable=True)
    experience     = Column(Integer,     nullable=True)
    available_days = Column(String(200), nullable=True)
    available_time = Column(String(100), nullable=True)
    fee            = Column(Integer,     nullable=True)
    languages      = Column(String(200), nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

    appointments   = relationship("Appointment", back_populates="doctor")


class Appointment(Base):
    __tablename__ = "appointments"

    id            = Column(Integer, primary_key=True, index=True)
    patient_id    = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id     = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    department    = Column(String(80),  nullable=False)
    date          = Column(String(20),  nullable=False)
    time_slot     = Column(String(20),  nullable=False)
    status        = Column(
        SAEnum(AppointmentStatus),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
    )
    reason        = Column(Text,    nullable=True)
    notes         = Column(Text,    nullable=True)

    # Email tracking
    approval_email_sent     = Column(Boolean, default=False)
    confirmation_email_sent = Column(Boolean, default=False)

    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")
    doctor  = relationship("Doctor",  back_populates="appointments")


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    role       = Column(String(20), nullable=False)
    content    = Column(Text,       nullable=False)
    agent_used = Column(String(60), nullable=True)
    created_at = Column(DateTime,   default=datetime.utcnow)