from datetime import datetime, timezone

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import User
from app.schemas.patient import PatientCreate
from app.schemas.user import UserCreate
from app.auth.utils import hash_password, verify_password, create_access_token
from app.services.assignment_service import assign_patient_to_available_nurse


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    role: str,
    age: int | None = None,
    is_active: bool = True,
    is_available: bool = False,
) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        name=name,
        age=age,
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
        is_available=is_available,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register_patient(db: Session, user_data: UserCreate | PatientCreate) -> User:
    user = create_user(
        db,
        name=user_data.name,
        age=user_data.age,
        email=user_data.email,
        password=user_data.password,
        role="patient",
        is_active=True,
        is_available=False,
    )
    assign_patient_to_available_nurse(db, user.id)
    return user


def login_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    token = create_access_token({
        "user_id": user.id,
        "role": user.role
    })

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
    }
