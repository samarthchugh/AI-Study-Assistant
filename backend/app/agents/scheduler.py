from datetime import datetime, timedelta
from app.utils.logging import get_logger

logger = get_logger(__name__)

WEEK_DAYS = 7
MAINTAIN_DAYS = [0, 3, 6]       # 3×/week for strong topics
SINGLE_TOPIC_DAYS = [0, 2, 5]   # 3 spread days for a single weak topic


class Scheduler:
    """
    Converts plan -> weekly schedule.

    Cadence rules:
    - maintain only          → 3 days at offsets 0, 3, 6
    - single weak topic      → 3 days at offsets 0, 2, 5  (+ maintain at day 3 if present)
    - multiple weak topics   → 7 days cycling through all priority items,
                               each maintain item slotted in once on a maintain day
    """

    def _make_entry(self, today: datetime, day_offset: int, item: dict) -> dict:
        day = today + timedelta(days=day_offset)
        return {
            "day": day.strftime("%A"),
            "date": day.strftime("%Y-%m-%d"),
            "topic": item["topic"],
            "task": item["task"],
            "priority": item["priority"],
        }

    def generate_weekly_schedule(self, plan: list):
        try:
            logger.info("Generating weekly schedule from plan")
            if not plan:
                return []

            today = datetime.now()
            priority_items = [i for i in plan if i["task"] != "maintain"]
            maintain_items = [i for i in plan if i["task"] == "maintain"]

            # ── Maintain-only plan ────────────────────────────────────────────
            if not priority_items:
                schedule = []
                for slot_idx, day_offset in enumerate(MAINTAIN_DAYS):
                    item = maintain_items[slot_idx % len(maintain_items)]
                    schedule.append(self._make_entry(today, day_offset, item))
                return schedule

            unique_topics = {i["topic"] for i in priority_items}

            # ── Single weak topic: 3 spread days (revise → practice → practice)
            if len(unique_topics) == 1:
                revise_item  = next((i for i in priority_items if i["task"] == "revise"),  priority_items[0])
                practice_item = next((i for i in priority_items if i["task"] == "practice"), priority_items[-1])
                ordered = [revise_item, practice_item, practice_item]
                schedule = []
                for slot_idx, day_offset in enumerate(SINGLE_TOPIC_DAYS):
                    schedule.append(self._make_entry(today, day_offset, ordered[slot_idx]))
                # slot maintain item mid-week (day 3) if present
                if maintain_items:
                    schedule.append(self._make_entry(today, 3, maintain_items[0]))
                schedule.sort(key=lambda x: x["date"])
                return schedule

            # ── Multiple weak topics: 2×n days (one revise+practice per topic) ─
            # Each unique topic gets exactly one revise slot + one practice slot.
            # Total days = 2 × n, capped at 7.
            target_days = min(2 * len(unique_topics), WEEK_DAYS)

            # Build ordered list: for each topic, revise first then practice
            ordered_priority = []
            for topic in sorted(unique_topics):
                revise  = next((i for i in priority_items if i["topic"] == topic and i["task"] == "revise"),  None)
                practice = next((i for i in priority_items if i["topic"] == topic and i["task"] == "practice"), None)
                if revise:
                    ordered_priority.append(revise)
                if practice:
                    ordered_priority.append(practice)

            # Distribute maintain slots evenly within the target days
            maintain_offsets = [int(target_days * (k + 1) / (len(maintain_items) + 1))
                                 for k in range(len(maintain_items))] if maintain_items else []

            schedule = []
            priority_idx = 0
            maintain_used = 0

            for day_offset in range(target_days):
                if maintain_used < len(maintain_items) and day_offset == maintain_offsets[maintain_used]:
                    schedule.append(self._make_entry(today, day_offset, maintain_items[maintain_used]))
                    maintain_used += 1
                else:
                    item = ordered_priority[priority_idx % len(ordered_priority)]
                    priority_idx += 1
                    schedule.append(self._make_entry(today, day_offset, item))

            return schedule
        except Exception as e:
            logger.error(f"Error in Scheduler - {str(e)}")
            return []