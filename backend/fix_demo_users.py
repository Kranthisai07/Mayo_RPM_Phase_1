"""
Quick fix: Check existing demo users and reset their passwords correctly.
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from app.database.database import Base, SessionLocal, engine
from app.models import User
from app.auth.utils import hash_password, verify_password

DEMO_USERS = [
    {"name": "System Admin",  "email": "admin@example.com",   "password": "AdminPass123",  "role": "admin"},
    {"name": "Demo Nurse",    "email": "nurse@example.com",   "password": "Nurse123",       "role": "nurse"},
    {"name": "Demo Patient",  "email": "patient@example.com", "password": "Patient123",     "role": "patient"},
]

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    for u in DEMO_USERS:
        user = db.query(User).filter(User.email == u["email"]).first()

        if not user:
            user = User(
                name=u["name"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[CREATED] {u['role']}: {u['email']} / {u['password']}")
        else:
            # Reset password to make sure it matches
            ok = verify_password(u["password"], user.password_hash)
            if not ok:
                print(f"[FIX] Password mismatch for {u['email']} - resetting...")
                user.password_hash = hash_password(u["password"])
                user.is_active = True
                db.commit()
                print(f"[FIXED] {u['role']}: {u['email']} / {u['password']}")
            else:
                print(f"[OK]  {u['role']}: {u['email']} / {u['password']}  (active={user.is_active})")
                if not user.is_active:
                    user.is_active = True
                    db.commit()
                    print(f"      -> Activated!")
finally:
    db.close()

print("\nDone. Try logging in now.")
