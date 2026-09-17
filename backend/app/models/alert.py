from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    vital_id = Column(Integer, ForeignKey("vitals.id"), nullable=True)

    alert_type = Column(String, nullable=False)

    severity = Column(String, nullable=False)

    message = Column(String, nullable=False)

    status = Column(String, default="active")

    is_escalated = Column(Boolean, nullable=False, default=False)

    escalated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("User", back_populates="alerts")

    vital = relationship("Vitals", back_populates="alerts")
