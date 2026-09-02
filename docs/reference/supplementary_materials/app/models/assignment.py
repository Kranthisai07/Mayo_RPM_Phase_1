from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class PatientAssignment(Base):
    __tablename__ = "patient_assignments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    nurse_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

    patient = relationship(
        "User",
        foreign_keys=[patient_id],
        back_populates="patient_assignments",
    )
    nurse = relationship(
        "User",
        foreign_keys=[nurse_id],
        back_populates="nurse_assignments",
    )
