from dataclasses import dataclass
from datetime import datetime

from api.db.client import get_supabase


class UserDbError(Exception):
    pass


@dataclass
class User:
    user_id: int
    username: str | None
    email: str | None
    user_timezone: str
    apple_user_id: str | None
    is_plus: bool
    plus_expires_at: datetime | None
    created_at: datetime | None

    @classmethod
    def from_row(cls, row: dict) -> "User":
        return cls(
            user_id=row["user_id"],
            username=row.get("username"),
            email=row.get("email"),
            user_timezone=row.get("user_timezone") or "America/New_York",
            apple_user_id=row.get("apple_user_id"),
            is_plus=bool(row.get("is_plus", False)),
            plus_expires_at=_parse_timestamp(row.get("plus_expires_at")),
            created_at=_parse_timestamp(row.get("created_at"))
        )


def _parse_timestamp(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def find_by_apple_user_id(apple_user_id: str) -> User | None:
    response = (
        get_supabase()
        .table("users")
        .select("*")
        .eq("apple_user_id", apple_user_id)
        .maybe_single()
        .execute()
    )
    if response.data:
        return User.from_row(response.data)
    return None


def find_by_id(user_id: int) -> User | None:
    response = (
        get_supabase()
        .table("users")
        .select("*")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if response.data:
        return User.from_row(response.data)
    return None


def find_by_email_insensitive(email: str) -> User | None:
    response = (
        get_supabase()
        .table("users")
        .select("*")
        .ilike("email", email)
        .limit(1)
        .execute()
    )
    if response.data:
        return User.from_row(response.data[0])
    return None


def create_user(**fields) -> User:
    response = get_supabase().table("users").insert(fields).execute()
    if not response.data:
        raise UserDbError("Failed to create user")
    return User.from_row(response.data[0])


def update_user(user_id: int, **fields) -> User | None:
    response = (
        get_supabase()
        .table("users")
        .update(fields)
        .eq("user_id", user_id)
        .execute()
    )
    if response.data:
        return User.from_row(response.data[0])
    return find_by_id(user_id)
