from datetime import datetime, timezone

from api.db.client import get_supabase


def count_for_month(user_id: int, year: int, month: int) -> int:
    response = (
        get_supabase()
        .table("ai_usage")
        .select("*", count="exact", head=True)
        .eq("user_id", user_id)
        .eq("year", year)
        .eq("month", month)
        .execute()
    )
    return response.count or 0


def record_usage(user_id: int, year: int, month: int) -> None:
    if count_for_month(user_id, year, month) > 0:
        return

    get_supabase().table("ai_usage").insert({
        "user_id": user_id,
        "year": year,
        "month": month,
        "created_at": datetime.now(timezone.utc).isoformat()
    }).execute()
