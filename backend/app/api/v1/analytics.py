from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.services.intelligence_service import IntelligenceService
from app.utils.topic_utils import normalize_topic
from app.dependencies import get_current_user
from app.db.session import get_db
from app.agents.graph import app_graph
from app.utils.logging import get_logger
from app.config import redis_client

logger = get_logger(__name__)
router = APIRouter(prefix = "/analytics", tags = ["ANALYTICS"])

@router.get("/weak-topics")
def weak_topics(db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    service = IntelligenceService()
    
    try:
        logger.info(f"Fetching weak topics for user_id: {current_user}")
        weak_topics = service._get_weak_topics(user_id=int(current_user), top_k=5)
        
        return {
            "user_id": int(current_user),
            "weak_topics": weak_topics
        }
    except Exception as e:
        logger.error(f"Error fetching weak topics for user_id: {current_user}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/confidence")
def topic_confidence(topic: str, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    service = IntelligenceService()
    
    try:
        logger.info(f"Fetching confidence for user_id: {current_user}, topic: {topic}")
        topic = normalize_topic(topic)
        
        confidence = service._get_confidence(
            user_id=int(current_user),
            topic=topic
        )
        
        return {
            "user_id": int(current_user),
            "topic": topic,
            "confidence": round(confidence, 4)
        }
    except Exception as e:
        logger.error(f"Error fetching confidence for user_id: {current_user}, topic: {topic}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
    
@router.get("/all-topics")
def get_all_topics(db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    try:
        logger.info(f"Fetching all topics for user_id: {current_user}")

        key = f"user:{int(current_user)}:topics"
        topics = redis_client.smembers(key)
        
        return {
            "user_id": int(current_user),
            "topics": list(topics)
        }
    except Exception as e:
        logger.error(f"Error fetching all topics for user_id: {current_user}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/overview")
def analytics_overview(db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    service = IntelligenceService()
    user_id = int(current_user)
    
    try:
        logger.info(f"Fetching analytics overview for user_id: {user_id}")
        # Get all topics
        topics_key = f"user:{user_id}:topics"
        topics = list(redis_client.smembers(topics_key))
        
        # get weak topics
        weak_topics = service._get_weak_topics(user_id = user_id, top_k = 5)
        
        # Build confidence map
        confidence_map = {}
        
        for topic in topics:
            normalized_topic = normalize_topic(topic)
            
            confidence = service._get_confidence(
                user_id = user_id,
                topic = normalized_topic
            )
            
            confidence_map[normalized_topic] = round(confidence, 4)
        logger.info(f"Analytics overview fetched successfully for user_id: {user_id}")
        return {
            "user_id": user_id,
            "topics": topics,
            "weak_topics": weak_topics,
            "confidence_map": confidence_map
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics overview for user_id: {user_id}: {e}")
        raise HTTPException(status_code = 500, detail = str(e))
    
@router.get("/recommend")
def recommend_topic(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    intelligence = IntelligenceService()
    try:
        logger.info(f"Recommending topic for user_id: {current_user_id}")
        result = intelligence.recommend_topic(user_id=int(current_user_id))
        
        if result["reason"] == "no_content":
            return {
                "status": "no_content",
                "message": "Upload study material first."
            }
            
        return {
            "recommended_topic": result["topic"],
            "reason": result["reason"]
        }
    except Exception as e:
        logger.error(f"Error recommending topic for user_id: {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/revision")
def get_revision_topics(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
    top_k: int = 3
):
    intelligence = IntelligenceService()
    try:
        logger.info(f"Fetching revision topics for user_id: {current_user_id}")
        result = intelligence.get_revision_topics(user_id=int(current_user_id))
        
        return {
            "user_id": int(current_user_id),
            "revision_topics": result
        }
    except Exception as e:
        logger.error(f"Error fetching revision topics for user_id: {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/recommend-smart")
def recommend_smart(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    intelligence = IntelligenceService()
    try:
        logger.info(f"Fetching smart recommendation for user_id: {current_user_id}")
        result = intelligence.recommend_smart_topic(user_id=int(current_user_id))
        
        if result["reason"] == "no_content":
            return {
                "status": "no_content",
                "message": "Upload study material first."
            }
            
        return {
            "recommended_topic": result["topic"],
            "reason": result
        }
    except Exception as e:
        logger.error(f"Error fetching smart recommendation for user_id: {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/weekly-plan")
def weekly_plan(current_user: int = Depends(get_current_user)):
    try:
        result = app_graph.invoke({
            "user_id": int(current_user)
        })
        
        return {
            "user_id": int(current_user),
            "weekly_plan": result['schedule']
        }
    except Exception as e:
        raise HTTPException(status_code = 500, detail=str(e))
    