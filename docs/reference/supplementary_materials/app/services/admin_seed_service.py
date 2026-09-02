from sqlalchemy.orm import Session

from app.config import ADMIN_EMAIL, ADMIN_NAME, ADMIN_PASSWORD
from app.models import User
from app.auth.utils import hash_password


def create_default_admin(db: Session):
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        print("Warning: ADMIN_EMAIL or ADMIN_PASSWORD is not set. Default admin was not created.")
        return None

    existing_admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if existing_admin:
        return existing_admin

    admin_user = User(
        name=ADMIN_NAME,
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD),
        role="admin",
        is_active=True,
        is_available=False,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user
