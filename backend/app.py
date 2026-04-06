import os
import json
import requests
import spacy
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import anthropic
from difflib import SequenceMatcher

load_dotenv()
app = Flask(__name__)

CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# --- Config ---
GOOGLE_API_KEY = os.getenv("GOOGLE_FACT_CHECK")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

GOOGLE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

nlp = spacy.load("en_core_web_sm")


# ═══════════════════════════════════════════════
# HELPER: Calculate relevance between query and claim
# ═══════════════════════════════════════════════
def calculate_relevance(query, claim_text):
    """Returns 0.0-1.0 similarity score."""
    if not query or not claim_text:
        return 0.0
    return round(SequenceMatcher(None, query.lower(), claim_text.lower()).ratio(), 2)


# ═══════════════════════════════════════════════
# HELPER: Normalize ratings to frontend categories
# ═══════════════════════════════════════════════
def normalize_rating(textual_rating):
    """
    Frontend expects:
      - condensedRating: short display string
      - ratingCategory: "true" | "false" | "mixed" | "unrated"
    """
    rating_lower = (textual_rating or "").lower().strip()

    true_keywords = ["true", "correct", "accurate", "yes", "right", "verified"]
    false_keywords = ["false", "incorrect", "wrong", "no", "pants on fire",
                      "fake", "fabricated", "lie", "misleading", "4 pinocchios",
                      "not true", "inaccurate"]
    mixed_keywords = ["mixed", "half true", "half-true", "partly", "partially",
                      "mostly true", "mostly false", "cherry-pick", "context",
                      "exaggerated", "unproven", "disputed", "outdated"]

    if any(kw in rating_lower for kw in false_keywords):
        return {"condensedRating": "False", "ratingCategory": "false"}
    elif any(kw in rating_lower for kw in true_keywords):
        return {"condensedRating": "True", "ratingCategory": "true"}
    elif any(kw in rating_lower for kw in mixed_keywords):
        return {"condensedRating": "Mixed", "ratingCategory": "mixed"}
    else:
        return {"condensedRating": textual_rating or "Unrated", "ratingCategory": "unrated"}


# ═══════════════════════════════════════════════
# HELPER: Enrich Google Fact Check results
# ═══════════════════════════════════════════════
def enrich_fact_checks(claims, query):
    """
    Adds fields the frontend expects:
      - claim.relevance (float 0-1)
      - review.condensedRating (string)
      - review.ratingCategory ("true"/"false"/"mixed"/"unrated")
      - review.source (publisher URL for attribution)
    """
    enriched = []
    for claim in claims:
        claim_text = claim.get("text", "")
        claim["relevance"] = calculate_relevance(query, claim_text)

        reviews = claim.get("claimReview", [])
        for review in reviews:
            rating_info = normalize_rating(review.get("textualRating", ""))
            review["condensedRating"] = rating_info["condensedRating"]
            review["ratingCategory"] = rating_info["ratingCategory"]
            # ✅ Add source URL for attribution
            review["source"] = review.get("url", "")

        enriched.append(claim)

    # Sort by relevance (highest first)
    enriched.sort(key=lambda c: c.get("relevance", 0), reverse=True)
    return enriched


# ═══════════════════════════════════════════════
# HELPER: Fetch news articles (optional)
# ═══════════════════════════════════════════════
def fetch_news(query):
    """
    Returns the news object structure the frontend expects.
    Uses NewsAPI if available, otherwise returns empty structure.
    """
    empty_news = {
        "articles": [],
        "total_articles": 0,
        "support_count": 0,
        "contradict_count": 0,
        "neutral_count": 0,
        "ai_summary": None,
        "source_diversity": {
            "is_diverse": False,
            "unique_sources": 0
        },
        "bias_analysis": None
    }

    if not NEWS_API_KEY:
        return empty_news

    try:
        resp = requests.get("https://newsapi.org/v2/everything", params={
            "q": query,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 10,
            "apiKey": NEWS_API_KEY
        }, timeout=10)

        if resp.status_code != 200:
            return empty_news

        data = resp.json()
        raw_articles = data.get("articles", [])

        if not raw_articles:
            return empty_news

        articles = []
        sources_seen = set()
        for art in raw_articles:
            source_name = art.get("source", {}).get("name", "Unknown")
            sources_seen.add(source_name)
            articles.append({
                "url": art.get("url", ""),
                "imageUrl": art.get("urlToImage", ""),
                "stance": "neutral",
                "source": source_name,
                "publishedAt": art.get("publishedAt", ""),
                "title": art.get("title", ""),
                "description": art.get("description", "")
            })

        return {
            "articles": articles,
            "total_articles": len(articles),
            "support_count": 0,
            "contradict_count": 0,
            "neutral_count": len(articles),
            "ai_summary": None,
            "source_diversity": {
                "is_diverse": len(sources_seen) >= 3,
                "unique_sources": len(sources_seen)
            },
            "bias_analysis": {
                "bias_detected": "unclear",
                "direction": None,
                "note": "Automated bias detection not yet implemented."
            }
        }

    except Exception as e:
        print(f"News fetch error: {e}")
        return empty_news


