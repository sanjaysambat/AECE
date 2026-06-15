import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from ai_engine.ethical_engine import evaluate_action
from ai_engine.scenario_generator import generate_scenario
from app.db_ops import compute_reject_rate, create_decision, create_feedback, list_decisions
from database.session import get_db as database_get_db
from shared.schemas import (
    EvaluateActionRequest,
    EvaluateActionResponse,
    FeedbackRequest,
    GenerateScenarioRequest,
    GenerateScenarioResponse,
    HistoryResponse,
    DecisionHistoryItem,
    SystemStatusResponse,
)


router = APIRouter(tags=["AECE"])


@router.post("/evaluate-action", response_model=EvaluateActionResponse)
async def evaluate_action_endpoint(
    request: Request,
    payload: EvaluateActionRequest,
    db: Session = Depends(database_get_db),
):
    # Continuous learning signal from stored feedback.
    reject_rate = compute_reject_rate(db)
    learning_context = {"reject_rate": reject_rate}

    result = evaluate_action(payload, learning_context=learning_context)

    decision_id_row = create_decision(
        db,
        scenario=payload.scenario,
        ethical_score=result.ethical_score,
        decision=result.decision,
        explanation=result.explanation,
        framework_scores=result.framework_scores.model_dump(),
        alternatives=result.alternatives,
    )

    # Ensure response includes DB id + timestamp from API engine (timestamp is already set).
    response = EvaluateActionResponse(
        ethical_score=result.ethical_score,
        decision=result.decision,
        explanation=result.explanation,
        alternatives=result.alternatives,
        framework_scores=result.framework_scores,
        weights_used=result.weights_used,
        governance_override_applied=result.governance_override_applied,
        timestamp=result.timestamp,
        decision_id=str(decision_id_row.id),
    )

    # Real-time dashboard broadcast.
    manager = request.app.state.ws_manager
    await manager.broadcast(
        {
            "type": "decision_update",
            "payload": response.model_dump(),
        }
    )
    return response


@router.post("/generate-scenario", response_model=GenerateScenarioResponse)
def generate_scenario_endpoint(payload: GenerateScenarioRequest):
    return generate_scenario(payload)


@router.get("/history", response_model=HistoryResponse)
def history_endpoint(
    q: str | None = Query(default=None, description="Search in scenario/explanation"),
    decision: str | None = Query(default=None, description="Filter by decision"),
    min_score: int | None = Query(default=None, ge=0, le=100, description="Minimum ethical score"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database_get_db),
):
    items, total = list_decisions(
        db,
        q=q,
        decision=decision,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )

    return HistoryResponse(
        items=[
            DecisionHistoryItem(
                id=str(it.id),
                scenario=it.scenario,
                ethical_score=it.ethical_score,
                decision=it.decision,
                explanation=it.explanation,
                timestamp=it.timestamp,
            )
            for it in items
        ],
        total=total,
    )


@router.post("/feedback")
async def feedback_endpoint(
    request: Request,
    payload: FeedbackRequest,
    db: Session = Depends(database_get_db),
):
    decision_uuid = uuid.UUID(payload.decision_id)
    row = create_feedback(db, decision_id=decision_uuid, user_feedback=payload.user_feedback)

    manager = request.app.state.ws_manager
    await manager.broadcast(
        {
            "type": "feedback_update",
            "payload": {
                "id": str(row.id),
                "decision_id": payload.decision_id,
                "user_feedback": payload.user_feedback,
            },
        }
    )
    return {"id": str(row.id), "decision_id": payload.decision_id, "user_feedback": payload.user_feedback}


@router.get("/system-status", response_model=SystemStatusResponse)
def system_status_endpoint(request: Request, db: Session = Depends(database_get_db)):
    # Verify DB is reachable.
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return SystemStatusResponse(
        status="ok",
        timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        database_connected=db_ok,
        websocket_clients_connected=request.app.state.ws_manager.connected_count(),
        scoring_mode="openai_or_heuristic",
    )

