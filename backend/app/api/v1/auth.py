from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from firebase_admin import auth as firebase_auth
from app.db.session import get_db
from app.db.models import User
from app.services.security import verify_password, create_access_token, hash_password
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.firebase_admin_init import get_firebase_app

router = APIRouter(prefix="/auth", tags=["auth"])


class FirebaseTokenPayload(BaseModel):
    id_token: str


@router.post("/firebase", response_model=Token)
def firebase_login(payload: FirebaseTokenPayload, db: Session = Depends(get_db)):
    get_firebase_app()
    try:
        decoded = firebase_auth.verify_id_token(payload.id_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    email: str | None = decoded.get("email")
    firebase_uid: str = decoded["uid"]

    if not email:
        raise HTTPException(status_code=400, detail="Email not available from this provider")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, hashed_password=None, provider="firebase", firebase_uid=firebase_uid)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user.firebase_uid:
        user.firebase_uid = firebase_uid
        db.commit()

    return {"access_token": create_access_token(data={"sub": str(user.id)}), "token_type": "bearer"}


@router.post("/signup", response_model=UserResponse)
def signup(user_create: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_create.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(email=user_create.email, hashed_password=hash_password(user_create.password), provider="local")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(data={"sub": str(user.id)}), "token_type": "bearer"}
