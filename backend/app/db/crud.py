from sqlalchemy.orm import Session
from app.db import models

def get_user_topic_progress(db: Session, user_id: int, topic: str):
    return (
        db.query(models.UserTopicProgress)
        .filter(
            models.UserTopicProgress.user_id == user_id,
            models.UserTopicProgress.topic == topic
        )
        .first()
    )