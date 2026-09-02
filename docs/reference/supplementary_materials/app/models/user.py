from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    age = Column(Integer, nullable=True)

    email = Column(String, unique=True, index=True, nullable=False)

    password_hash = Column(String, nullable=False)

    role = Column(String, nullable=False, default="patient")

    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    last_login = Column(DateTime(timezone=True), nullable=True)

    vitals = relationship("Vitals", back_populates="patient")
    alerts = relationship("Alert", back_populates="patient")
    patient_assignments = relationship(
        "PatientAssignment",
        foreign_keys="PatientAssignment.patient_id",
        back_populates="patient",
    )
    nurse_assignments = relationship(
        "PatientAssignment",
        foreign_keys="PatientAssignment.nurse_id",
        back_populates="nurse",
    )
    audit_logs = relationship("AuditLog", back_populates="actor")
