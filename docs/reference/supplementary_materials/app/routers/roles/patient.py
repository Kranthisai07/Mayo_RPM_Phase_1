from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import get_current_user, require_role
from app.schemas.user import UserResponse
from app.services.user_service import get_user_profile, get_user_by_id

router = APIRouter(
    prefix="/patient",
    tags=["Patient"]
)



# Get current logged-in user profile
@router.get("/me", response_model=UserResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["patient"])) 
):
    return get_user_profile(db, current_user["user_id"])



# Get user by id (self only)
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["patient"]))
):
    return get_user_by_id(db, current_user["user_id"], user_id)