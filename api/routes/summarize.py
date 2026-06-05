from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from api.core.rate_limit import limiter
from api.db import users as user_db
from api.dependencies import AuthUserId
from api.services.gemini import GeminiError, ValidationError, generate_summary
from api.services.quota import has_exhausted_free_quota, increment_usage

router = APIRouter(tags=["ai"])


class SummarizeEntry(BaseModel):
    Gratitude1: str
    Gratitude2: str
    Gratitude3: str
    UserPrompt: str
    UserResponse: str


class SummarizeRequest(BaseModel):
    Year: int
    Month: int
    Entries: list[SummarizeEntry] = Field(default_factory=list)


@router.post("/summarize")
@limiter.limit("5/minute")
@limiter.limit("30/day")
def summarize(request: Request, body: SummarizeRequest, user_id: int = AuthUserId):
    user = user_db.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "User not found"})

    if body.Month < 1 or body.Month > 12:
        raise HTTPException(status_code=400, detail={"message": "Invalid Month"})

    if not body.Entries:
        raise HTTPException(
            status_code=400,
            detail={"message": "No entries found for this month"}
        )

    if not user.is_plus and has_exhausted_free_quota(user.user_id, body.Year, body.Month):
        raise HTTPException(
            status_code=403,
            detail={"message": "Free plan includes 1 AI recap per month. Upgrade to Plus."}
        )

    try:
        entries_payload = [entry.model_dump() for entry in body.Entries]
        summary = generate_summary(entries_payload)
    except ValidationError as error:
        raise HTTPException(status_code=400, detail={"message": str(error)})
    except GeminiError:
        raise HTTPException(
            status_code=503,
            detail={"message": "Failed to contact AI service"}
        )

    if not user.is_plus:
        increment_usage(user.user_id, body.Year, body.Month)

    return {
        "summary": summary,
        "message": "Monthly summary generated"
    }
