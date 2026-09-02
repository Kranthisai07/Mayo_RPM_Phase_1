from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.database.database import Base, SessionLocal, engine
from app.models import Alert, AuditLog, PatientAssignment, User, Vitals
from app.routers import admin, alerts, nurse, patient, vitals
from app.services.admin_seed_service import create_default_admin


app = FastAPI(
    title="Hospital Remote Monitoring API",
    description="Patient monitoring backend",
    version="1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8081",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        create_default_admin(db)
    finally:
        db.close()


app.include_router(auth_router)
app.include_router(patient.router)
app.include_router(nurse.router)
app.include_router(admin.router)
app.include_router(vitals.router)
app.include_router(alerts.router)


@app.get("/")
def home():
    return {
        "message": "API Running",
        "status": "healthy",
    }
