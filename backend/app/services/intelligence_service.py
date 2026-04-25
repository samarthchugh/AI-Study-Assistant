import json
import time
import math
from app.config import redis_client
from app.utils.logging import get_logger
from app.utils.topic_utils import normalize_topic

logger = get_logger(__name__)   

class IntelligenceService:
    
    def __init__(self):
        self.redis = redis_client
        self.max_attempts = 20 
        
    def _attempts_key(self, user_id: int, topic: str) -> str:
        return f"user:{user_id}:topic:{topic}:attempts"
    
    def _record_attempt(
        self,
        user_id: int,
        topic: str,
        score_ratio: float,
        time_taken: int,
        difficulty: int,
    ):
        """
        Store a quiz attempt in Redis for recency tracking and adaptive learning.
        """
        
        try:
            key = self._attempts_key(user_id, topic)
            
            attempt_data = {
                "score_ratio": score_ratio,
                "time_taken": time_taken,
                "difficulty": difficulty,
                "timestamp": int(time.time())
            }
            
            # convert to JSON string for storage
            attempt_json = json.dumps(attempt_data)
            
            # Push to Redis (newest first)
            self.redis.lpush(key, attempt_json)
            
            # keep only last N attempts
            self.redis.ltrim(key, 0, self.max_attempts - 1)
            
            # Optional: set TTL (for future forgetting curve)
            self.redis.expire(key, 60 * 60 * 24 * 7)  # keep for 30 days
            logger.info(f"Recorded attempt for user {user_id}, topic {topic}, score_ratio {score_ratio}, time_taken {time_taken}, difficulty {difficulty}")
        except Exception as e:
            logger.error(f"Error recording attempt for user {user_id}, topic {topic}: {e}")

    def _get_recent_attempts(self, user_id: int, topic: str):
        """
        Fetch and parse recent attempts from Redis.
        Returns a list of dicts with attempt data.
        """
        try:
            key = self._attempts_key(user_id, topic)
            
            # get all attempts (newest first)
            attempts_new = self.redis.lrange(key, 0, -1)
            
            attempts = []
            
            for item in attempts_new:
                try:
                    attempt_data = json.loads(item)
                    attempts.append(attempt_data)
                except json.JSONDecodeError:
                    # skip corrupted entries (defensive programming)
                    logger.warning(f"Corrupted attempt data for user {user_id}, topic {topic}")
                    continue  
                
            logger.info(f"Fetched {len(attempts)} attempts for user {user_id}, topic {topic}")
            return attempts
        except Exception as e:
            logger.error(f"Error fetching attempts for user {user_id}, topic {topic}: {e}")
            return []
    
    def _compute_recency_score(self, attempts: list, lambda_decay: float = 0.3) -> float:
        """
        Compute a recency-weighted score based on past attempts.
        More recent attempts have higher weight.
        """
        try:
            if not attempts:
                return 0.0
            
            weighted_sum = 0.0
            weight_total = 0.0
            
            for i, attempt in enumerate(attempts):
                score = attempt.get("score_ratio", 0.0)
                
                weight = math.exp(-lambda_decay * i)  # exponential decay based on recency
                
                weighted_sum += score * weight
                weight_total += weight
                
            
            if weight_total == 0:
                return 0.0
            
            logger.info(f"Computed recency score: weighted_sum={weighted_sum}, weight_total={weight_total}, recency_score={weighted_sum / weight_total}")
            
            return weighted_sum / weight_total
        except Exception as e:
            logger.error(f"Error computing recency score: {e}")
            return 0.0
        
    def _compute_confidence(self, recency_score: float, master_score: float, alpha: float  = 0.7):
        """
        Combine recency score and master score to compute an overall confidence level.
        alpha controls the weighting between recency and mastery.
        """
        try:
            # Safety clamping
            recency_score = max(0.0, min(1.0, recency_score))
            master_score = max(0.0, min(1.0, master_score))
            
            confidence = (alpha * recency_score) + ((1 - alpha) * master_score) 
            
            logger.info(f"Computed confidence: recency_score={recency_score}, master_score={master_score}, confidence={confidence}")
            
            return round(confidence, 4)
            
        except Exception as e:
            logger.error(f"Error computing confidence: {e}")
            return 0.0
        
    def _update_weak_topics(self, user_id: int, topic: str, confidence: float):
        """
        Update weak topic ranking using Redis ZSET.
        Higher score = weaker topic.
        """
        
        try:
            key = f"user:{user_id}:weak_topics"
            
            # convert confidence to weakness score (inverse)
            weakness_score = 1.0 - confidence
            
            # store in ZSET with topic as member and weakness score as score
            self.redis.zadd(key, {topic: weakness_score})
            logger.info(f"Updated weak topic for user {user_id}, topic {topic}, confidence {confidence}, weakness_score {weakness_score}")
        except Exception as e:
            logger.error(f"Error updating weak topics for user {user_id}, topic {topic}: {e}")
            
    
    def process_attempt(
        self,
        user_id: int,
        topic: str,
        score_ratio: float,
        time_taken: int,
        difficulty: int,
        mastery_score: float
    ):
        try:
            topic = normalize_topic(topic)
            # 1. Store attempt
            self._record_attempt(user_id, topic, score_ratio, time_taken, difficulty)

            # 2. Fetch attempts
            attempts = self._get_recent_attempts(user_id, topic)

            # 3. Recency
            recency_score = self._compute_recency_score(attempts)

            # 4. Confidence
            confidence = self._compute_confidence(recency_score, mastery_score)

            # 5. Store confidence
            self.redis.set(
                f"user:{user_id}:topic:{topic}:confidence",
                confidence
            )

            # 6. Weak topics
            self._update_weak_topics(user_id, topic, confidence)
            logger.info(f"Processed attempt for user {user_id}, topic {topic}, score_ratio {score_ratio}, time_taken {time_taken}, difficulty {difficulty}, mastery_score {mastery_score}, recency_score {recency_score}, confidence {confidence}")    

            return confidence
        except Exception as e:
            logger.error(f"Error processing attempt for user {user_id}, topic {topic}: {e}")
            return 0.0
        
    def _get_confidence(self, user_id: int, topic: str):
        key = f"user:{user_id}:topic:{topic}:confidence"
        value = self.redis.get(key)
        return float(value) if value else 0.0
        
    def _get_weak_topics(self, user_id: int, top_k: int = 5):
        try:
            key = f"user:{user_id}:weak_topics"
            results = self.redis.zrevrange(key, 0, top_k - 1, withscores=True)
            
            return [
                {"topic": topic, "weakness": score, "confidence": 1 - score}
                for topic, score in results
            ]
        except Exception as e:
            logger.error(f"Enable to fetch weak topics:({e})")
            return []
            
    def recommend_topic(self, user_id: int):
        """
        Decide the best topic for the user to study next
        """
        try:
            # Try weakest topic
            weak_topics = self._get_weak_topics(user_id)
            
            if weak_topics:
                logger.info(f"Recommended topic for user {user_id} based on weak topics: {weak_topics[0]['topic']}")
                return {
                    "topic": weak_topics[0]["topic"],
                    "reason": "weak_topic"
                }
                
            # Fallback: recommend a latest topic
            topics = self.redis.smembers(f"user:{user_id}:topics")
            
            if topics:
                logger.info(f"Recommended topic for user {user_id} based on fallback: {list(topics)[0]}")
                return {
                    "topic": list(topics)[0],
                    "reason": "fallback_topic"
                }
                
            # NO topics -> New user
            return {
                "topic": None,
                "reason": "no_content"
            }
        except Exception as e:
            logger.error(f"Error recommending topic for user {user_id}: {e}")
            return {
                "topic": None,
                "reason": "error"
            }
            
    def _compute_forgetting_score(self, last_attempts_ts: int, confidence: float, lambda_decay: float = 0.1):
        """
        Compute how much the user might have forgotten a topic based on time since last attempt and confidence level.
        
        Returns:
        - retention score (0 to 1): higher means better retention, lower means more likely forgotten
        """
        try:
            if not last_attempts_ts:
                return 0.0  # No attempts means no forgetting (or unknown)
            now  = int(time.time())
            time_gap = (now - last_attempts_ts) / 3600  # scale to hours
            retention = confidence * math.exp(-lambda_decay * time_gap)
            
            return max(0.0, min(1.0, retention))  # clamp to [0, 1]
        except Exception as e:
            logger.error(f"Error computing forgetting score: {e}")
            return 0.0
        
    def _get_last_attempt_time(self, user_id: int, topic: str):
        try:
            attempts = self._get_recent_attempts(user_id, topic)
            if not attempts:
                return None
            return attempts[0].get("timestamp")  # newest attempt timestamp
        except json.JSONDecodeError:
            logger.warning(f"Corrupted last attempt data for user {user_id}, topic {topic}")
            return 0
        
    def get_revision_topics(self, user_id: int, top_k: int = 3):
        """
        Return Topics that need revision based on forgetting curve.
        Only includes topics where the user has attempted at least one quiz —
        the forgetting curve requires a real baseline score to be meaningful.
        """
        try:
            topics = self.redis.smembers(f"user:{user_id}:topics")

            revision_scores = []

            for topic in topics:
                topic = normalize_topic(topic)
                last_ts = self._get_last_attempt_time(user_id, topic)
                if last_ts is None:
                    continue  # no quiz attempt yet — nothing to revise
                confidence = self._get_confidence(user_id, topic)
                retention = self._compute_forgetting_score(last_ts, confidence)
                revision_priority = 1 - retention  # higher means more urgent revision
                revision_scores.append({
                    "topic": topic,
                    "confidence": confidence,
                    "retention": retention,
                    "revision_priority": round(revision_priority, 4)
                })
                
            # Sort by highest priority
            revision_scores.sort(key=lambda x: x["revision_priority"], reverse=True)
            
            return revision_scores[:top_k]
        except Exception as e:
            logger.error(f"Error getting revision topics for user {user_id}: {e}")
            return []
        
    def recommend_smart_topic(self, user_id: int):
        """
        Smart Recommendation combining:
        - Weak topics(performance)
        - Forgetten topics (time decay)
        """
        try:
            topics = self.redis.smembers(f"user:{user_id}:topics")
            if not topics:
                return {
                    "topic": None,
                    "reason": "no_content"
                }
            
            scored_topics = []
            
            for topic in topics:
                topic = normalize_topic(topic)
                
                # 1. Confidence -> weakness
                confidence = self._get_confidence(user_id, topic)
                weakness = 1 - confidence
                
                # 2. Forgetting score
                last_ts = self._get_last_attempt_time(user_id, topic)
                retention = self._compute_forgetting_score(last_ts, confidence)
                forgetting = 1 - retention
                
                # 3. Combined score
                score =(0.6 * weakness) + (0.4 * forgetting)  # weights can be tuned
                
                scored_topics.append({
                    "topic": topic,
                    "confidence": confidence,
                    "weakness": weakness,
                    "retention": retention,
                    "forgetting": forgetting,
                    "combined_score": round(score, 4)
                })
            #  sort highest priority first
            scored_topics.sort(key=lambda x: x["combined_score"], reverse=True)
            
            best = scored_topics[0]
            
            return {
                "topic": best["topic"],
                "reason": "smart_recommendation",
                "details": best
            }
        except Exception as e:
            logger.error(f"Error recommending smart topic for user {user_id}: {e}")
            return {
                "topic": None,
                "reason": "error"
            }