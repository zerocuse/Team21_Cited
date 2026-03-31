from models import db
from models.models import FactCheck, VerificationStatus, CheckedVia

CATEGORY_TO_STATUS = {
    "true":    VerificationStatus.TRUE,
    "false":   VerificationStatus.FALSE,
    "mixed":   VerificationStatus.PARTIALLY_TRUE,
}

def create_fact_check(claim_id: int, user_id: int, verdict: dict) -> FactCheck | None:
    """
    Creates a FactCheck row from a verdict dict returned by build_verdict().
    Returns None (gracefully) if verdict is None or category is unrated.
    """
    if not verdict:
        return None

    status = CATEGORY_TO_STATUS.get(verdict.get("category"))
    if status is None:
        return None  # unrated — skip without blocking

    record = FactCheck(
        claimID=claim_id,
        userID=user_id,
        verdict=status,
        confidence_score=min(100.0, round(verdict.get("totalReviews", 1) * 25.0, 2)),
        explanation=verdict.get("summary"),
        checked_via=CheckedVia.EXISTING_FACT,
    )
    db.session.add(record)
    db.session.commit()
    return record