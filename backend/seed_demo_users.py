from app.database.database import SessionLocal
from app.models import User
from app.auth.utils import hash_password


DEMO_USERS = [
    {
        "name": "System Admin",
        "email": "admin@example.com",
        "password": "AdminPass123",
        "role": "admin",
    },
    {
        "name": "Demo Nurse",
        "email": "nurse@example.com",
        "password": "Nurse123",
        "role": "nurse",
    },
    {
        "name": "Demo Patient",
        "email": "patient@example.com",
        "password": "Patient123",
        "role": "patient",
    },
]


def seed_demo_users():
    db = SessionLocal()

    try:
        for user_data in DEMO_USERS:

            existing = (
                db.query(User)
                .filter(User.email == user_data["email"])
                .first()
            )

            if existing:
                print(f"✓ {user_data['role'].capitalize()} already exists")
                continue

            user = User(
                name=user_data["name"],
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                role=user_data["role"],
                is_active=True,
            )

            db.add(user)
            db.commit()

            print(
                f"✓ Created {user_data['role']} ({user_data['email']})"
            )

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_users()
