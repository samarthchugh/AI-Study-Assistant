def normalize_topic(topic: str) -> str:
    """Lowercase and strip whitespace from a topic string for consistent Redis key and DB lookups."""
    return topic.strip().lower()