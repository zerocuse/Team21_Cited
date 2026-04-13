from models import db
from models.models import FactCheck, VerificationStatus, CheckedVia

CATEGORY_TO_STATUS = {
    "true":    VerificationStatus.TRUE,
    "false":   VerificationStatus.FALSE,
    "mixed":   VerificationStatus.PARTIALLY_TRUE,
}

<<<<<<< HEAD
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
=======
def create_fact_check(claim_id: int, user_id: int, verdict: dict) -> FactCheck | None:
    """
    Creates a FactCheck row from a verdict dict returned by build_verdict().
    Returns None (gracefully) if verdict is None or category is unrated.
>>>>>>> 5d53dfcd1b33041783090f1a2ec54fc222d96a0e
    """
    if not verdict:
        return None

    status = CATEGORY_TO_STATUS.get(verdict.get("category"))
    if status is None:
        return None  # unrated — skip without blocking

<<<<<<< HEAD
    if confidence_score is None:
        confidence_score = min(100.0, round(verdict.get("totalReviews", 1) * 25.0, 2))

=======
>>>>>>> 5d53dfcd1b33041783090f1a2ec54fc222d96a0e
    record = FactCheck(
        claimID=claim_id,
        userID=user_id,
        verdict=status,
<<<<<<< HEAD
        confidence_score=confidence_score,
=======
        confidence_score=round(
            (verdict.get("totalReviews", 1) / max(verdict.get("totalReviews", 1), 1)) * 100, 2
        ),
>>>>>>> 5d53dfcd1b33041783090f1a2ec54fc222d96a0e
        explanation=verdict.get("summary"),
        checked_via=CheckedVia.EXISTING_FACT,
    )
    db.session.add(record)
    db.session.commit()
    return record