import uuid
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    provider = Column(String, default="local")
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True,index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    topic = Column(String, nullable=False)
    difficulty_level = Column(Integer, nullable=False)
    
    status = Column(String, default="active", nullable=False)
    total_questions = Column(Integer, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # constraints
    __table_args__ = (
        CheckConstraint('difficulty_level >= 1 AND difficulty_level <= 5', name='check_difficulty_level'),
        CheckConstraint("status IN ('active', 'completed')", name='check_status')
    )
    
    # relationships
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")
    
class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)

    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)

    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)  # mcq or short
    options = Column(JSONB, nullable=True)

    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)

    difficulty_level = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("question_type IN ('mcq', 'short')"),
        CheckConstraint("difficulty_level >= 1 AND difficulty_level <= 5"),
    )

    quiz = relationship("Quiz", back_populates="questions")
    question_attempts = relationship("QuestionAttempt", back_populates="question")
    
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)

    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    score_ratio = Column(Float, nullable=True)

    confidence_score = Column(Float, nullable=True)

    submitted_at = Column(DateTime(timezone=True), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)

    quiz = relationship("Quiz", back_populates="attempts")
    question_attempts = relationship("QuestionAttempt", back_populates="quiz_attempt")
    Index("idx_quiz_user", "quiz_id", "user_id")
    
class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

    id = Column(Integer, primary_key=True, index=True)

    quiz_attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    user_answer = Column(Text, nullable=False)
    is_correct = Column(Integer, nullable=False)  # 0 or 1
    score = Column(Float, nullable=False)

    confidence_score = Column(Float, nullable=True)

    answered_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    quiz_attempt = relationship("QuizAttempt", back_populates="question_attempts")
    question = relationship("Question", back_populates="question_attempts")
    

class UserTopicProgress(Base):
    __tablename__ = "user_topic_progress"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic = Column(String, nullable=False)

    current_difficulty = Column(Integer, nullable=False, default=2)
    mastery_score = Column(Float, nullable=False, default=0.0)

    last_attempt_at = Column(DateTime(timezone=True), nullable=True)

    total_attempts = Column(Integer, nullable=False, default=0)
    correct_attempts = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("current_difficulty >= 1 AND current_difficulty <= 5"),
        CheckConstraint("mastery_score >= 0 AND mastery_score <= 1"),
        UniqueConstraint("user_id", "topic", name="uq_user_topic")
    )
    
