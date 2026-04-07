from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.service import register_user, login_user
from app.schema.schema import PatientCreate, LoginRequest, TokenResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register(
    data: PatientCreate,
    db: Session = Depends(get_db)
):
    user = register_user(
        db=db,
        name=data.name,
        age=data.age,
        email=data.email,
        password=data.password
    )

    return {
        "message": "Account created successfully",
        "patient_id": user.id
    }


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    token = login_user(
        db=db,
        email=data.email,
        password=data.password
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }