from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Vitals(Base):
    __tablename__ = "vitals"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    weight_value = Column(Float)

    spo2_value = Column(Float)

    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("User", back_populates="vitals")

    alerts = relationship("Alert", back_populates="vital")