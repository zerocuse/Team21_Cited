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
from datetime import datetime, timedelta
import re

load_dotenv()
app = Flask(__name__)

CORS(app, supports_credentials=True, cors_allowed_origins="*")

# --- Config ---
GOOGLE_API_KEY = os.getenv("GOOGLE_FACT_CHECK")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API = os.getenv("CLAUDE_API")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

claude_client = anthropic.Anthropic(api_key=CLAUDE_API)

GOOGLE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

nlp = spacy.load("en_core_web_sm")


# ═══════════════════════════════════════════════
# HELPER: Improve search query for better results
# ═══════════════════════════════════════════════
def generate_search_variations(query):
    """Generate multiple search query variations to improve fact-check coverage."""
    variations = [query]
    
    # Remove question marks and common filler words
    clean_query = query.replace("?", "").strip()
    variations.append(clean_query)
    
    # Add "did", "is", "was" variants
    if not any(word in query.lower() for word in ["did", "is", "was", "are"]):
        variations.append(f"is {clean_query}")
        variations.append(f"did {clean_query}")
    
    # Add common event keywords
    if any(word in query.lower() for word in ["bomb", "attack", "strike", "kill"]):
        variations.append(query.replace("?", "").strip())
    
    return variations[:3]  # Return top 3 variations


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
    rating_lower = (textual_rating or "").lower().strip()

    true_keywords = ["true", "correct", "accurate", "yes", "right", "verified", "confirmed"]
    false_keywords = ["false", "incorrect", "wrong", "no", "pants on fire",
                      "fake", "fabricated", "lie", "misleading", "4 pinocchios",
                      "not true", "inaccurate", "debunked"]
    mixed_keywords = ["mixed", "half true", "half-true", "partly", "partially",
                      "mostly true", "mostly false", "cherry-pick", "context",
                      "exaggerated", "unproven", "disputed", "outdated", "nuanced"]

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
    enriched = []
    for claim in claims:
        claim_text = claim.get("text", "")
        claim["relevance"] = calculate_relevance(query, claim_text)

        reviews = claim.get("claimReview", [])
        for review in reviews:
            rating_info = normalize_rating(review.get("textualRating", ""))
            review["condensedRating"] = rating_info["condensedRating"]
            review["ratingCategory"] = rating_info["ratingCategory"]
            review["source"] = review.get("url", "")

        enriched.append(claim)

    enriched.sort(key=lambda c: c.get("relevance", 0), reverse=True)
    return enriched


# ═══════════════════════════════════════════════
# HELPER: Fetch news articles
# ═══════════════════════════════════════════════
def fetch_news(query):
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
# HELPER: Use Gemini for real-time analysis when fact-checks are limited
# ═══════════════════════════════════════════════
def get_gemini_realtime_analysis(claim, news_articles):
    """Use Gemini to analyze claim based on recent news coverage."""
    
    news_context = ""
    if news_articles:
        news_context = "Recent News Coverage:\n"
        for art in news_articles[:5]:
            news_context += f"- {art['source']}: {art['title']}\n"
            if art.get('description'):
                news_context += f"  {art['description']}\n"
    
    prompt = f"""Analyze this claim based on current news and public information: "{claim}"

{news_context}

Based on recent news, public records, and reliable sources, determine:
1. Is this claim TRUE, FALSE, MOSTLY TRUE, MOSTLY FALSE, or MIXED?
2. How confident are you? (HIGH, MEDIUM, LOW)
3. What evidence supports or contradicts this claim?
4. Are there recent developments that affect this verdict?

Return ONLY valid JSON:
{{
  "verdict": "true|false|mostly true|mostly false|mixed",
  "confidence": "high|medium|low",
  "summary": "One sentence summary of verdict.",
  "detailed_reasoning": "Explanation based on current events and reliable sources.",
  "key_findings": ["Finding 1", "Finding 2"],
  "red_flags": [],
  "what_to_watch": "What developments to monitor.",
  "evidence_assessment": {{
    "source_agreement": "agree|disagree|partial|insufficient",
    "fact_checks_summary": "Summary of available evidence.",
    "news_coverage_summary": "What news sources are reporting.",
    "trending_context": "Is this trending or recent?"
  }},
  "sources_cited": [
    {{
      "type": "news",
      "source": "Source Name",
      "title": "Article Title",
      "url": "https://example.com",
      "date": "2024-01-15",
      "stance": "supports|contradicts|neutral",
      "excerpt": "Relevant quote or fact"
    }}
  ]
}}"""

    try:
        response = gemini_model.generate_content(prompt)
        raw_json = response.text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw_json)
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            parsed["source"] = "Gemini AI (Real-time Analysis)"
        return parsed
    except Exception as e:
        print(f"Gemini Real-time Analysis Error: {e}")
        return None


