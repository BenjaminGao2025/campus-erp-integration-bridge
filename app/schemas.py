from typing import Any, Literal

from pydantic import BaseModel, Field


class IntakeRequest(BaseModel):
    request_type: Literal["worker_change", "payroll_correction"]
    submitted_by: str
    submitted_by_email: str
    payload: dict[str, Any]
    free_text: str | None = None


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    decision_by: str
    comment: str | None = None


class AiSummaryRequest(BaseModel):
    request_type: str | None = None
    free_text: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
