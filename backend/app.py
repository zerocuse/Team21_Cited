from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import spacy
from models import *
from flask_sqlalchemy import SQLAlchemy



load_dotenv(override=True)
app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///factcheck.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')


db.init_app(app)

CORS(
    app,
    resources={r"/*": {"origins": [
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]}},
    supports_credentials=True
)

# Register auth blueprint
from routes.auth import auth_bp
app.register_blueprint(auth_bp)


app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
news_api_key = os.getenv("NEWS_API_KEY")
newsData_key = os.getenv("NEWS_DATA_API")
newsData_base_url = "https://newsdata.io/api/1/latest"
nlp = spacy.load("en_core_web_sm")


GOOGLE_API_KEY = os.getenv("GOOGLE_FACT_CHECK")
GOOGLE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store"
    return response

SHORTCUTS = {
    "pants on fire": "false",
    "four pinocchios": "false",
    "three pinocchios": "mostly false",
    "two pinocchios": "half true",
    "one pinocchio": "mostly true",
    "full flop": "false",
    "half flip": "mixed",
    "no flip": "true",
    "liar liar pants on fire": "false",
}

FALSE_WORDS = {
    "false", "wrong", "incorrect", "fake", "fiction",
    "fabricated", "unfounded", "debunked", "bogus", "hoax"
}
TRUE_WORDS = {
    "true", "correct", "accurate", "verified",
    "confirmed", "factual"
}
MIXED_WORDS = {
    "mixed", "half", "partly", "partially", "misleading",
    "exaggerated", "mixture", "unproven", "distorted", "outdated"
}

# strip filler words
STRIP_POS = {"DET", "ADP", "CCONJ", "SCONJ", "PUNCT", "PART", "INTJ", "SPACE"}


def condense_rating(rating_text):
    """Use spaCy to reduce a verbose fact-check rating to its core meaning."""
    if not rating_text:
        return "unrated"

    raw = rating_text.lower().strip()
    for key, val in SHORTCUTS.items():
        if key in raw:
            return val

    #Spacy
    doc = nlp(raw)

    # meaningful tokens
    meaningful = []
    for token in doc:
        if token.pos_ in STRIP_POS:
            continue
        if token.is_stop and token.pos_ not in ("ADJ", "ADV"):
            continue
        meaningful.append(token)

    adjectives = [t for t in meaningful if t.pos_ == "ADJ"]
    if adjectives:
        result_tokens = []
        for token in adjectives[:2]:
            if token.i > 0:
                prev = doc[token.i - 1]
                if prev.pos_ == "ADV" and prev.dep_ == "advmod":
                    result_tokens.append(prev.text)
            result_tokens.append(token.text)
        if result_tokens:
            return " ".join(result_tokens)

    nouns = [t.text for t in meaningful if t.pos_ == "NOUN"]
    if nouns:
        return nouns[0]

    verbs = [t.lemma_ for t in meaningful if t.pos_ == "VERB"]
    if verbs:
        return verbs[0]

    fallback = [t.text for t in meaningful[:2]]
    return " ".join(fallback) if fallback else raw


def classify_rating(condensed):
    words = set(condensed.lower().split())
    if words & FALSE_WORDS:
        return "false"
    if words & MIXED_WORDS:
        return "mixed"
    if words & TRUE_WORDS:
        return "true"

    c = condensed.lower()
    if any(w in c for w in FALSE_WORDS):
        return "false"
    if any(w in c for w in MIXED_WORDS):
        return "mixed"
    if any(w in c for w in TRUE_WORDS):
        return "true"

    return "unrated"


