from models import Claim, db

def create_claim(claim_text: str, user_id: int):
    existing = Claim.query.filter_by(claim_text=claim_text, userID=user_id).first()
    if existing:
        existing.view_count = (existing.view_count or 0) + 1
        db.session.commit()
        return existing
    
    if not claim_text or not claim_text.strip():
        raise ValueError("Claim text cannot be null or empty")
    
    new_claim = Claim(
        claim_text=claim_text,
        userID=user_id
    )
    
    db.session.add(new_claim)
    db.session.commit()
    return new_claim

def get_claim_by_id(claimID: int) -> Claim:
    claim = Claim.query.get(claimID)
    if not claim:
        raise ValueError(f"Claim with ID {claimID} does not exist")
    return claim


def delete_claim(claimID: int) -> None:
    claim = Claim.query.get(claimID)
    if not claim:
        raise ValueError(f"Claim with ID {claimID} does not exist")
    
    db.session.delete(claim)
    db.session.commit()

def increment_claim_views(claimID: int) -> None:
    claim = Claim.query.get(claimID)
    if not claim:
        raise ValueError(f"Claim with ID {claimID} does not exist")
    
    claim.views += 1
    db.session.commit()