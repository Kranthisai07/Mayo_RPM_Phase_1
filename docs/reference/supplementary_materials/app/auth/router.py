from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.service import login_user, register_patient
from app.schemas.patient import PatientResponse
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)



@router.post("/register", response_model=PatientResponse)
def register(
    data: UserCreate,
    db: Session = Depends(get_db)
):
    return register_patient(db=db, user_data=data)


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    return login_user(
        db=db,
        email=data.email,
        password=data.password
    )
