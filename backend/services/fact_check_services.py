from models import db
from models.models import FactCheck, VerificationStatus, CheckedVia

CATEGORY_TO_STATUS = {
    "true":    VerificationStatus.TRUE,
    "false":   VerificationStatus.FALSE,
    "mixed":   VerificationStatus.PARTIALLY_TRUE,
}

def create_fact_check(
    claim_id: int,
    user_id: int,
    verdict: dict,
    confidence_score: float | None = None,
) -> FactCheck | None:
    """
    Creates a FactCheck row from a verdict dict returned by build_verdict().
    Returns None (gracefully) if verdict is None or category is unrated.

    confidence_score: if provided (from credibility_scorer), used directly.
                      Falls back to a simple review-count heuristic otherwise.
    """
    if not verdict:
        return None

    status = CATEGORY_TO_STATUS.get(verdict.get("category"))
    if status is None:
        return None  # unrated — skip without blocking

    if confidence_score is None:
        confidence_score = min(100.0, round(verdict.get("totalReviews", 1) * 25.0, 2))

    record = FactCheck(
        claimID=claim_id,
        userID=user_id,
        verdict=status,
        confidence_score=confidence_score,
        explanation=verdict.get("summary"),
        checked_via=CheckedVia.EXISTING_FACT,
    )
    db.session.add(record)
    db.session.commit()
    return record