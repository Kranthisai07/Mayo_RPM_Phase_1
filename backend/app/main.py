from fastapi import FastAPI

from app.database.database import engine
from app.models.models import Base

from app.routers import alerts, patient, vitals
from app.auth.router import router as auth_router


app = FastAPI(
    title="Hospital Remote Monitoring API",
    description="patient monitoring backend",
    version="1.0"
)


# -------------------------
# Create Database Tables
# -------------------------

@app.on_event("startup")
def startup():

    Base.metadata.create_all(bind=engine)


# -------------------------
# Include Routers
# -------------------------

app.include_router(auth_router)

app.include_router(patient.router)

app.include_router(vitals.router)

app.include_router(alerts.router)


# -------------------------
# Health Check
# -------------------------

@app.get("/")
def home():

    return {
        "message": "API Running"
    }