from fastapi import APIRouter, Depends
from app.database.database import get_db
from app.auth.dependencies import get_current_user, require_role



router = APIRouter(
    prefix = "/nurse"
    
)