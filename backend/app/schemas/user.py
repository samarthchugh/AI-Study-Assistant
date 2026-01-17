from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=64,
        description="Password must be between 8 and 64 characters long."
    )
    
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    provider: str
    created_at: datetime

    class Config:
        orm_mode = True