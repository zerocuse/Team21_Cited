from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import spacy
from models import *
from flask_sqlalchemy import SQLAlchemy
from services.claim_comparator import compare_claims, invert_rating_category, invert_condensed_rating



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
    if not fact_checks:
        return None

    category_counts = {}
    total = 0

    for claim in fact_checks:
        for review in claim.get("claimReview", []):
            # Use already-enriched and inverted category if available
            category = review.get("ratingCategory")
            if not category:
                original = review.get("textualRating", "")
                condensed = condense_rating(original)
                category = classify_rating(condensed)
            category_counts[category] = category_counts.get(category, 0) + 1
            total += 1

    if total == 0:
        return None

    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    top_category = sorted_categories[0][0]

    source_word = "source" if total == 1 else "sources"
    summaries = {
        "true":    f"Rated 'true' by {total} {source_word}. Claim appears credible.",
        "false":   f"Rated 'false' by {total} {source_word}. Claim appears unfounded.",
        "mixed":   f"Rated 'mixed' by {total} {source_word}. Claim has mixed support.",
        "unrated": f"Rated 'unrated' by {total} {source_word}. Verdict unclear.",
    }

    return {
        "topRating":    top_category,
        "category":     top_category,
        "totalReviews": total,
        "breakdown":    category_counts,
        "summary":      summaries.get(top_category, summaries["unrated"]),
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


@app.route('/fact-check', methods=['POST'])
def handle_fact_check():
    query = request.form.get('query')
    if not query:
        return jsonify({"status": "error", "message": "No query"}), 400

    # Try to identify the logged-in user from the token
    from routes.auth import _decode_token
    from services.claim_service import create_claim

    auth_header = request.headers.get('Authorization', '')
    token = auth_header.removeprefix('Bearer ').strip()
    user_id = _decode_token(token) if token else None

    query = " ".join(query.split())
    doc = nlp(query)
    relevant_sentences = [sent.text.strip() for sent in doc.sents if is_relevant_claim(sent)]
    if not relevant_sentences:
        relevant_sentences = [sent.text for sent in list(doc.sents)[:1]]

    all_results = []

    for search_term in relevant_sentences[:4]:
        params = {
            "query": search_term,
            "key": GOOGLE_API_KEY,
            "languageCode": "en"
        }

        try:
            response = requests.get(GOOGLE_URL, params=params)
            data = response.json()
            google_claims = data.get('claims', [])
            print(f"DEBUG: search_term='{search_term}', API key present={bool(GOOGLE_API_KEY)}, status={response.status_code}, claims_count={len(google_claims)}")


            if google_claims:
                
                # ── Compare & filter/invert ratings ──
                for claim in google_claims[:]:  # iterate over a COPY
                    matched_text = claim.get("text", "")
                    if not matched_text:
                        continue

                    relationship = compare_claims(search_term, matched_text)

                    if relationship == "UNRELATED":
                        google_claims.remove(claim)
                    elif relationship == "OPPOSITE":
                        for review in claim.get("claimReview", []):
                            review["_inverted"] = True

                # Now enrich (condense + classify) as before
                enriched_claims = enrich_reviews(google_claims)

                # ── NEW: Apply inversion to enriched ratings ──
                for claim in enriched_claims:
                    for review in claim.get("claimReview", []):
                        if review.get("_inverted"):
                            review["condensedRating"] = invert_condensed_rating(
                                review["condensedRating"]
                            )
                            review["ratingCategory"] = invert_rating_category(
                                review["ratingCategory"]
                            )

                verdict = build_verdict(enriched_claims)
                all_results.append({
                    "original_claim": search_term,
                    "fact_checks": enriched_claims,
                    "verdict": verdict
                })
            else:
                all_results.append({
                    "original_claim": search_term,
                    "fact_checks": [],
                    "verdict": None
                })
        except Exception as e:
            print(f"Error checking sentence: {e}")
            all_results.append({
                "original_claim": search_term,
                "fact_checks": [],
                "verdict": None,
                "error": str(e)
            })

    # Save to DB if user is logged in
    from models.models import Source, Citation, ClaimSourceLink, SourceType
    if user_id:
        try:
            from services.fact_check_services import create_fact_check
            from services.ai_analyzer import analyze_claim

            claim = create_claim(query, user_id)

            has_google_verdict = any(r.get("verdict") for r in all_results)

            if has_google_verdict:
                for result in all_results:
                    if result.get("verdict"):
                        create_fact_check(claim.claimID, user_id, result["verdict"])
            else:
                ai_result = analyze_claim(query)
                if ai_result:
                    from models.models import FactCheck
                    record = FactCheck(
                        claimID=claim.claimID,
                        userID=user_id,
                        verdict=ai_result["verdict"],
                        confidence_score=ai_result["confidence_score"],
                        explanation=ai_result["explanation"],
                        checked_via=ai_result["checked_via"],
                    )
                    db.session.add(record)

            # Save sources from Google results
            print(f"DEBUG: Saving sources for {len(all_results)} results")
            for result in all_results:
                for fact_check_item in result.get("fact_checks", []):
                    for review in fact_check_item.get("claimReview", []):
                        publisher_name = review.get("publisher", {}).get("name", "Unknown")
                        review_url = review.get("url", "")
                        rating_text = review.get("textualRating", "")

                        if not review_url:
                            continue

                        # Reuse existing source if URL already exists
                        existing_source = Source.query.filter_by(url=review_url).first()
                        if existing_source:
                            source = existing_source
                        else:
                            source = Source(
                                url=review_url,
                                title=publisher_name,
                                source_type=SourceType.NEWS,
                            )
                            db.session.add(source)
                            db.session.flush()  # get sourceID before linking

                        # Link source to claim (skip if already linked)
                        existing_link = ClaimSourceLink.query.filter_by(
                            claimID=claim.claimID,
                            sourceID=source.sourceID
                        ).first()
                        if not existing_link:
                            link = ClaimSourceLink(
                                claimID=claim.claimID,
                                sourceID=source.sourceID
                            )
                            db.session.add(link)

                        # Create citation with the rating text
                        citation = Citation(
                            claimID=claim.claimID,
                            sourceID=source.sourceID,
                            info_used=rating_text
                        )
                        db.session.add(citation)

            db.session.commit()

        except Exception as e:
            print(f"Failed to save claim/fact_check: {e}")

    return jsonify({"status": "success", "results": all_results})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        #from services.seed_admins import seed_admins
        #seed_admins()
    app.run(debug=True, port=5001)

