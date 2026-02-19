from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import spacy



load_dotenv()
app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
news_api_key = os.getenv("NEWS_API_KEY")
newsData_key = os.getenv("NEWS_DATA_API")
newsData_base_url = "https://newsdata.io/api/1/latest"
nlp = spacy.load("en_core_web_sm")


GOOGLE_API_KEY = os.getenv("GOOGLE_FACT_CHECK")
GOOGLE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


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

# ─── strip (filler words) ───
STRIP_POS = {"DET", "ADP", "CCONJ", "SCONJ", "PUNCT", "PART", "INTJ", "SPACE"}


def condense_rating(rating_text):
    """Use spaCy to reduce a verbose fact-check rating to its core meaning."""
    if not rating_text:
        return "unrated"

    raw = rating_text.lower().strip()

    # Check shortcut map first
    for key, val in SHORTCUTS.items():
        if key in raw:
            return val

    #Spacy
    doc = nlp(raw)

    # Extract meaningful tokens
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
    """Classify a condensed rating into a traffic-light category."""
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
    """Build an overall verdict summary from all fact-checks for one claim."""
    if not fact_checks:
        return None
#Ratings
    condensed_map = {}  
    total = 0

    for claim in fact_checks:
        for review in claim.get("claimReview", []):
            original = review.get("textualRating", "")
            condensed = condense_rating(original)
            condensed_map[condensed] = condensed_map.get(condensed, 0) + 1
            total += 1

    if total == 0:
        return None

    # Most frequent rating wins
    sorted_ratings = sorted(condensed_map.items(), key=lambda x: x[1], reverse=True)
    top_rating = sorted_ratings[0][0]
    category = classify_rating(top_rating)

    #Summary 
    source_word = "source" if total == 1 else "sources"
    summaries = {
        "true": f"Rated '{top_rating}' by {total} {source_word}. Claim appears credible.",
        "false": f"Rated '{top_rating}' by {total} {source_word}. Claim appears unfounded.",
        "mixed": f"Rated '{top_rating}' by {total} {source_word}. Claim has mixed support.",
        "unrated": f"Rated '{top_rating}' by {total} {source_word}. Verdict unclear.",
    }

    return {
        "topRating": top_rating,
        "category": category,
        "totalReviews": total,
        "breakdown": condensed_map,
        "summary": summaries.get(category, summaries["unrated"]),
    }


def enrich_reviews(fact_checks):
    """Add condensedRating and ratingCategory to each claimReview."""
    if not fact_checks:
        return fact_checks

    for claim in fact_checks:
        for review in claim.get("claimReview", []):
            original = review.get("textualRating", "")
            review["condensedRating"] = condense_rating(original)
            review["ratingCategory"] = classify_rating(review["condensedRating"])

    return fact_checks


def is_relevant_claim(sent):
    has_subject = any(token.dep_ in ("nsubj", "nsubjpass") for token in sent)
    has_verb = any(token.pos_ == "VERB" for token in sent)
    return has_subject and has_verb and len(sent) > 3


@app.route('/fact-check', methods=['POST'])
def handle_fact_check():
    query = request.form.get('query')
    if not query:
        return jsonify({"status": "error", "message": "No query"}), 400

    doc = nlp(query)
    relevant_sentences = [sent.text for sent in doc.sents if is_relevant_claim(sent)]
    sentences_to_check = relevant_sentences if relevant_sentences else [query]

    all_results = []

    for search_term in sentences_to_check[:3]:
        params = {
            "query": search_term,
            "key": GOOGLE_API_KEY,
            "languageCode": "en"
        }

        try:
            response = requests.get(GOOGLE_URL, params=params)
            data = response.json()
            google_claims = data.get('claims', [])

            if google_claims:
                enriched_claims = enrich_reviews(google_claims)

                #Verdict
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

    return jsonify({"status": "success", "results": all_results})


if __name__ == "__main__":
    app.run(debug=True)