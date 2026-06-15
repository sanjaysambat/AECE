from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


DecisionType = Literal["Approved", "Conditional", "Flagged", "Blocked"]


class Weights(BaseModel):
    w1: float = Field(0.22, ge=0, le=1, description="Utilitarian weight")
    w2: float = Field(0.22, ge=0, le=1, description="Deontological weight")
    w3: float = Field(0.18, ge=0, le=1, description="Virtue weight")
    w4: float = Field(0.18, ge=0, le=1, description="Care ethics weight")
    w5: float = Field(0.20, ge=0, le=1, description="Context weight")


class EvaluateActionRequest(BaseModel):
    scenario: str = Field(min_length=1, max_length=20000)
    # Stakeholder-controlled weights.
    weights: Weights | None = None

    # Governance override (optional).
    governance_override: DecisionType | None = None
    policy_settings: dict[str, Any] | None = None


class FrameworkScores(BaseModel):
    utilitarian: float
    deontological: float
    virtue: float
    care: float
    context: float


class EvaluateActionResponse(BaseModel):
    ethical_score: int = Field(ge=0, le=100)
    decision: DecisionType
    explanation: str
    alternatives: list[str]
    framework_scores: FrameworkScores
    weights_used: Weights
    governance_override_applied: bool = False
    timestamp: datetime
    decision_id: str


class GenerateScenarioRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    style: str | None = Field(
        default="robot autonomy",
        description="How scenarios should be framed (e.g., robot autonomy, healthcare robot, etc.)",
    )


class GenerateScenarioResponse(BaseModel):
    scenario: str
    # Optional metadata for the frontend.
    recommended_weights: Weights | None = None


class FeedbackRequest(BaseModel):
    decision_id: str
    user_feedback: Literal["approve", "reject"] = Field(...)


class DecisionHistoryItem(BaseModel):
    id: str
    scenario: str
    ethical_score: int
    decision: DecisionType
    explanation: str
    timestamp: datetime


class HistoryResponse(BaseModel):
    items: list[DecisionHistoryItem]
    total: int


class SystemStatusResponse(BaseModel):
    status: Literal["ok"]
    timestamp: datetime
    database_connected: bool
    websocket_clients_connected: int
    scoring_mode: str

