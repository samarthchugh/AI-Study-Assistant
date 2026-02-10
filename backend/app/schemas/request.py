from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, example="What programming languages are mentioned?")
    
class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float