def build_verdict(fact_checks):
    """
    Build a credibility-weighted verdict from a list of Google Fact Check claims.

    Each review's vote is multiplied by its source's credibility weight so that
    a single authoritative source (government, established fact-checker) can
    outweigh a large number of low-quality sources.
    """
    if not fact_checks:
        return None

    from services.credibility_scorer import score_single_source, credibility_weight

    # count_map  : {condensed_rating: raw_count}   – used for UI breakdown display
    # weight_map : {condensed_rating: total_weight} – used for winner selection
    # cat_weight : {category: total_weight}         – used to pick winning category
    count_map: dict[str, int] = {}
    weight_map: dict[str, float] = {}
    cat_weight: dict[str, float] = {}
    total_reviews = 0

    for claim in fact_checks:
        for review in claim.get("claimReview", []):
            url       = review.get("url", "")
            publisher = review.get("publisher", {}).get("name", "")
            cred      = score_single_source(url, publisher)
            w         = credibility_weight(cred)

            original  = review.get("textualRating", "")
            condensed = condense_rating(original)
            category  = classify_rating(condensed)

            count_map[condensed]  = count_map.get(condensed, 0) + 1
            weight_map[condensed] = weight_map.get(condensed, 0.0) + w
            cat_weight[category]  = cat_weight.get(category, 0.0) + w
            total_reviews += 1

    if total_reviews == 0:
        return None

    # Winning category = highest credibility-weighted total
    best_category = max(cat_weight, key=lambda c: cat_weight[c])

    # Best condensed rating within the winning category (highest weight)
    cat_ratings = {r: weight_map[r] for r in weight_map if classify_rating(r) == best_category}
    top_rating  = max(cat_ratings, key=cat_ratings.get) if cat_ratings else best_category

    # Dominance: % of total credibility weight held by the winning category
    total_weight = sum(cat_weight.values())
    dominance = round((cat_weight[best_category] / total_weight) * 100, 1) if total_weight > 0 else 50.0

    source_word = "source" if total_reviews == 1 else "sources"
    summaries = {
        "true":    f"Rated '{top_rating}' by {total_reviews} {source_word} ({dominance:.0f}% credibility-weighted consensus). Claim appears credible.",
        "false":   f"Rated '{top_rating}' by {total_reviews} {source_word} ({dominance:.0f}% credibility-weighted consensus). Claim appears unfounded.",
        "mixed":   f"Rated '{top_rating}' by {total_reviews} {source_word} ({dominance:.0f}% credibility-weighted consensus). Claim has mixed support.",
        "unrated": f"Rated '{top_rating}' by {total_reviews} {source_word}. Verdict unclear.",
    }

    return {
        "topRating":    top_rating,
        "category":     best_category,
        "totalReviews": total_reviews,
        "breakdown":    count_map,   # raw counts for UI display
        "dominance":    dominance,   # credibility-weighted consensus % for confidence calc
        "summary":      summaries.get(best_category, summaries["unrated"]),
    }


def enrich_reviews(fact_checks):
    if not fact_checks:
        return fact_checks

    for claim in fact_checks:
        for review in claim.get("claimReview", []):
            original = review.get("textualRating", "")
            review["condensedRating"] = condense_rating(original)
            review["ratingCategory"] = classify_rating(review["condensedRating"])

    return fact_checks


def is_relevant_claim(sent):
    """Refined check for factual density."""
    # Must have a subject and a main verb
    has_subject = any(token.dep_ in ("nsubj", "nsubjpass") for token in sent)
    has_verb = any(token.pos_ == "VERB" for token in sent)

    # Exclude very short fragments and questions (which aren't usually 'claims')
    is_not_short = len(sent) > 4
    is_not_question = not sent.text.strip().endswith('?')

    # Look for Entities (Dates, People, Orgs) - these are high-value claims
    has_entities = len(sent.ents) > 0

    return (has_subject and has_verb and is_not_short and is_not_question) or has_entities


_GREETING_TOKENS = {
    "hello", "hi", "hey", "greetings", "howdy", "sup", "yo",
    "bye", "goodbye", "thanks", "thank", "ok", "okay",
}

_OPINION_STARTERS = {
    "i think", "i feel", "i believe", "i like", "i love",
    "i hate", "i want", "i prefer", "i wish", "i enjoy",
    "in my opinion", "personally", "i find", "i disagree",
}


