from app.services.intelligence_service import IntelligenceService

service = IntelligenceService()

# service._record_attempt(
#     user_id=1,
#     topic="graphs",
#     score_ratio=0.8,
#     time_taken=40,
#     difficulty=3
# )

R = 0.4   # recent performance dropped
M = 0.8   # historical mastery

service._update_weak_topics(1, "graphs", 0.4)   # weak
service._update_weak_topics(1, "arrays", 0.8)   # strong

# C = service._compute_confidence(R, M)
# print(C)
