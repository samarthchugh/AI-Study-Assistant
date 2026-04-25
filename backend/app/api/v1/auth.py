from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.services.security import (
    verify_password, 
    create_access_token, 
    hash_password
)
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
# from app.schemas.auth import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserResponse)
def signup(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user. Returns 400 if the email is already taken."""
    user = db.query(User).filter(User.email == user_create.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")        
    hashed_password = hash_password(user_create.password)
    new_user = User(email=user_create.email, hashed_password=hashed_password, provider="local")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate with email + password and return a bearer JWT. Returns 401 on bad credentials."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
    