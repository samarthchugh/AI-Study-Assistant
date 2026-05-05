from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[List[Any]] = None
    confidence: Optional[float] = None
    created_at: datetime

    class Config:
        orm_mode = True


class SessionOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class SessionWithMessages(SessionOut):
    messages: List[MessageOut] = []
