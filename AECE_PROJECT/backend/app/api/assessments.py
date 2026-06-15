from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.repositories import create_assessment, list_assessments
from app.db.session import get_db
from app.schemas import AssessmentCreateResponse, AssessmentListResponse, AssessmentRequest
from app.services.scoring_engine import assess_scenario


router = APIRouter(prefix="/api", tags=["assessments"])


@router.post("/assessments", response_model=AssessmentCreateResponse)
def create_assessment_endpoint(
    payload: AssessmentRequest,
    db: Session = Depends(get_db),
):
    session_id = payload.session_id or "anonymous"
    result = assess_scenario(payload.scenario)

    row = create_assessment(
        db,
        session_id=session_id,
        scenario_text=payload.scenario,
        overall_score=int(result["overall_score"]),
        dimensions=result["dimensions"],
        rationale=result["rationale"],
        ethical_flags=result["ethical_flags"],
        mitigation=result["mitigation"],
        model_used=str(result.get("model_used", "heuristic")),
    )

    return AssessmentCreateResponse(
        id=row.id,
        created_at=row.created_at,
        session_id=row.session_id,
        overall_score=row.overall_score,
        dimensions=row.dimensions,
        rationale=row.rationale,
        ethical_flags=row.ethical_flags,
        mitigation=row.mitigation,
        model_used=row.model_used,
    )


@router.get("/assessments", response_model=AssessmentListResponse)
def list_assessments_endpoint(
    session_id: str = Query(..., min_length=1, max_length=128),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = list_assessments(db, session_id=session_id, limit=limit, offset=offset)

    return AssessmentListResponse(
        items=[
            {
                "id": item.id,
                "scenario_text": item.scenario_text,
                "overall_score": item.overall_score,
                "dimensions": item.dimensions,
                "rationale": item.rationale,
                "ethical_flags": item.ethical_flags,
                "mitigation": item.mitigation,
                "model_used": item.model_used,
                "created_at": item.created_at,
            }
            for item in items
        ],
        total=total,
    )

