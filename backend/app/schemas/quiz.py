from pydantic import BaseModel, Field
from typing import List

class AnswerItem(BaseModel):
    question_id: int = Field(..., description="ID of the question")
    answer: str = Field(..., description="Answer provided by the user", min_length=1)
    
class SubmitQuizRequest(BaseModel):
    answers: List[AnswerItem]
    
class SubmitQuizResponse(BaseModel):
    quiz_id: int = Field(..., description="ID of the quiz")
    score_ratio: float 
    correct_answers: int
    total_questions: int
    new_difficulty: int
    updated_mastery: float
    time_taken_seconds: int