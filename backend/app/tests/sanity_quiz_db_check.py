from app.db.session import SessionLocal
from app.db.models import Quiz, UserTopicProgress

db = SessionLocal()

progress = UserTopicProgress(user_id=1, topic="Machine Learning")
db.add(progress)
db.commit()

print("Inserted successfully")
# from app.db.session import SessionLocal
# from app.db.models import User

# db = SessionLocal()

# user = User(
#     email="test@example.com",
#     hashed_password="fakehash",
#     provider="local"
# )

# db.add(user)
# db.commit()

# print("User created with ID:", user.id)