"""
Hybrid claim comparator for TM21-148.
Layer 1 — Root verb match + negation check
Layer 2 — Subject matching + negation check
Layer 3 — Groq LLM fallback
"""

import os
import spacy
from groq import Groq

nlp = spacy.load("en_core_web_sm")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

NEGATION_WORDS = {
    "not", "never", "no", "neither", "nor", "n't", "cannot",
    "wasn't", "weren't", "isn't", "aren't", "didn't", "doesn't",
    "don't", "hasn't", "haven't", "hadn't", "won't", "wouldn't",
    "couldn't", "shouldn't",
}


def _has_negation(doc) -> bool:
    for token in doc:
        if token.dep_ == "neg":
            return True
        if token.lower_ in NEGATION_WORDS:
            return True
    return False


def _extract_root_verb(doc):
    for token in doc:
        if token.dep_ == "ROOT" and token.pos_ in ("VERB", "AUX"):
            return token
    return None


def _get_subject_words(doc) -> set:
    for token in doc:
        if token.dep_ in ("nsubj", "nsubjpass"):
            words = set()
            words.add(token.text.lower())
            for child in token.children:
                if child.dep_ in ("compound", "flat", "flat:name"):
                    words.add(child.text.lower())
            return words
    return set()


def _verb_compare(user_doc, matched_doc) -> str:
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


def _subject_compare(user_doc, matched_doc) -> str:
    user_subj = _get_subject_words(user_doc)
    matched_subj = _get_subject_words(matched_doc)

    if not user_subj or not matched_subj:
        return "INCONCLUSIVE"

    # Different subjects → definitely unrelated
    if not (user_subj & matched_subj):
        return "UNRELATED"

    # Same subject with clear negation mismatch → opposite
    user_negated = _has_negation(user_doc)
    matched_negated = _has_negation(matched_doc)

    if user_negated != matched_negated:
        return "OPPOSITE"

    # Same subject, no negation difference — let LLM verify
    # because antonyms (alive/dead, true/false) aren't caught by negation
    return "INCONCLUSIVE"


def _llm_compare(user_claim: str, matched_claim: str) -> str:
    prompt = f"""You are a fact-check assistant. Compare these two claims and determine their relationship.

Claim A (user submitted): "{user_claim}"
Claim B (from fact-check database): "{matched_claim}"

Do these two claims make the same assertion, opposite assertions, or are they about unrelated topics?

Respond with ONLY one word: SAME, OPPOSITE, or UNRELATED"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
        )
        result = response.choices[0].message.content.strip().upper()

        if result in ("SAME", "OPPOSITE", "UNRELATED"):
            return result
        return "SAME"

    except Exception as e:
        print(f"[claim_comparator] Groq error: {e}")
        return "SAME"


def compare_claims(user_claim: str, matched_claim: str) -> str:
    user_doc = nlp(user_claim)
    matched_doc = nlp(matched_claim)

    result = _verb_compare(user_doc, matched_doc)
    if result != "INCONCLUSIVE":
        return result

    result = _subject_compare(user_doc, matched_doc)
    if result != "INCONCLUSIVE":
        return result

    return _llm_compare(user_claim, matched_claim)


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
    if category == "true":
        return "false"
    elif category == "false":
        return "true"
    return category


def invert_condensed_rating(condensed: str) -> str:
    lower = condensed.lower()
    if lower in _INVERSION_MAP:
        return _INVERSION_MAP[lower]
    return condensed