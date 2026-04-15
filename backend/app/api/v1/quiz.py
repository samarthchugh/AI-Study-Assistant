from http.client import HTTPException
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.quiz_engine import QuizEngine
from app.dependencies import get_current_user
from app.db.models import Quiz, User, QuizAttempt

from app.schemas.quiz import SubmitQuizRequest, SubmitQuizResponse
from app.dependencies import get_current_user

router = APIRouter(prefix='/quiz', tags=['QUIZ'])

@router.post("/generate")
def generate_quiz(
    topic: str,
    num_questions: int = 5,
    difficulty: int = 2,
    current_user_id: str = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    engine = QuizEngine(db)
    quiz = engine.generate_quiz(
        user_id=int(current_user_id),
        topic=topic,
        num_questions=num_questions,
        difficulty=difficulty
    )
    
    return {
        "quiz_id": quiz.id,
        "topic": quiz.topic,
        "difficulty": quiz.difficulty_level,
        "total_questions": quiz.total_questions
    }

@router.get("/{quiz_id}")
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == int(current_user_id))
        .first()
    )
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return {
        "quiz_id": quiz.id,
        "topic": quiz.topic,
        "difficulty": quiz.difficulty_level,
        "total_questions": quiz.total_questions,
        "questions": [
            {
                "question_id": q.id,
                "question_text": q.question_text,
                "options": q.options
            }
            for q in quiz.questions
        ]
    }
    

@router.post("/{quiz_id}/submit", response_model=SubmitQuizResponse)
def submit_quiz(
    quiz_id: int,
    request: SubmitQuizRequest,
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    engine = QuizEngine(db)
    
    result = engine.submit_quiz(
        user_id = int(current_user),
        quiz_id = quiz_id,
        attempt_id=attempt_id,
        submitted_answers = request.answers
    )
    
    return result

@router.post("/{quiz_id}/start")
def start_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    engine = QuizEngine(db)
    
    try:
        result = engine.start_quiz(
            user_id=int(current_user_id),
            quiz_id=quiz_id
        )
        
        return {
            'message': "Quiz started",
            **result
        }
    except HTTPException as e:
        raise e