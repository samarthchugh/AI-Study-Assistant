from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union

class AnswerItem(BaseModel):
    question_id: int = Field(..., description="ID of the question")
    answer: str = Field(..., description="Answer provided by the user", min_length=1)

class SubmitQuizRequest(BaseModel):
    answers: List[AnswerItem]

class QuestionResult(BaseModel):
    question_id: int
    question_text: str
    question_type: str
    options: Optional[Union[Dict[str, str], List[str]]]
    user_answer: str
    correct_answer: str
    explanation: Optional[str]
    is_correct: bool

class SubmitQuizResponse(BaseModel):
    quiz_id: int
    score_ratio: float
    correct_answers: int
    total_questions: int
    new_difficulty: int
    updated_mastery: float
    time_taken_seconds: Optional[int]
    question_breakdown: List[QuestionResult]