# ═══════════════════════════════════════════════
# CLAUDE ANALYSIS (Primary)
# ═══════════════════════════════════════════════
def get_claude_analysis(claim, fact_checks, news_data):
    """Claude fact-check analysis with explicit source citations."""

    # Build detailed fact-check context with sources
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
            
            fact_check_sources.append({
                "publisher": publisher,
                "rating": rating,
                "url": url,
                "date": date,
                "claim_match": claimed_text
            })

    if not fact_check_sources:
        fc_context += "No prior fact-checks found.\n"

    # Build news context with sources
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
            
            news_sources.append({
                "source": source_name,
                "title": title,
                "url": url,
                "date": date
            })
    else:
        news_context += "No news articles found.\n"

    news_count = news_data.get("total_articles", 0) if news_data else 0

    prompt = f"""You are a rigorous, evidence-based fact-checker. Analyze this claim and provide a detailed verdict.

CLAIM TO ANALYZE: "{claim}"

{fc_context}

{news_context}

ANALYSIS REQUIREMENTS:
1. Provide a clear verdict (true, false, mostly true, mostly false, mixed, or unverified)
2. Only use "unverified" if absolutely no evidence is available
3. For recent events, use news coverage to inform the verdict
4. Rate your confidence (high, medium, low) based on source agreement
5. List specific sources that support or contradict the claim

CRITICAL: Return ONLY valid JSON (no markdown):

{{
  "verdict": "true|false|mostly true|mostly false|mixed|unverified",
  "confidence": "high|medium|low",
  "summary": "One clear sentence verdict.",
  "detailed_reasoning": "Multi-sentence explanation grounded in sources.",
  "key_findings": ["Finding 1", "Finding 2"],
  "red_flags": [],
  "what_to_watch": "Future developments that could change this verdict.",
  "evidence_assessment": {{
    "source_agreement": "agree|disagree|partial|insufficient",
    "fact_checks_summary": "Summary of professional fact-checkers.",
    "news_coverage_summary": "Summary of news coverage.",
    "trending_context": "Is this claim currently trending?"
  }},
  "sources_cited": [
    {{
      "type": "fact-check|news",
      "publisher": "Name",
      "rating": "True|False|Mixed",
      "url": "https://...",
      "date": "2024-01-15",
      "stance": "supports|contradicts|neutral",
      "excerpt": "Brief quote"
    }}
  ]
}}"""

    try:
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system="""You are a rigorous, neutral fact-checker.
- Only respond with valid JSON — no markdown, no additional commentary.
- For recent events or news-worthy claims, use available news coverage.
- Base verdicts on evidence, not uncertainty.
- Only use "unverified" when there is genuinely no evidence whatsoever.
- When news coverage exists, use it to inform your verdict.""",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        raw = message.content[0].text.strip()
        
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        parsed = json.loads(raw)

        # Validate/sanitize values
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

        if "sources_cited" not in parsed or not isinstance(parsed["sources_cited"], list):
            parsed["sources_cited"] = []
        
        for src in parsed["sources_cited"]:
            src["type"] = src.get("type", "unknown")
            src["stance"] = src.get("stance", "neutral").lower()
            if src["stance"] not in ["supports", "contradicts", "neutral"]:
                src["stance"] = "neutral"

        if not isinstance(parsed.get("key_findings"), list):
            parsed["key_findings"] = []
        if not isinstance(parsed.get("red_flags"), list):
            parsed["red_flags"] = []

        return parsed

    except json.JSONDecodeError as e:
        print(f"Claude JSON parse error: {e}")
        print(f"Raw response: {raw}")
        return None
    except Exception as e:
        print(f"Claude unexpected error: {e}")
        return None


