from pydantic import BaseModel
from typing import Dict

class RetrievedChunk(BaseModel):
    text: str
    score: float
    metadata: Dict