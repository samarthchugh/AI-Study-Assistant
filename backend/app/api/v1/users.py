from fastapi import APIRouter, Depends
from app.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
def read_me(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}
