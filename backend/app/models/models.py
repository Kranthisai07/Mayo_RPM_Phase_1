from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


# -------------------------
# Patient Table
# -------------------------

class Patient(Base):

    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    age = Column(Integer, nullable=False)

    email = Column(String, unique=True, index=True, nullable=False)

    password_hash = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    last_login = Column(DateTime(timezone=True), nullable=True)

    vitals = relationship("Vitals", back_populates="patient")

    alerts = relationship("Alert", back_populates="patient")


# -------------------------
# Vitals Table
# -------------------------

class Vitals(Base):

    __tablename__ = "vitals"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    weight_value = Column(Float)

    spo2_value = Column(Float)

    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="vitals")

    alerts = relationship("Alert", back_populates="vital")


# -------------------------
# Alert Table
# -------------------------

class Alert(Base):

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    vital_id = Column(Integer, ForeignKey("vitals.id"), nullable=True)

    alert_type = Column(String, nullable=False)

    severity = Column(String, nullable=False)

    message = Column(String, nullable=False)

    status = Column(String, default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="alerts")

    vital = relationship("Vitals", back_populates="alerts")