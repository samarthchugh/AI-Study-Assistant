from typing import List, Dict
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from app.db import models
from app.db.crud import get_user_topic_progress
from app.services.vector_store_instance import vector_store
from app.rag.retriever import Retriever
from app.utils.logging import get_logger
from app.services.llm import generate_json_completion
from app.services.intelligence_service import IntelligenceService
from app.utils.topic_utils import normalize_topic
from app.config import redis_client

logger = get_logger(__name__)

class QuizEngine:
    """
    QuizEngine orchestrates the full quiz lifecycle for the AI Study Assistant.
    
    Responsibilities:
    - Generate quizzes using RAG (retriever + LLM)
    - Normalize and validates LLM outputs
    - Store quizzes and questions in the database
    - Evaluate quiz submissions (MCQ + short answers)
    - Track user performance over time
    - Update adaptive learning signals:
        - matery_score (confidence in topic understanding)[range 0-1]
        - difficulty level (adaptive quiz difficulty) (1-5 scale)
    
    Adaptive Learning:
    - mastery_score is updated based on recent performance (weighted update)
    - difficulty is adjusted dynamically:
        - increase if perfomance is high
        - decrease if performance is low
        - clamped between 1-5
    
    Design NotesL:
    - Uses defensive programming (normalization + fallback) for LLm reliability
    - Keeps logic centralized for simplicity (can be modularized later if needed)
    """
    def __init__(
        self,
        db: Session
    ):
        self.db = db
        self.retriever = Retriever(vector_store=vector_store, top_k=8)
        
    def _normalize_quiz_payload(self, payload: dict) -> dict:
        """
        Normalize LLM output into expected schema.

        Handles:
        - Nested structures (e.g., {"quiz": {"questions": [...]}})
        - Alternate keys ("items", "data", etc.)
        - Structural inconsistencies

        Raises:
        - ValueError if payload cannot be normalized

        Purpose:
        - Protect downstream pipeline from LLM variability
        """

        # Case 1: already correct
        if "questions" in payload:
            return payload

        # Case 2: wrapped structure
        for key, value in payload.items():
            if isinstance(value, dict) and "questions" in value:
                return value

        # Case 3: alternative keys
        for alt_key in ["items", "quiz", "data"]:
            if alt_key in payload:
                val = payload[alt_key]  # ✅ FIX: assign first

                if isinstance(val, list):
                    return {"questions": val}

                if isinstance(val, dict) and "questions" in val:
                    return val

        raise ValueError("Invalid LLM output: cannot normalize structure")  
    
    def _fallback_quiz_generation(self, context_chunks, num_questions: int):
        """
        Generate a fallback quiz when LLM output fails validation.

        Behavior:
        - Uses context chunks to create simple short-answer questions
        - Ensures system does not fail due to LLM issues

        Tradeoff:
        - Lower quality than LLM-generated quiz
        - Guarantees system robustness

        Returns:
        - Valid quiz payload with basic questions
        """
        questions = []
        for i, chunk in enumerate(context_chunks[:num_questions]):
            text = chunk.text.strip()
            
            question = f"What is described in the following text?\n{text[:150]}..."
            
            questions.append({
                "question": question,
                "type": "short",
                "correct_answer": text[:200],
                "explanation": "This question is generated as a fallback due to LLM output issues."
            })
        return {"questions": questions}
        
    def generate_quiz(self, user_id: int, topic: str = None, num_questions: int = 5, difficulty: int = None) -> models.Quiz:
        """
        Generte a quiz for a given topic using RAG + LLM.
        
        Flow:
        1. Retrieve relevant context using vector search
        2. Generate quiz via LLM (structured JSON)
        3. Normalize and validate output
        4. Fallback if LLM output is invalid
        5. Persist quiz and questions in DB 
        
        Features:
        - Supports both MCQ and short-answer questions
        - Allows external difficulty override or uses adaptive difficulty
        - Ensures schema consistency via normalization + validation

        Returns:
        - Quiz object stored in DB
        """
        intelligence = IntelligenceService()
        
        # Hybrid topic selection
        if topic:
            topic = normalize_topic(topic)
        else:
            recommendation = intelligence.recommend_smart_topic(user_id=user_id)
            
            if recommendation['topic']:
                topic = recommendation['topic']
            else:
                topics = redis_client.smembers(f"user:{user_id}:topics")
                
                if not topics:
                    raise ValueError(
                        "No topics found for user. Please upload study material first."
                    )
                topic = list(topics)[0]
        
        if not topic or not topic.strip():
            raise ValueError("Topic must be a non-empty string.")
        
        # 1. Get difficulty from progress
        progress = get_user_topic_progress(self.db, user_id, topic)
        
        # difficulty from confidence
        if difficulty is None:
            confidence = intelligence._get_confidence(user_id=user_id, topic=topic)
            
            if confidence < 0.4:
                difficulty = 1
            elif confidence < 0.7:
                difficulty = 2
            else:
                difficulty = 3
                
        # weak topic aware quality
        weak_topics = intelligence._get_weak_topics(user_id, top_k=2)
        
        if weak_topics:
            weak_names = [w["topic"] for w in weak_topics]
            focus = ", ".join(weak_names)
            query = f"{topic} concepts with focus on weak areas: {focus}"
        else:
            query = f"{topic} concepts, definition, applications, explainations, examples"
        # 2. Retrieve context (topic-filtered)
        chunks = self.retriever.retrieve(
            query=query,
            filters={"topic": topic, "user_id": user_id}
        )
        if not chunks:
            raise ValueError(f"No content found for topic: {topic}")
        
        context_text = "\n\n".join(chunk.text for chunk in chunks)
        
        # 3. Generate structure quiz JSON
        quiz_payload = self._generate_quiz_with_llm(
            context=context_text,
            difficulty=difficulty,
            num_questions=num_questions
        )
        try:
            quiz_payload = self._normalize_quiz_payload(quiz_payload)
        except Exception:
            logger.warning("LLM output normalization failed, activating fallback generator.")
            quiz_payload = self._fallback_quiz_generation(chunks, num_questions)
        
        # Safety Validation
        if "questions" not in quiz_payload:
            raise ValueError("Invalid LLM Output: missing 'questions' key.")
        
        if not isinstance(quiz_payload["questions"], list) :
            raise ValueError("Invalid LLM Output: 'questions' must be a list.")  
        
        if len(quiz_payload["questions"]) == 0:
            raise ValueError("LLM returns empty questions list.")
        
        # if len(quiz_payload["questions"]) != num_questions:
        #     raise ValueError(f"LLM Output question count mismatch: expected {num_questions}, got {len(quiz_payload['questions'])}")
        
        # 4. Persist Quiz + Questions
        try:
            quiz = models.Quiz(
                user_id=user_id,
                topic=topic,
                difficulty_level=difficulty,
                total_questions=len(quiz_payload["questions"]),
                status="active",
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(quiz)
            self.db.flush()  # To get quiz.id
            
            for q in quiz_payload["questions"]:
                question = models.Question(
                    quiz_id=quiz.id,
                    question_text=q.get("question"),
                    question_type=q.get("type"),
                    options=q.get("options"),
                    correct_answer=q.get("correct_answer"),
                    explanation=q.get("explanation"),
                    difficulty_level=difficulty,
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(question)
                
            self.db.commit()
            self.db.refresh(quiz)
            
            logger.info(
                "Quiz generated successfully",
                extra={
                    "quiz_id": quiz.id,
                    "user_id": user_id,
                    "topic": topic,
                    "difficulty": difficulty
                }
            )
            return quiz
        
        except Exception as e:
            self.db.rollback()
            logger.exception("Quiz Generation failed.")
            raise
    
    def submit_quiz(self, user_id:int, quiz_id:int, submitted_answers:list, attempt_id: int):
        """
        Evaluate a submitted quiz and update user learning state.

        Flow:
        1. Fetch quiz and questions
        2. Evaluate answers:
            - MCQ → deterministic comparison
            - Short → LLM-based evaluation
        3. Store:
            - QuizAttempt (overall result)
            - QuestionAttempt (per-question result)
        4. Compute:
            - score
            - score_ratio
        5. Update UserTopicProgress:
            - mastery_score (confidence)
            - difficulty level (adaptive adjustment)
            - attempt counters

        Adaptive Logic:
        - mastery_score:
            Weighted update using previous mastery and current performance

        - difficulty:
            Increased if score_ratio is high
            Decreased if score_ratio is low
            Clamped between 1 and 5

        Returns:
        - Evaluation summary (score, difficulty, mastery updates)
        """
        try:
            # 1. Fetch Quiz
            quiz = (
                self.db.query(models.Quiz)
                .filter(models.Quiz.id == quiz_id, models.Quiz.user_id == user_id)
                .first()
            )
            
            attempt = (
                self.db.query(models.QuizAttempt).filter(
                    models.QuizAttempt.id == attempt_id,
                    models.QuizAttempt.user_id == user_id,
                    models.QuizAttempt.quiz_id == quiz_id
                ).first()
            )
            
            if not attempt:
                raise ValueError("Quiz attempt not found.")
            
            if not quiz:
                raise ValueError("Quiz not found.")
            
            # 2. Validate ownership and status
            if quiz.user_id != user_id:
                raise ValueError("Unauthorized: Quiz does not belong to the user.")
            
            # 3. Prevent Re-submission
            if quiz.status == "completed":
                raise ValueError("Quiz has already been completed.")
            
            # 4. Load questions
            questions = (
                self.db.query(models.Question)
                .filter(models.Question.quiz_id == quiz_id)
                .all()
            )
            if not questions:
                raise ValueError("No questions found for this quiz.")
            
            question_map = {q.id: q for q in questions}
            
            # 5. Validate submitted answers
            if len(submitted_answers) != len(questions):
                raise ValueError("Number of submitted answers does not match number of questions.")
            
            # Prepare grading counters
            correct_count = 0
            total_questions = len(questions)
            
            # temporary grading placeholder
            graded_results = []
            for item in submitted_answers:
                question_id = item.question_id
                user_answer = item.answer.strip()
                
                if question_id not in question_map:
                    raise ValueError(f"Invalid question ID: {question_id}")
                
                question = question_map[question_id]
                
                correct_answer = question.correct_answer.strip()
                
                # MCQ Grading
                if question.question_type == "mcq":
                    is_correct = (
                        user_answer.lower() == correct_answer.lower()
                    )
                    
                # Short Answer Grading
                elif question.question_type == "short":
                    correct_keywords = set(
                        correct_answer.lower().split()
                    )
                    user_words = set(
                        user_answer.lower().split()
                    )
                    
                    if not correct_keywords:
                        is_correct = False
                    else:
                        overlap = correct_keywords.intersection(user_words)
                        overlap_ratio = len(overlap) / len(correct_keywords)
                        is_correct = overlap_ratio >= 0.5  # Threshold can be tuned
                
                else:
                    is_correct = False  # Unknown question type
                    
                if is_correct:
                    correct_count += 1
                
                graded_results.append({
                    "question": question,
                    "user_answer": user_answer,
                    "is_correct": is_correct
                })
            # Do not commit yet - grading logic comes next
            # 1. Compute score
            score_ratio = correct_count / total_questions
            
            # 2. Create QuizAttempt record
            # quiz_attempt = models.QuizAttempt(
            #     user_id=user_id,
            #     quiz_id=quiz_id,
            #     score=correct_count,
            #     score_ratio=score_ratio,
            #     max_score=total_questions,
            #     confidence_score=score_ratio,  # v1: use score ratio as confidence proxy (Week 5 will improve)
            #     time_taken_seconds=None,  # To be updated when we track start time
            #     submitted_at=datetime.now(timezone.utc)
            # )
            
            end_time = datetime.now(timezone.utc)
            if attempt.start_time:
                time_taken = int((end_time - attempt.start_time).total_seconds())
            else:
                time_taken = None
            
            attempt.submitted_at = end_time
            attempt.time_taken_seconds = time_taken
            attempt.score = correct_count
            attempt.score_ratio = score_ratio
            attempt.confidence_score = score_ratio  # v1 proxy
            attempt.max_score = total_questions
            
            # 3. Create QuestionAttempt records
            for result in graded_results:
                question = result["question"]
                
                question_attempt = models.QuestionAttempt(
                    quiz_attempt_id=attempt.id,
                    question_id=question.id,
                    user_answer=result["user_answer"],
                    is_correct=1 if result["is_correct"] else 0,
                    score = 1.0 if result["is_correct"] else 0.0,
                    confidence_score = score_ratio, # simple v1
                    answered_at=datetime.now(timezone.utc)
                )
                self.db.add(question_attempt)
            
            # 4. Update UserTopicProgress
            progress = get_user_topic_progress(self.db, user_id, quiz.topic)
            if not progress:
                progress = models.UserTopicProgress(
                    user_id=user_id,
                    topic=normalize_topic(quiz.topic),
                    current_difficulty=quiz.difficulty_level,
                    mastery_score=0.0,
                    last_attempt_at=None,
                    total_attempts=0,
                    correct_attempts=0,
                    updated_at=datetime.now(timezone.utc)
                )
                self.db.add(progress)
                self.db.flush()
                
            previous_mastery = progress.mastery_score
            previous_attempts = progress.total_attempts
            current_difficulty = progress.current_difficulty

            # Running average mastery
            new_mastery = (
                (previous_mastery * previous_attempts) + score_ratio
            ) / (previous_attempts + 1)

            # Difficulty adjustment (1–5 scale)
            if score_ratio >= 0.8:
                new_difficulty = min(current_difficulty + 1, 5)
            elif score_ratio <= 0.4:
                new_difficulty = max(current_difficulty - 1, 1)
            else:
                new_difficulty = current_difficulty

            # Update progress fields
            progress.mastery_score = new_mastery
            progress.current_difficulty = new_difficulty
            progress.total_attempts = previous_attempts + 1
            progress.correct_attempts += correct_count
            progress.last_attempt_at = datetime.now(timezone.utc)
            progress.updated_at = datetime.now(timezone.utc)

            # -----------------------
            # 5️⃣ Mark Quiz Completed
            # -----------------------
            quiz.status = "completed"
            quiz.completed_at = datetime.now(timezone.utc)

            # -----------------------
            # 6️⃣ Commit Transaction
            # -----------------------
            self.db.commit()
            logger.info(
                "Quiz submitted and evaluated successfully",
                extra={
                    "quiz_id": quiz.id,
                    "user_id": user_id,
                    "topic": quiz.topic,
                    "score_ratio": score_ratio,
                    "new_mastery": new_mastery,
                    "new_difficulty": new_difficulty
                }
            )
        except Exception as e:
            self.db.rollback()
            logger.exception("Error processing quiz submission.")
            raise
        
        # Intelligence Layer Update (Redis)
        try:
            intelligence = IntelligenceService()
            intelligence.process_attempt(
                user_id=user_id,
                topic=quiz.topic,
                score_ratio=score_ratio,
                time_taken=time_taken or 0,
                difficulty=quiz.difficulty_level,
                mastery_score=new_mastery
            )
            logger.info(f"Intelligence signals updated for user {user_id}, topic {quiz.topic}")
        except Exception as e:
            logger.error(f"Error updating intelligence signals: {e}")

        return {
            "quiz_id": quiz.id,
            "score_ratio": round(score_ratio, 3),
            "correct_answers": correct_count,
            "total_questions": total_questions,
            "new_difficulty": new_difficulty,
            "updated_mastery": round(new_mastery, 3),
            "time_taken_seconds": time_taken,
            "question_breakdown": [
                {
                    "question_id": r["question"].id,
                    "question_text": r["question"].question_text,
                    "question_type": r["question"].question_type,
                    "options": r["question"].options,
                    "user_answer": r["user_answer"],
                    "correct_answer": r["question"].correct_answer,
                    "explanation": r["question"].explanation,
                    "is_correct": r["is_correct"],
                }
                for r in graded_results
            ],
        }
        
    def start_quiz(self, user_id: int, quiz_id: int):
        """
        Start the Quiz attempt and record start_time.

        - Creates a new QuizAttempt with the start time when the user initiates the quiz.
        - Stores the start time.
        - Returns attempt_id
        """
        try:
            quiz = (
                self.db.query(models.Quiz).filter(models.Quiz.id == quiz_id, models.Quiz.user_id == user_id).first()
            )
            
            if not quiz:
                raise ValueError("Quiz not found.")
            
            # Create a attempt with start time
            attempt = models.QuizAttempt(
                quiz_id=quiz.id,
                user_id=user_id,
                start_time=datetime.now(timezone.utc)
            )
            
            self.db.add(attempt)
            self.db.commit()
            self.db.refresh(attempt)
            logger.info(f"Quiz attempt started for user {user_id}, quiz {quiz_id}, attempt {attempt.id}")
            return {
                "attempt_id": attempt.id,
                "start_time": attempt.start_time
            }
        except Exception as e:
            logger.error(f"Error starting quiz attempt for user {user_id}, quiz {quiz_id} in start_quiz function: {e}")
            raise
        
    def _generate_quiz_with_llm(self, context: str, difficulty: int, num_questions: int) -> dict:
        """
        Generate quiz questions using LLM based on retrieved context.

        Responsibilities:
        - Construct prompt with strict schema instructions
        - Enforce MCQ + short question mix
        - Inject difficulty constraints
        - Parse structured JSON output

        Notes:
        - LLM output is not guaranteed → must be validated later
        - Prompt encourages diversity in question types and reasoning

        Returns:
        - Raw quiz payload (dict)
        """
        
        prompt = f"""
        You are generating a quiz.

        STRICT RULES (VERY IMPORTANT):
        - Output must be a valid JSON only.
        - Do NOT include any explaination, text, or formatting outside JSON.
        - Do NOT include markdown.
        - Do NOT include comments.
        
        FORMAT EXACTLY LIKE THIS:
        {{
            "questions": [
                {{
                    "question": "...?",
                    "type": "mcq" or "short",
                    "options": ["A", "B", "C", "D"] (only if type is mcq),
                    "correct_answer": "...",
                    "explanation": "..." (optional, but helpful for study assistant feedback)
                }}
            ]
        }}
        
        CONSTRAINTS:
        - Generate exactly {num_questions} questions.
        - Difficulty level = {difficulty}
        
        QUESTION TYPE RULES:
        - At least 50% should be MCQs with 4 options
        - Remaining short answer questions
        
        DIFICULTY RULES:
        - Easy (1-2): direct factual questions.
        - Medium (3): conceptual understanding
        - Hard (4-5): reasoning + application based questions
        
        MCQ RULES:
        - MUST include exactly 4 options
        - Distractors should be relevant and commonly confused with the correct answer
        - Correct answer should be clearly supported by the context, not ambiguous.
        - Options must be meaningful text (not A/B/C/D)
        - The "correct_answer" MUST be one of: "A", "B", "C", or "D"
        - DO NOT return the full text answer in correct_answer
        - Example:
            options: ["Object classification", "Image segmentation", "Clustering", "Regression"]
            correct_answer: "A"
        
        SHORT RULES:
        - Clear, answerable from context
        - MUST include "correct_answer" field with the ideal answer
        - Explanation "explaination" field is highly recommended to clarify the reasoning
        
        Context:
        {context}
        """

        return generate_json_completion(prompt)
        