def is_scorable_claim(query: str) -> tuple[bool, str]:
    """
    Use the loaded spaCy model to decide whether a query is a fact-checkable
    claim worth processing.

    Returns (True, "") if scorable, or (False, rejection_reason) otherwise.
    Errs on the side of acceptance — only rejects things that are clearly
    unverifiable (greetings, pure opinions, math, empty noise).
    """
    doc = nlp(query)
    tokens = [t for t in doc if not t.is_punct and not t.is_space and not t.is_quote]

    # ── 1. Minimum length ──────────────────────────────────────────────────
    if len(tokens) < 3:
        return False, "Too short to fact-check — please provide a complete claim."

    q = query.lower().strip()

    # ── 2. Pure greeting ──────────────────────────────────────────────────
    if len(tokens) <= 5 and tokens[0].lower_ in _GREETING_TOKENS:
        return False, "This looks like a greeting, not a verifiable claim."

    # ── 3. Named entities present (strong scorability signal) ─────────────
    has_entities = len(doc.ents) > 0

    # ── 4. Numeric / quantitative content ─────────────────────────────────
    QUANT_ENT_TYPES = {"CARDINAL", "PERCENT", "QUANTITY", "MONEY", "ORDINAL", "DATE", "TIME"}
    has_numbers = any(t.like_num or t.ent_type_ in QUANT_ENT_TYPES for t in doc)

    # ── 5. Comparative / superlative adjective or adverb ──────────────────
    has_comparative = any(t.tag_ in {"JJR", "JJS", "RBR", "RBS"} for t in doc)

    # ── 6. At least one sentence with subject + verb (assertion structure) ─
    has_assertion = any(is_relevant_claim(sent) for sent in doc.sents)

    # ── 7. Pure personal opinion with no factual anchor ───────────────────
    is_pure_opinion = any(q.startswith(op) for op in _OPINION_STARTERS)
    if is_pure_opinion and not has_entities and not has_numbers:
        return False, (
            "Personal opinions without factual assertions cannot be fact-checked. "
            "Try rephrasing as a specific claim (e.g. 'X causes Y' or 'X happened in Y')."
        )

    # ── 8. Pure arithmetic expression ─────────────────────────────────────
    MATH_OPS = {"+", "-", "*", "/", "=", "×", "÷", "plus", "minus", "times", "divided"}
    if all(t.like_num or t.lower_ in MATH_OPS for t in tokens):
        return False, "Mathematical expressions are not fact-checkable claims."

    # ── 9. Needs at least one factual signal ──────────────────────────────
    factual_signals = sum([has_entities, has_numbers, has_comparative, has_assertion])
    if factual_signals == 0:
        return False, (
            "This submission doesn't contain enough verifiable information to fact-check. "
            "Include specific people, places, dates, numbers, or factual assertions."
        )

    return True, ""


def _parse_verdict_from_text(text: str) -> str:
    """Parse a verdict category from free-form analysis text."""
    t = text.lower()
    has_false = any(w in t for w in ["false", "incorrect", "debunked", "no evidence", "not true", "unfounded"])
    has_true  = any(w in t for w in ["true", "correct", "accurate", "confirmed", "verified"])
    has_mixed = any(w in t for w in ["partially", "mixed", "some truth", "partly", "misleading"])

    if has_mixed:
        return "mixed"
    if has_false and not has_true:
        return "false"
    if has_true and not has_false:
        return "true"
    if has_false and has_true:
        return "mixed"
    return "unrated"


def _build_report_dict(claim: str, all_sources: list, verdict: dict | None,
                       gemini_analysis: str, tiered: dict) -> dict:
    """Build a structured report dictionary for the frontend."""
    from services.credibility_scorer import compute_confidence, score_single_source

    # Determine verdict category and summary
    category = "unrated"
    summary = "No conclusion could be reached."
    if verdict:
        category = verdict.get("category", "unrated")
        summary  = verdict.get("summary", "")
    elif gemini_analysis:
        category = _parse_verdict_from_text(gemini_analysis)
        summary  = gemini_analysis[:300]

    # Credibility score — use weighted verdict dominance when available,
    # otherwise fall back to average source credibility
    if tiered["raw_google_claims"] and verdict:
        score = compute_confidence(tiered["raw_google_claims"], verdict)
    elif verdict and verdict.get("dominance") is not None:
        # Verdict came from cached DB or gov docs; use dominance directly
        from services.credibility_scorer import compute_source_credibility
        src_cred = compute_source_credibility(tiered.get("raw_google_claims", []))
        score = round(min(100.0, src_cred * 0.65 + verdict["dominance"] * 0.35), 2)
    else:
        valid_urls = [s["url"] for s in all_sources if s.get("url")]
        if valid_urls:
            score = round(
                sum(score_single_source(u) for u in valid_urls) / len(valid_urls), 1
            )
        else:
            score = 40.0

    # Normalise sources
    normalised = []
    for src in all_sources:
        preview = src.get("preview", "") or "No preview available."
        normalised.append({
            "url":             src.get("url", ""),
            "title":           src.get("title", "Unknown Source"),
            "quote":           preview[:400],
            "relevance_score": src.get("relevance_score", 0.5),
            "tier":            src.get("tier", "web_search"),
            "tier_label":      src.get("tier_label", "Web Search"),
            "publisher":       src.get("publisher", ""),
            "rating":          src.get("rating", ""),
        })

    return {
        "claim":           claim,
        "verdict":         category,
        "credibility_score": score,
        "summary":         summary,
        "sources":         normalised,
        "source_count":    len(normalised),
        "sources_by_tier": tiered["sources_by_tier"],
        "tiers_searched":  tiered["tiers_searched"],
        "analysis_notes":  gemini_analysis[:500] if gemini_analysis else "",
    }