# ═══════════════════════════════════════════════
# CLAUDE ANALYSIS (Primary) - WITH SOURCE CITATIONS
# ═══════════════════════════════════════════════
def get_claude_analysis(claim, fact_checks, news_data):
    """
    Claude fact-check analysis with explicit source citations.
    Returns frontend-aligned JSON with verdicts and sources.
    """

    # ✅ Build detailed fact-check context with sources
    fc_context = "## Professional Fact-Checks:\n"
    fact_check_sources = []
    
    for idx, fc in enumerate(fact_checks[:5], 1):
        claimed_text = fc.get("text", "")
        relevance = fc.get("relevance", 0)
        
        for review in fc.get("claimReview", []):
            publisher = review.get("publisher", {}).get("name", "Unknown Publisher")
            rating = review.get("textualRating", "Unrated")
            url = review.get("url", "")
            date = review.get("reviewDate", "")
            
            fc_context += (
                f"{idx}. **{publisher}**: {rating}\n"
                f"   - Claim: \"{claimed_text}\"\n"
                f"   - Relevance: {relevance}\n"
                f"   - Date: {date}\n"
                f"   - URL: {url}\n\n"
            )
            
            # ✅ Track sources for citation in response
            fact_check_sources.append({
                "publisher": publisher,
                "rating": rating,
                "url": url,
                "date": date,
                "claim_match": claimed_text
            })

    if not fact_check_sources:
        fc_context += "No prior fact-checks found.\n"

    # ✅ Build news context with sources
    news_context = "## News Coverage:\n"
    news_sources = []
    
    if news_data and news_data.get("articles"):
        for idx, art in enumerate(news_data["articles"][:5], 1):
            source_name = art.get("source", "Unknown")
            title = art.get("title", "")
            url = art.get("url", "")
            date = art.get("publishedAt", "")
            
            news_context += (
                f"{idx}. **{source_name}**: {title}\n"
                f"   - Date: {date}\n"
                f"   - URL: {url}\n\n"
            )
            
            # ✅ Track news sources
            news_sources.append({
                "source": source_name,
                "title": title,
                "url": url,
                "date": date
            })
    else:
        news_context += "No news articles found.\n"

    news_count = news_data.get("total_articles", 0) if news_data else 0

    # ✅ Enhanced prompt requesting detailed source analysis
    prompt = f"""You are a rigorous, evidence-based fact-checker. Analyze this claim and provide a detailed verdict with explicit source citations.

CLAIM TO ANALYZE: "{claim}"

{fc_context}

{news_context}

ANALYSIS REQUIREMENTS:
1. Provide a clear verdict (true, false, mostly true, mostly false, mixed, or unverified)
2. Rate your confidence (high, medium, low) based on source agreement
3. List specific sources that support or contradict the claim
4. Identify which sources agree/disagree and why
5. Flag any missing context or uncertainty

CRITICAL: Return ONLY valid JSON (no markdown, no explanations outside JSON):

{{
  "verdict": "true|false|mostly true|mostly false|mixed|unverified",
  "confidence": "high|medium|low",
  "source": "Claude AI (primary)",
  "summary": "One clear sentence verdict.",
  "detailed_reasoning": "Multi-sentence explanation grounded in sources.",
  "key_findings": ["Finding 1 with source", "Finding 2 with source"],
  "red_flags": ["Flag 1", "Flag 2"],
  "what_to_watch": "Future developments that could change this verdict.",
  "evidence_assessment": {{
    "source_agreement": "agree|disagree|partial|insufficient",
    "fact_checks_summary": "Which fact-checkers rated this true/false and why.",
    "news_coverage_summary": "How news sources are covering this claim.",
    "trending_context": "Whether this claim is currently trending/viral."
  }},
  "sources_cited": [
    {{
      "type": "fact-check",
      "publisher": "Publisher Name",
      "rating": "True/False/Mixed",
      "url": "https://example.com",
      "date": "2024-01-15",
      "stance": "supports|contradicts|neutral",
      "excerpt": "Brief quote or finding from source"
    }},
    {{
      "type": "news",
      "source": "News Source Name",
      "title": "Article Title",
      "url": "https://example.com",
      "date": "2024-01-15",
      "stance": "supports|contradicts|neutral",
      "excerpt": "Brief relevant quote from article"
    }}
  ],
  "totalFactChecks": {len(fact_checks)},
  "totalNewsArticles": {news_count}
}}"""

    try:
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system="""You are a rigorous, neutral fact-checker with expertise across multiple domains.
- Always respond with ONLY valid JSON — no markdown, no additional commentary.
- Use only the specified verdict and confidence values.
- Base all verdicts on evidence provided, not assumptions.
- Clearly distinguish established facts from uncertain claims.
- Always cite sources explicitly when making claims.
- When sources conflict, explain the disagreement clearly.""",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        raw = message.content[0].text.strip()
        
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        parsed = json.loads(raw)

        # ── Validate/sanitize values ──
        valid_verdicts = ["true", "false", "mostly true", "mostly false", "mixed", "unverified"]
        if parsed.get("verdict", "").lower() not in valid_verdicts:
            parsed["verdict"] = "unverified"
        else:
            parsed["verdict"] = parsed["verdict"].lower()

        valid_confidence = ["high", "medium", "low"]
        if parsed.get("confidence", "").lower() not in valid_confidence:
            parsed["confidence"] = "medium"
        else:
            parsed["confidence"] = parsed["confidence"].lower()

        parsed["source"] = "Claude AI (primary)"

        # Ensure nested structure exists
        if "evidence_assessment" not in parsed or not isinstance(parsed["evidence_assessment"], dict):
            parsed["evidence_assessment"] = {
                "source_agreement": "insufficient",
                "fact_checks_summary": "",
                "news_coverage_summary": "",
                "trending_context": ""
            }

        valid_agreements = ["agree", "disagree", "partial", "insufficient"]
        ea = parsed["evidence_assessment"]
        if ea.get("source_agreement", "").lower() not in valid_agreements:
            ea["source_agreement"] = "insufficient"
        else:
            ea["source_agreement"] = ea["source_agreement"].lower()

        # ✅ Validate sources_cited array
        if "sources_cited" not in parsed or not isinstance(parsed["sources_cited"], list):
            parsed["sources_cited"] = []
        
        # Ensure each source has required fields
        for src in parsed["sources_cited"]:
            src["type"] = src.get("type", "unknown")
            src["stance"] = src.get("stance", "neutral").lower()
            if src["stance"] not in ["supports", "contradicts", "neutral"]:
                src["stance"] = "neutral"

        # Ensure arrays
        if not isinstance(parsed.get("key_findings"), list):
            parsed["key_findings"] = []
        if not isinstance(parsed.get("red_flags"), list):
            parsed["red_flags"] = []

        # Ensure counts
        parsed["totalFactChecks"] = len(fact_checks)
        parsed["totalNewsArticles"] = news_count

        return parsed

    except json.JSONDecodeError as e:
        print(f"Claude JSON parse error: {e}")
        print(f"Raw response: {raw}")
        return None
    except anthropic.APIError as e:
        print(f"Claude API error: {e}")
        return None
    except Exception as e:
        print(f"Claude unexpected error: {e}")
        return None