# ═══════════════════════════════════════════════
# HELPER: Build static fallback verdict
# ═══════════════════════════════════════════════
def fallback_verdict(fact_checks, news_data, original_claim):
    """Last resort when both AI services fail - use available data intelligently."""
    news_count = news_data.get("total_articles", 0) if news_data else 0
    
    sources_cited = []
    has_contradicting_sources = False
    has_supporting_sources = False
    
    # Extract sources from available data
    for fc in fact_checks[:3]:
        for review in fc.get("claimReview", []):
            rating = review.get("textualRating", "").lower()
            stance = "neutral"
            if any(kw in rating for kw in ["true", "correct", "verified"]):
                stance = "supports"
                has_supporting_sources = True
            elif any(kw in rating for kw in ["false", "incorrect", "debunked"]):
                stance = "contradicts"
                has_contradicting_sources = True
            
            sources_cited.append({
                "type": "fact-check",
                "publisher": review.get("publisher", {}).get("name", "Unknown"),
                "rating": review.get("textualRating", "Unrated"),
                "url": review.get("url", ""),
                "date": review.get("reviewDate", ""),
                "stance": stance,
                "excerpt": fc.get("text", "")[:100]
            })
    
    for art in news_data.get("articles", [])[:3]:
        sources_cited.append({
            "type": "news",
            "source": art.get("source", "Unknown"),
            "title": art.get("title", ""),
            "url": art.get("url", ""),
            "date": art.get("publishedAt", ""),
            "stance": "neutral",
            "excerpt": art.get("description", "")[:100]
        })
    
    # Determine verdict based on available sources
    if sources_cited and (has_supporting_sources or has_contradicting_sources):
        verdict = "mixed" if (has_supporting_sources and has_contradicting_sources) else ("true" if has_supporting_sources else "false")
        confidence = "medium"
        reasoning = f"Based on available fact-checks and news coverage: {len(sources_cited)} source(s) found."
    elif news_count >= 3:
        verdict = "mixed"
        confidence = "low"
        reasoning = f"Significant news coverage found ({news_count} articles). Requires manual review for full context."
    else:
        verdict = "unverified"
        confidence = "low"
        reasoning = "Insufficient evidence available. Claim may be too recent or niche."
    
    return {
        "verdict": verdict,
        "confidence": confidence,
        "source": "System (Fallback Analysis)",
        "summary": f"Verdict: {verdict.upper()} (with {confidence} confidence)",
        "detailed_reasoning": reasoning,
        "key_findings": [
            f"Found {len(fact_checks)} fact-check(s)",
            f"Found {news_count} news article(s)"
        ],
        "red_flags": [] if verdict != "unverified" else ["Limited data available — review sources for context."],
        "what_to_watch": "Check the sources below for the latest information.",
        "evidence_assessment": {
            "source_agreement": "partial" if verdict == "mixed" else ("agree" if verdict != "unverified" else "insufficient"),
            "fact_checks_summary": f"{len(fact_checks)} fact-check(s) found from professional databases.",
            "news_coverage_summary": f"{news_count} news article(s) covering this topic.",
            "trending_context": "Recent topic with multiple sources" if news_count > 0 else "Unable to assess without data."
        },
        "sources_cited": sources_cited,
        "totalFactChecks": len(fact_checks),
        "totalNewsArticles": news_count
    }


# ═══════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════

@app.route('/fact-check', methods=['POST'])
def handle_fact_check():
    """POST /fact-check → full fact-check pipeline with intelligent fallbacks."""
    query = request.form.get('query')
    if not query:
        return jsonify({"status": "error", "message": "No query"}), 400

    doc = nlp(query)
    search_term = next(doc.sents).text if list(doc.sents) else query

    try:
        # ── Step 1: Try multiple search variations ──
        all_fact_checks = []
        search_variations = generate_search_variations(search_term)
        
        for variation in search_variations:
            params = {
                "query": variation,
                "key": GOOGLE_API_KEY,
                "languageCode": "en",
                "pageSize": 10
            }
            try:
                google_data = requests.get(GOOGLE_URL, params=params, timeout=10).json()
                raw_claims = google_data.get('claims', [])
                all_fact_checks.extend(raw_claims)
            except Exception as e:
                print(f"❌ CLAUDE ERROR: {type(e).__name__} - {str(e)}") # This tells you if it's a 404, 429, or JSON error
                return None

        # Remove duplicates
        seen_urls = set()
        unique_claims = []
        for claim in all_fact_checks:
            for review in claim.get("claimReview", []):
                url = review.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_claims.append(claim)
                    break

        # ✅ Enrich with relevance + rating categories
        fact_checks = enrich_fact_checks(unique_claims, search_term)

        # ── Step 2: Fetch news ──
        news_data = fetch_news(search_term)

        # ── Step 3: AI Analysis with intelligent fallback ──
        verdict_obj = None
        
        # Try Claude first
        if len(fact_checks) > 0 or news_data.get("total_articles", 0) > 0:
            print(f"Claude: Found {len(fact_checks)} fact-checks and {news_data.get('total_articles', 0)} news articles")
            verdict_obj = get_claude_analysis(search_term, fact_checks, news_data)

        # Fallback to Gemini real-time analysis if limited fact-checks but news exists
        if verdict_obj is None and news_data.get("total_articles", 0) >= 3:
            print("⚠️ Claude failed. Using Gemini Real-time Analysis...")
            verdict_obj = get_gemini_realtime_analysis(search_term, news_data.get("articles", []))

        # Final fallback: Use available data intelligently
        if verdict_obj is None:
            print("⚠️ Both AI services failed. Using Fallback Analysis...")
            verdict_obj = fallback_verdict(fact_checks, news_data, search_term)

        # Ensure verdict_obj has all required fields
        if verdict_obj:
            verdict_obj["totalFactChecks"] = len(fact_checks)
            verdict_obj["totalNewsArticles"] = news_data.get("total_articles", 0)

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
            "sources_cited": verdict_obj.get("sources_cited", []) if verdict_obj else [],
            "trending_matches": []
        }

        return jsonify({"status": "success", "results": [result_item]})

    except Exception as e:
        print(f"Fact-check error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


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


@app.before_request
def handle_preflight():
    """Handle CORS preflight requests."""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)