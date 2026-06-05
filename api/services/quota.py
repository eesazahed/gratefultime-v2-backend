from datetime import datetime, timezone

from api.config import settings
from api.db import ai_usage
from api.db.users import User


def get_ai_previews_remaining(user: User) -> int:
    if user.is_plus:
        return -1

    now = datetime.now(timezone.utc)
    if ai_usage.count_for_month(user.user_id, now.year, now.month) >= settings.free_ai_previews_per_month:
        return 0

    return settings.free_ai_previews_per_month


def has_exhausted_free_quota(user_id: int, year: int, month: int) -> bool:
    return ai_usage.count_for_month(user_id, year, month) >= settings.free_ai_previews_per_month


def increment_usage(user_id: int, year: int, month: int) -> None:
    ai_usage.record_usage(user_id, year, month)
