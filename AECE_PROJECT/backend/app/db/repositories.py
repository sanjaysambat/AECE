import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import EthicalAssessment


def create_assessment(
    db: Session,
    *,
    session_id: str,
    scenario_text: str,
    overall_score: int,
    dimensions: dict,
    rationale: str,
    ethical_flags: list[str],
    mitigation: list[str],
    model_used: str,
) -> EthicalAssessment:
    row = EthicalAssessment(
        session_id=session_id,
        scenario_text=scenario_text,
        overall_score=overall_score,
        dimensions=dimensions,
        rationale=rationale,
        ethical_flags=ethical_flags,
        mitigation=mitigation,
        model_used=model_used,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_assessments(
    db: Session,
    *,
    session_id: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[EthicalAssessment], int]:
    stmt = select(EthicalAssessment).where(EthicalAssessment.session_id == session_id).order_by(
        EthicalAssessment.created_at.desc()
    )
    items_stmt = stmt.limit(limit).offset(offset)
    items = list(db.execute(items_stmt).scalars().all())
    total = db.execute(select(EthicalAssessment).where(EthicalAssessment.session_id == session_id)).scalars().all()
    return items, len(total)

