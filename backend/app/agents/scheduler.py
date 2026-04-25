from datetime import datetime, timedelta
from app.utils.logging import get_logger

logger = get_logger(__name__)

class Scheduler:
    """
    Converts plan -> weekly schedule
    """
    
    def generate_weekly_schedule(self, plan: list):
        """Map each plan item to a calendar day starting from today, one item per day."""
        try:
            logger.info("Generating weekly schedule from plan")
            today = datetime.now()
            schedule = []
            
            for i, item in enumerate(plan):
                day = today + timedelta(days=i)
                schedule.append({
                    "day": day.strftime("%A"),
                    "date": day.strftime("%Y-%m-%d"),
                    "topic": item['topic'],
                    "task": item['task'],
                    "priority": item['priority']
                })
            
            return schedule
        except Exception as e:
            logger.error(f"Error in Scheduler - {str(e)}")
            return []