def _save_source_to_db(claim_id: int, url: str, title: str, info: str, source_type) -> None:
    """Upsert a source and link it to a claim; add a citation if info is provided."""
    from models.models import Source, Citation, ClaimSourceLink
    if not url:
        return
    try:
        existing = Source.query.filter_by(url=url).first()
        if existing:
            source = existing
        else:
            source = Source(url=url, title=title or "Unknown", source_type=source_type)
            db.session.add(source)
            db.session.flush()

        existing_link = ClaimSourceLink.query.filter_by(
            claimID=claim_id, sourceID=source.sourceID
        ).first()
        if not existing_link:
            db.session.add(ClaimSourceLink(claimID=claim_id, sourceID=source.sourceID))

        if info:
            db.session.add(Citation(
                claimID=claim_id, sourceID=source.sourceID,
                info_used=info[:500]
            ))
    except Exception as e:
        print(f"[DB] _save_source_to_db error: {e}")


@app.route('/fact-check', methods=['POST'])
def handle_fact_check():
    import json as _json
    query = request.form.get('query')
    if not query:
        return jsonify({"status": "error", "message": "No query"}), 400

    from routes.auth import _decode_token
    from services.claim_service import create_claim
    from services.tiered_search import run_tiered_search, ALL_METHODS

    auth_header = request.headers.get('Authorization', '')
    token = auth_header.removeprefix('Bearer ').strip()
    user_id = _decode_token(token) if token else None

    query = " ".join(query.split())

    # ── Parse selected fact-check methods ───────────────────────────────────
    try:
        raw_methods = request.form.get('fact_check_methods', '[]')
        selected_methods = _json.loads(raw_methods)
        if not isinstance(selected_methods, list) or not selected_methods:
            selected_methods = list(ALL_METHODS)
    except Exception:
        selected_methods = list(ALL_METHODS)

    # Only cache to the Cited database when all 3 methods are used
    cache_to_db = set(selected_methods) >= ALL_METHODS

    # ── Scorability gate — reject before any processing or DB write ────────
    scorable, rejection_reason = is_scorable_claim(query)
    if not scorable:
        return jsonify({"status": "unscoreable", "message": rejection_reason}), 422

    doc = nlp(query)
    relevant_sentences = [sent.text.strip() for sent in doc.sents if is_relevant_claim(sent)]
    if not relevant_sentences:
        relevant_sentences = [sent.text for sent in list(doc.sents)[:1]]

    all_results = []

    for search_term in relevant_sentences[:4]:
        try:
            # ── Tiered source discovery ──────────────────────────────────────
            tiered = run_tiered_search(search_term, methods=selected_methods)
            raw_google_claims = tiered["raw_google_claims"]
            all_sources       = tiered["all_sources"]
            gemini_analysis   = tiered.get("gemini_analysis", "")

            # ── Backward-compat verdict from Google (Tier 2) ────────────────
            enriched_claims = []
            verdict = None
            if raw_google_claims:
                enriched_claims = enrich_reviews(raw_google_claims)
                verdict = build_verdict(enriched_claims)

            # ── Build structured report ──────────────────────────────────────
            report = _build_report_dict(search_term, all_sources, verdict, gemini_analysis, tiered)

            all_results.append({
                "original_claim": search_term,
                "fact_checks":    enriched_claims,   # backward compat
                "verdict":        verdict,            # backward compat
                "report":         report,
            })

        except Exception as e:
            print(f"Error checking sentence: {e}")
            all_results.append({
                "original_claim": search_term,
                "fact_checks":    [],
                "verdict":        None,
                "report":         None,
                "error":          str(e),
            })

    # ── Persist to DB only when all methods used and verdict is conclusive ───
    from models.models import Source, Citation, ClaimSourceLink, SourceType
    if user_id and cache_to_db:
        try:
            from services.fact_check_services import create_fact_check
            from services.ai_analyzer import analyze_claim
            from services.credibility_scorer import compute_confidence

            has_google_verdict = any(r.get("verdict") for r in all_results)
            ai_result = None

            if not has_google_verdict:
                # Fallback to LLM when no structured verdict exists
                ai_result = analyze_claim(query)

            # Only persist when we have a conclusive verdict
            is_conclusive = has_google_verdict or (ai_result is not None)
            if not is_conclusive:
                # Inconclusive — skip DB write entirely
                return jsonify(all_results), 200

            claim_record = create_claim(query, user_id)

            if has_google_verdict:
                for result in all_results:
                    if result.get("verdict"):
                        score = compute_confidence(
                            result.get("fact_checks", []),
                            result["verdict"],
                        )
                        fc = create_fact_check(claim_record.claimID, user_id, result["verdict"], score)
                        if fc and claim_record.status is None:
                            claim_record.status = fc.verdict
                            db.session.commit()
            else:
                from models.models import FactCheck
                record = FactCheck(
                    claimID=claim_record.claimID,
                    userID=user_id,
                    verdict=ai_result["verdict"],
                    confidence_score=ai_result["confidence_score"],
                    explanation=ai_result["explanation"],
                    checked_via=ai_result["checked_via"],
                )
                db.session.add(record)
                claim_record.status = ai_result["verdict"]
                db.session.commit()

            # Save all sources (Tier 2 Google + Tier 3/4)
            TIER_TYPE_MAP = {
                "cached_db":         SourceType.OTHER,
                "expert_fact_check": SourceType.NEWS,
                "web_scrape":        SourceType.GOVERNMENT,
                "web_search":        SourceType.NEWS,
            }

            for result in all_results:
                # Tier 2 – Google claimReview sources
                for fc_item in result.get("fact_checks", []):
                    for review in fc_item.get("claimReview", []):
                        _save_source_to_db(
                            claim_record.claimID,
                            review.get("url", ""),
                            review.get("publisher", {}).get("name", "Unknown"),
                            review.get("textualRating", ""),
                            SourceType.NEWS,
                        )

                # Tier 1 / 3 / 4 sources from the report
                report = result.get("report") or {}
                for src in report.get("sources", []):
                    url = src.get("url", "")
                    if not url or url.startswith("cited://"):
                        continue
                    tier = src.get("tier", "web_search")
                    _save_source_to_db(
                        claim_record.claimID,
                        url,
                        src.get("title", "Unknown"),
                        src.get("quote", ""),
                        TIER_TYPE_MAP.get(tier, SourceType.OTHER),
                    )

            db.session.commit()

        except Exception as e:
            print(f"Failed to save claim/fact_check: {e}")

    return jsonify(all_results), 200


