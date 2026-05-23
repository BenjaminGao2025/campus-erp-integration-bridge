from fastapi import APIRouter

from app.schemas import AiSummaryRequest
from app.services.ai_assist_service import summarize_request

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/request-summary")
def request_summary(body: AiSummaryRequest):
    return summarize_request(body.request_type, body.free_text, body.payload)
