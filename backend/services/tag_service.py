"""
TM21-149: Auto-tag claims using spaCy NER for duplicate detection.
Extracts named entities and key nouns, saves as Tags, and checks
for existing claims with matching tags before hitting the Google API.
"""

import spacy
from models import db
from models.models import Tag, ClaimTagLink, Claim, FactCheck

nlp = spacy.load("en_core_web_sm")

# Entity types we care about for fact-checking
RELEVANT_ENTITY_TYPES = {"PERSON", "ORG", "GPE", "EVENT", "NORP", "LOC", "DATE"}

# Map spaCy entity labels to tag categories
ENTITY_CATEGORY_MAP = {
    "PERSON": "person",
    "ORG":    "organization",
    "GPE":    "location",
    "LOC":    "location",
    "EVENT":  "event",
    "NORP":   "group",
    "DATE":   "date",
}


def extract_tags(claim_text: str) -> list[dict]:
    """
    Extract tags from claim text using spaCy NER + key nouns.

    Returns list of dicts: [{"name": "charlie kirk", "category": "person"}, ...]
    """
    doc = nlp(claim_text)
    tags = []
    seen = set()

    # Extract named entities
    for ent in doc.ents:
        if ent.label_ in RELEVANT_ENTITY_TYPES:
            name = ent.text.lower().strip()
            if name and name not in seen and len(name) > 1:
                seen.add(name)
                tags.append({
                    "name": name,
                    "category": ENTITY_CATEGORY_MAP.get(ent.label_, "topic"),
                })

    # Extract key nouns (subjects and objects) that aren't already entities
    for token in doc:
        if (token.dep_ in ("nsubj", "nsubjpass", "dobj", "pobj")
                and token.pos_ in ("NOUN", "PROPN")
                and token.text.lower() not in seen
                and not token.is_stop
                and len(token.text) > 2):
            name = token.lemma_.lower()
            if name not in seen:
                seen.add(name)
                tags.append({"name": name, "category": "topic"})

    return tags


def save_tags_for_claim(claim_id: int, claim_text: str) -> list[Tag]:
    """
    Extract tags from claim text and save to DB.
    Creates new Tags if they don't exist, links them via ClaimTagLink.
    Returns list of Tag objects.
    """
    tag_dicts = extract_tags(claim_text)
    saved_tags = []

    for t in tag_dicts:
        # Get or create the tag
        tag = Tag.query.filter_by(tagName=t["name"]).first()
        if not tag:
            tag = Tag(
                tagName=t["name"],
                tagCategory=t["category"],
                timesUsed=1,
            )
            db.session.add(tag)
            db.session.flush()
        else:
            tag.timesUsed += 1

        # Link tag to claim (skip if already linked)
        existing_link = ClaimTagLink.query.filter_by(
            claimID=claim_id, tagID=tag.tagID
        ).first()
        if not existing_link:
            link = ClaimTagLink(claimID=claim_id, tagID=tag.tagID)
            db.session.add(link)

        saved_tags.append(tag)

    db.session.commit()
    return saved_tags


def find_similar_claims(claim_text: str, threshold: float = 0.9) -> list[dict] | None:
    """
    Check if an existing claim shares enough tags to be a duplicate.

    Args:
        claim_text: The new claim to check
        threshold: Minimum tag overlap ratio (0-1) to consider a match

    Returns:
        List of fact-check result dicts from the best matching claim,
        or None if no similar claim found.
    """
    new_tags = extract_tags(claim_text)
    if not new_tags:
        return None

    new_tag_names = {t["name"] for t in new_tags}

    # Find all claims that share at least one tag
    matching_tags = Tag.query.filter(Tag.tagName.in_(new_tag_names)).all()
    if not matching_tags:
        return None

    matching_tag_ids = [t.tagID for t in matching_tags]

    # Get all claim IDs linked to these tags
    links = ClaimTagLink.query.filter(ClaimTagLink.tagID.in_(matching_tag_ids)).all()
    if not links:
        return None

    # Count how many tags each existing claim shares with the new one
    claim_tag_counts = {}
    for link in links:
        claim_tag_counts[link.claimID] = claim_tag_counts.get(link.claimID, 0) + 1

    # Find the best match
    best_claim_id = None
    best_overlap = 0

    for claim_id, shared_count in claim_tag_counts.items():
        # Get total tags for this existing claim
        total_existing = ClaimTagLink.query.filter_by(claimID=claim_id).count()
        # Overlap = shared tags / max(new tags, existing tags)
        overlap = shared_count / max(len(new_tag_names), total_existing)

        if overlap > best_overlap:
            best_overlap = overlap
            best_claim_id = claim_id

    if best_overlap < threshold or best_claim_id is None:
        return None

    # Found a match — return its fact check results
    claim = Claim.query.get(best_claim_id)
    if not claim:
        return None

    fact_checks = FactCheck.query.filter_by(claimID=best_claim_id).all()
    if not fact_checks:
        return None

    print(f"TAG CACHE HIT: '{claim_text}' matched claim #{best_claim_id} "
          f"('{claim.claim_text}') with {best_overlap:.0%} tag overlap")

    return {
        "cached_claim_id": best_claim_id,
        "cached_claim_text": claim.claim_text,
        "tag_overlap": round(best_overlap, 2),
        "fact_checks": [
            {
                "verdict": fc.verdict.value if fc.verdict else None,
                "confidence_score": fc.confidence_score,
                "explanation": fc.explanation,
                "checked_via": fc.checked_via.value if fc.checked_via else None,
            }
            for fc in fact_checks
        ],
    }