# ═══════════════════════════════════════════════
# GEMINI ANALYSIS (Fallback)
# ═══════════════════════════════════════════════
def get_gemini_analysis(claim, fact_checks, news_data):
    """Gemini fallback, same output format as Claude."""

    fc_context = "## Fact-Checks:\n"
    for fc in fact_checks[:3]:
        for review in fc.get("claimReview", []):
            publisher = review.get("publisher", {}).get("name", "Source")
            rating = review.get("textualRating", "Unrated")
            url = review.get("url", "")
            fc_context += f"- {publisher}: {rating} ({url})\n"

    news_count = news_data.get("total_articles", 0) if news_data else 0

    prompt = f"""Analyze claim: "{claim}"

Evidence:
{fc_context if fc_context else "None"}

Return ONLY JSON (no markdown):
{{
  "verdict": "true|false|mostly true|mostly false|mixed|unverified",
  "confidence": "high|medium|low",
  "source": "Gemini AI (primary)",
  "summary": "1-sentence verdict.",
  "detailed_reasoning": "Full explanation.",
  "key_findings": ["Finding 1"],
  "red_flags": [],
  "what_to_watch": "Future context.",
  "evidence_assessment": {{
    "source_agreement": "agree|disagree|partial|insufficient",
    "fact_checks_summary": "Ratings summary.",
    "news_coverage_summary": "News summary.",
    "trending_context": "Viral status."
  }},
  "sources_cited": [],
  "totalFactChecks": {len(fact_checks)},
  "totalNewsArticles": {news_count}
}}"""
    
    try:
        response = gemini_model.generate_content(prompt)
        raw_json = response.text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw_json)
        parsed["source"] = "Gemini AI (primary)"
        parsed["totalFactChecks"] = len(fact_checks)
        parsed["totalNewsArticles"] = news_count
        if "sources_cited" not in parsed:
            parsed["sources_cited"] = []
        return parsed
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None


