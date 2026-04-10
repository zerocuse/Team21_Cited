"""
Hybrid claim comparator for TM21-148.
Determines whether a user's claim and a matched fact-check claim
are saying the SAME thing, the OPPOSITE, or are UNRELATED.

Layer 1 — Root verb match + negation check  (precise, fast)
Layer 2 — Subject matching + negation check  (catches everything else)

No LLM needed — runs entirely on spaCy.
"""

import spacy

nlp = spacy.load("en_core_web_sm")

NEGATION_WORDS = {
    "not", "never", "no", "neither", "nor", "n't", "cannot",
    "wasn't", "weren't", "isn't", "aren't", "didn't", "doesn't",
    "don't", "hasn't", "haven't", "hadn't", "won't", "wouldn't",
    "couldn't", "shouldn't",
}


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _has_negation(doc) -> bool:
    """Check whether a spaCy Doc contains negation."""
    for token in doc:
        if token.dep_ == "neg":
            return True
        if token.lower_ in NEGATION_WORDS:
            return True
    return False


def _extract_root_verb(doc):
    """Return the root verb token, or None."""
    for token in doc:
        if token.dep_ == "ROOT" and token.pos_ in ("VERB", "AUX"):
            return token
    return None


def _get_subject_words(doc) -> set:
    """
    Extract the grammatical subject's core words (head + compounds only).
    Does NOT follow the full subtree — avoids picking up names from
    prepositional phrases like "Assassination of Charlie Kirk".
    """
    for token in doc:
        if token.dep_ in ("nsubj", "nsubjpass"):
            words = set()
            words.add(token.text.lower())
            # Only direct compound children, not full subtree
            for child in token.children:
                if child.dep_ in ("compound", "flat", "flat:name"):
                    words.add(child.text.lower())
            return words
    return set()


# ═══════════════════════════════════════════════════════════════════════════
# Layer 1 — Root verb negation (when verbs match)
# ═══════════════════════════════════════════════════════════════════════════

def _verb_compare(user_doc, matched_doc) -> str:
    """
    Compare by root verb + negation.
    Only works when both share the same root verb lemma.
    """
    user_root = _extract_root_verb(user_doc)
    matched_root = _extract_root_verb(matched_doc)

    if user_root is None or matched_root is None:
        return "INCONCLUSIVE"

    if user_root.lemma_ != matched_root.lemma_:
        return "INCONCLUSIVE"

    user_negated = _has_negation(user_doc)
    matched_negated = _has_negation(matched_doc)

    if user_negated == matched_negated:
        return "SAME"
    return "OPPOSITE"


# ═══════════════════════════════════════════════════════════════════════════
# Layer 2 — Subject matching (handles different sentence structures)
# ═══════════════════════════════════════════════════════════════════════════

def _subject_compare(user_doc, matched_doc) -> str:
    """
    If the matched claim's grammatical subject is different from the user's,
    the claim is about something else → UNRELATED.

    e.g. User: "Charlie Kirk was killed"  (subject: Charlie Kirk)
         Match: "An image shows Renee Good..."  (subject: image)  → UNRELATED
         Match: "Mick Jagger posted about..."  (subject: Mick Jagger)  → UNRELATED
         Match: "Charlie Kirk isn't dead"  (subject: Charlie Kirk)  → check negation
    """
    user_subj = _get_subject_words(user_doc)
    matched_subj = _get_subject_words(matched_doc)

    # If we can't extract subjects from either, be conservative
    if not user_subj or not matched_subj:
        return "SAME"

    # Check if subjects share any words
    # e.g. {"charlie", "kirk"} & {"charlie", "kirk"} → match
    # e.g. {"charlie", "kirk"} & {"image"} → no match
    if not (user_subj & matched_subj):
        return "UNRELATED"

    # Same subject — check negation
    user_negated = _has_negation(user_doc)
    matched_negated = _has_negation(matched_doc)

    if user_negated != matched_negated:
        return "OPPOSITE"

    return "SAME"


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

def compare_claims(user_claim: str, matched_claim: str) -> str:
    """
    Determine the relationship between a user's claim and a fact-check match.

    1. If both claims share the same root verb → compare negation.
    2. Otherwise → compare grammatical subjects.
       - Different subject → UNRELATED
       - Same subject → check negation → SAME or OPPOSITE

    Returns: "SAME", "OPPOSITE", or "UNRELATED"
    """
    user_doc = nlp(user_claim)
    matched_doc = nlp(matched_claim)

    # Layer 1: root verb match
    result = _verb_compare(user_doc, matched_doc)
    if result != "INCONCLUSIVE":
        return result

    # Layer 2: subject matching
    return _subject_compare(user_doc, matched_doc)


# ═══════════════════════════════════════════════════════════════════════════
# Rating inversion
# ═══════════════════════════════════════════════════════════════════════════

_INVERSION_MAP = {
    "true":       "false",
    "false":      "true",
    "correct":    "incorrect",
    "incorrect":  "correct",
    "verified":   "debunked",
    "debunked":   "verified",
    "accurate":   "inaccurate",
    "inaccurate": "accurate",
}


def invert_rating_category(category: str) -> str:
    """Flip "true" <-> "false". Mixed/unrated stay the same."""
    if category == "true":
        return "false"
    elif category == "false":
        return "true"
    return category


def invert_condensed_rating(condensed: str) -> str:
    """Flip a condensed rating string if a mapping exists."""
    lower = condensed.lower()
    if lower in _INVERSION_MAP:
        return _INVERSION_MAP[lower]
    return condensed