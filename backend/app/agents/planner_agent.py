from app.utils.logging import get_logger

logger = get_logger(__name__)

class PlannerAgent:
    """
    Converts analysis -> actionable study plan
    """
    def run(self, analysis: dict):
        try:
            logger.info("Running PlannerAgent with analysis data")
            weak_topics =analysis.get("weak_topics", [])
            revision_topics = analysis.get("revision_topics", [])
            
            plan =[]
            used_topics =set()
            
            # 1. Priority 1 - Revision (forgotten topics)
            for t in revision_topics[:3]:
                topic = t['topic']
                if topic in used_topics:
                    continue
                # revise first
                plan.append({
                    "topic": topic,
                    "task": "revise",
                    "priority": "high"
                })
                
                # Then practice same topic
                plan.append({
                    "topic":topic,
                    "task": "practice",
                    "priority": "medium"
                })
                used_topics.add(topic)
                
            # 2. Priority 2 - Weak topics (struggling topics)
            for t in weak_topics[:2]:
                topic = t['topic']
                
                if topic in used_topics:
                    continue
                
                plan.append({
                    "topic": topic,
                    "task": "practice",
                    "priority": "medium"
                })
                used_topics.add(topic)
                
            return plan
        except Exception as e:
            logger.error(f"Error in PlannerAgent - {str(e)}")
            return []