# ═══════════════════════════════════════════════
# HELPER: Build static fallback verdict
# ═══════════════════════════════════════════════
def fallback_verdict(fact_checks, news_data):
    """Last resort when both AI services fail."""
    news_count = news_data.get("total_articles", 0) if news_data else 0
    
    # Extract sources from available data
    sources_cited = []
    
    for fc in fact_checks[:3]:
        for review in fc.get("claimReview", []):
            sources_cited.append({
                "type": "fact-check",
                "publisher": review.get("publisher", {}).get("name", "Unknown"),
                "rating": review.get("textualRating", "Unrated"),
                "url": review.get("url", ""),
                "date": review.get("reviewDate", ""),
                "stance": "neutral",
                "excerpt": fc.get("text", "")[:100]
            })
    
    for art in news_data.get("articles", [])[:2]:
        sources_cited.append({
            "type": "news",
            "source": art.get("source", "Unknown"),
            "title": art.get("title", ""),
            "url": art.get("url", ""),
            "date": art.get("publishedAt", ""),
            "stance": "neutral",
            "excerpt": art.get("description", "")[:100]
        })
    
    return {
        "verdict": "unverified",
        "confidence": "low",
        "source": "System (fallback)",
        "summary": "AI analysis services are temporarily unavailable.",
        "detailed_reasoning": "Unable to reach Claude or Gemini for analysis. "
                              "Showing raw fact-check and news data only. "
                              "Review the sources below directly for verification.",
        "key_findings": [
            f"Found {len(fact_checks)} fact-check(s)",
            f"Found {news_count} news article(s)"
        ],
        "red_flags": ["AI analysis unavailable — review sources manually."],
        "what_to_watch": "Check the sources below for the latest information.",
        "evidence_assessment": {
            "source_agreement": "insufficient",
            "fact_checks_summary": f"{len(fact_checks)} fact-check(s) found from professional databases.",
            "news_coverage_summary": f"{news_count} news article(s) found covering this topic.",
            "trending_context": "Unable to assess without AI analysis."
        },
        "sources_cited": sources_cited,
        "totalFactChecks": len(fact_checks),
        "totalNewsArticles": news_count
    }


