from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AssessmentRequest(BaseModel):
    scenario: str = Field(min_length=1, max_length=20000)
    session_id: str | None = Field(
        default=None,
        description="Browser/session identifier. If omitted, backend will still accept the request but frontend should supply one for history grouping.",
    )


class EthicalAssessmentResult(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    dimensions: dict[str, int]
    rationale: str
    ethical_flags: list[str]
    mitigation: list[str]
    model_used: str


class AssessmentCreateResponse(EthicalAssessmentResult):
    id: UUID
    created_at: datetime
    session_id: str


class AssessmentListItem(BaseModel):
    id: UUID
    scenario_text: str
    overall_score: int
    dimensions: dict[str, int]
    rationale: str
    ethical_flags: list[str]
    mitigation: list[str]
    model_used: str
    created_at: datetime


class AssessmentListResponse(BaseModel):
    items: list[AssessmentListItem]
    total: int


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database_connected: bool

