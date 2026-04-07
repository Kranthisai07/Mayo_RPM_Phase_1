from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import Patient
from app.auth.utils import hash_password, verify_password, create_access_token


def register_user(db: Session, name: str, age: int, email: str, password: str) -> Patient:
    existing = db.query(Patient).filter(Patient.email == email).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_pw = hash_password(password)

    user = Patient(
        name=name,
        age=age,
        email=email,
        password_hash=hashed_pw
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login_user(db: Session, email: str, password: str) -> str:
    user = db.query(Patient).filter(Patient.email == email).first()

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

    token = create_access_token({
        "patient_id": user.id,
        "email": user.email
    })

    return token