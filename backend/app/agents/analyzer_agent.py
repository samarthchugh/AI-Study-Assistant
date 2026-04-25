from app.services.intelligence_service import IntelligenceService
from app.utils.logging import get_logger
from app.utils.topic_utils import normalize_topic

logger = get_logger(__name__)

class AnalyzerAgent:
    """
    Reads user learning state and prepares structured analysis
    """
    
    def run(self, user_id: int):
        """Fetch weak topics, revision topics, and a smart recommendation for the user from Redis."""
        intelligence = IntelligenceService()
        
        try:
            logger.info(f"Running AnalyzerAgent for user_id: {user_id}")
            weak_topics = intelligence._get_weak_topics(user_id)
            revision_topics = intelligence.get_revision_topics(user_id)
            recommendation = intelligence.recommend_smart_topic(user_id)

            return {
                "weak_topics": weak_topics,
                "revision_topics": revision_topics,
                "recommend": recommendation
            }
        except Exception as e:
            logger.error(f"Error in AnalyzerAgent for user_id: {user_id} - {str(e)}")
            return {
                "weak_topics": [],
                "revision_topics": [],
                "recommend": None
            }