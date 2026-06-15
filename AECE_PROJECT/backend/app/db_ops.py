import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from database.models import Decision, Feedback


def ensure_tables_created() -> None:
    from database.session import engine
    from database.models import Base

    Base.metadata.create_all(bind=engine)


def create_decision(
    db: Session,
    *,
    scenario: str,
    ethical_score: int,
    decision: str,
    explanation: str,
    framework_scores: dict[str, Any] | None = None,
    alternatives: list[str] | None = None,
) -> Decision:
    row = Decision(
        scenario=scenario,
        ethical_score=int(ethical_score),
        decision=str(decision),
        explanation=explanation,
        framework_scores=framework_scores,
        alternatives=alternatives,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_decisions(
    db: Session,
    *,
    q: str | None = None,
    decision: str | None = None,
    min_score: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Decision], int]:
    stmt = select(Decision)

    if q:
        like = f"%{q}%"
        stmt = stmt.where(Decision.scenario.ilike(like) | Decision.explanation.ilike(like))

    if decision:
        stmt = stmt.where(Decision.decision == decision)

    if min_score is not None:
        stmt = stmt.where(Decision.ethical_score >= int(min_score))

    stmt = stmt.order_by(Decision.timestamp.desc()).limit(limit).offset(offset)
    items = list(db.execute(stmt).scalars().all())

    count_stmt = select(func.count()).select_from(Decision)
    if q:
        like = f"%{q}%"
        count_stmt = count_stmt.where(Decision.scenario.ilike(like) | Decision.explanation.ilike(like))
    if decision:
        count_stmt = count_stmt.where(Decision.decision == decision)
    if min_score is not None:
        count_stmt = count_stmt.where(Decision.ethical_score >= int(min_score))

    total = int(db.execute(count_stmt).scalar_one() or 0)
    return items, total


def create_feedback(db: Session, *, decision_id: uuid.UUID, user_feedback: str) -> Feedback:
    row = Feedback(decision_id=decision_id, user_feedback=str(user_feedback))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def compute_reject_rate(db: Session, *, lookback_feedback: int = 50) -> float:
    stmt = (
        select(Feedback.user_feedback)
        .order_by(Feedback.timestamp.desc())
        .limit(lookback_feedback)
    )
    rows: Sequence[str] = list(db.execute(stmt).scalars().all())
    if not rows:
        return 0.0
    rejects = sum(1 for r in rows if str(r).lower() == "reject")
    return rejects / max(1, len(rows))
