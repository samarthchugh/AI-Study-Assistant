from fastapi import HTTPException
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.quiz_engine import QuizEngine
from app.dependencies import get_current_user
from app.db.models import Quiz, User, QuizAttempt
from app.utils.logging import get_logger
from app.utils.topic_utils import normalize_topic

from app.schemas.quiz import SubmitQuizRequest, SubmitQuizResponse
from app.dependencies import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix='/quiz', tags=['QUIZ'])

@router.post("/generate")
def generate_quiz(
    topic: Optional[str] = None,
    num_questions: int = 5,
    difficulty: int = 2,
    current_user_id: str = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Quiz Generation Started...")
        engine = QuizEngine(db)
        
        if topic:
            topic = normalize_topic(topic)
            logger.info(f"Generating quiz for user_id: {current_user_id}, topic: {topic}, num_questions: {num_questions}, difficulty: {difficulty}")
        quiz = engine.generate_quiz(
            user_id=int(current_user_id),
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty
        )
        logger.info(f"Quiz Generation Completed - Quiz ID: {quiz.id}")
        return {
            "quiz_id": quiz.id,
            "topic": quiz.topic,
            "difficulty": quiz.difficulty_level,
            "total_questions": quiz.total_questions
        }
    except Exception as e:
        logger.error(f"Error generating quiz for user {current_user_id}, topic {topic}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{quiz_id}")
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    try:
        logger.info(f"Fetching quiz details for quiz_id: {quiz_id}, user_id: {current_user_id}")
        quiz = (
            db.query(Quiz)
            .filter(Quiz.id == quiz_id, Quiz.user_id == int(current_user_id))
            .first()
        )
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        logger.info(f"Quiz details fetched successfully for quiz_id: {quiz_id}, user_id: {current_user_id}")
        
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
    except Exception as e:
        logger.error(f"Error fetching quiz details for quiz_id: {quiz_id}, user_id: {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/{quiz_id}/submit", response_model=SubmitQuizResponse)
def submit_quiz(
    quiz_id: int,
    request: SubmitQuizRequest,
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    try:
        logger.info(f"Submitting quiz for quiz_id: {quiz_id}, user_id: {current_user}, attempt_id: {attempt_id}")
        engine = QuizEngine(db)
        
        result = engine.submit_quiz(
            user_id = int(current_user),
            quiz_id = quiz_id,
            attempt_id=attempt_id,
            submitted_answers = request.answers
        )
        logger.info(f"Quiz submitted successfully for quiz_id: {quiz_id}, user_id: {current_user}, attempt_id: {attempt_id}, score: {result['score_ratio']}")
        
        return result
    except Exception as e:
        logger.error(f"Error submitting quiz for quiz_id: {quiz_id}, user_id: {current_user}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{quiz_id}/start")
def start_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    engine = QuizEngine(db)
    
    try:
        logger.info(f"Starting quiz for quiz_id: {quiz_id}, user_id: {current_user_id}")
        result = engine.start_quiz(
            user_id=int(current_user_id),
            quiz_id=quiz_id
        )
        
        return {
            'message': "Quiz started",
            **result
        }
    except Exception as e:
        logger.error(f"Error starting quiz for quiz_id: {quiz_id}, user_id: {current_user_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