@app.cli.command("cleanup-inconclusive")
def cleanup_inconclusive():
    """Remove inconclusive (no-verdict) claim records from the database."""
    from models.models import Claim, FactCheck, Citation, ClaimSourceLink
    with app.app_context():
        _run_inconclusive_cleanup()


def _run_inconclusive_cleanup():
    """Delete all Claim records with status=None and their dependent rows."""
    from models.models import Claim, FactCheck, Citation, ClaimSourceLink
    try:
        inconclusive_ids = [
            r.claimID for r in Claim.query.filter_by(status=None).all()
        ]
        if not inconclusive_ids:
            print("[cleanup] No inconclusive records found.")
            return

        ClaimSourceLink.query.filter(
            ClaimSourceLink.claimID.in_(inconclusive_ids)
        ).delete(synchronize_session=False)

        Citation.query.filter(
            Citation.claimID.in_(inconclusive_ids)
        ).delete(synchronize_session=False)

        FactCheck.query.filter(
            FactCheck.claimID.in_(inconclusive_ids)
        ).delete(synchronize_session=False)

        deleted = Claim.query.filter(
            Claim.claimID.in_(inconclusive_ids)
        ).delete(synchronize_session=False)

        db.session.commit()
        print(f"[cleanup] Removed {deleted} inconclusive claim record(s).")
    except Exception as e:
        db.session.rollback()
        print(f"[cleanup] Error during inconclusive cleanup: {e}")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        _run_inconclusive_cleanup()
    app.run(debug=True, port=5001)