# ═══════════════════════════════════════════════
# HELPER: Fetch recent fact-check articles
# ═══════════════════════════════════════════════
def get_recent_articles():
    """
    Fetches recent fact-check articles for the landing page.
    Frontend expects: [{url, ratingCategory, condensedRating, date, 
                        claimant, claim, title, publisher}]
    """
    try:
        trending_queries = ["politics", "health", "economy", "climate", "technology"]
        articles = []
        seen_urls = set()

        for query in trending_queries:
            params = {
                "query": query,
                "key": GOOGLE_API_KEY,
                "languageCode": "en",
                "pageSize": 5
            }
            resp = requests.get(GOOGLE_URL, params=params, timeout=10)
            if resp.status_code != 200:
                continue

            claims = resp.json().get("claims", [])
            for claim in claims:
                for review in claim.get("claimReview", []):
                    url = review.get("url", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    rating_info = normalize_rating(review.get("textualRating", ""))
                    articles.append({
                        "url": url,
                        "ratingCategory": rating_info["ratingCategory"],
                        "condensedRating": rating_info["condensedRating"],
                        "date": review.get("reviewDate", ""),
                        "claimant": claim.get("claimant", ""),
                        "claim": claim.get("text", ""),
                        "title": review.get("title", claim.get("text", "")),
                        "publisher": review.get("publisher", {}).get("name", "")
                    })

            if len(articles) >= 12:
                break

        articles.sort(key=lambda a: a.get("date", ""), reverse=True)
        return articles[:12]

    except Exception as e:
        print(f"Recent articles error: {e}")
        return []


# ═══════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════

@app.route('/ai-status', methods=['GET'])
def ai_status():
    """Health check for AI backends."""
    status = {"claude": "unknown", "gemini": "unknown"}

    try:
        claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "ping"}]
        )
        status["claude"] = "online"
    except Exception:
        status["claude"] = "offline"

    try:
        gemini_model.generate_content("ping")
        status["gemini"] = "online"
    except Exception:
        status["gemini"] = "offline"

    return jsonify(status)


@app.route('/fact-check', methods=['GET'])
def get_recent_fact_checks():
    """
    GET /fact-check → returns recent articles for landing page.
    Frontend expects: { articles: [...] }
    """
    articles = get_recent_articles()
    return jsonify({"articles": articles})


@app.route('/fact-check', methods=['POST'])
def handle_fact_check():
    """
    POST /fact-check → full fact-check pipeline with verdicts and sources.
    Frontend expects: { status, results: [{ original_claim, verdict, 
                        fact_checks, news, sources_cited, trending_matches }] }
    """
    query = request.form.get('query')
    if not query:
        return jsonify({"status": "error", "message": "No query"}), 400

    doc = nlp(query)
    search_term = next(doc.sents).text if list(doc.sents) else query

    try:
        # ── Step 1: Google Fact Check API ──
        params = {
            "query": search_term,
            "key": GOOGLE_API_KEY,
            "languageCode": "en"
        }
        google_data = requests.get(GOOGLE_URL, params=params, timeout=10).json()
        raw_claims = google_data.get('claims', [])

        # ✅ Enrich with relevance + rating categories + sources
        fact_checks = enrich_fact_checks(raw_claims, search_term)

        # ── Step 2: Fetch news ──
        news_data = fetch_news(search_term)

        # ── Step 3: AI Analysis (Claude primary → Gemini fallback) ──
        verdict_obj = get_claude_analysis(search_term, fact_checks, news_data)

        if verdict_obj is None:
            print("⚠️ Claude failed, falling back to Gemini...")
            verdict_obj = get_gemini_analysis(search_term, fact_checks, news_data)

        if verdict_obj is None:
            print("⚠️ Both AI services failed, using static fallback")
            verdict_obj = fallback_verdict(fact_checks, news_data)

        # ── Step 4: Detect if current event ──
        is_current_event = (
            len(news_data.get("articles", [])) >= 3 or
            any(fc.get("relevance", 0) >= 0.5 for fc in fact_checks)
        )

        # ── Step 5: Build result matching frontend shape ──
        result_item = {
            "original_claim": search_term,
            "is_current_event": is_current_event,
            "verdict": verdict_obj,
            "fact_checks": fact_checks,
            "news": news_data,
            "sources_cited": verdict_obj.get("sources_cited", []),  # ✅ Explicit sources
            "trending_matches": []
        }

        return jsonify({"status": "success", "results": [result_item]})

    except Exception as e:
        print(f"Fact-check error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)