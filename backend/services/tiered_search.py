"""
Tiered fact-checking source finder.

Priority order:
  1. Cited cached database  (KnowledgeBaseEntry table)
  2. Expert-driven fact databases  (Google Fact Check API)
  3. Web scraping for primary documents  (.gov / .edu / .org / PDFs via Gemini)
  4. Normal web search  (Gemini API with Google Search grounding)
"""

import os
import requests
from urllib.parse import urlparse

GOOGLE_FACT_CHECK_KEY = os.getenv("GOOGLE_FACT_CHECK")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

PRIMARY_DOC_TLDS = {"gov", "edu", "mil", "int"}
PRIMARY_DOC_SECOND_LEVEL = {"ac"}          # catches .ac.uk, .ac.nz, etc.


# ── Helpers ──────────────────────────────────────────────────────────────────

def _is_primary_source(url: str) -> bool:
    """Return True when the URL looks like an official/primary-document source."""
    try:
        parsed = urlparse(url.lower())
        host = parsed.hostname or ""
        path = parsed.path
        parts = host.split(".")
        tld = parts[-1] if parts else ""
        second = parts[-2] if len(parts) >= 2 else ""
        return (
            tld in PRIMARY_DOC_TLDS
            or second in PRIMARY_DOC_SECOND_LEVEL
            or path.lower().endswith(".pdf")
        )
    except Exception:
        return False


# ── Tier 1 – Cited database cache ────────────────────────────────────────────

def search_tier1_cached_db(search_term: str) -> list[dict]:
    """Query KnowledgeBaseEntry for previously verified cached results."""
    try:
        from models.models import KnowledgeBaseEntry
        import sqlalchemy as sa

        keywords = [w for w in search_term.lower().split() if len(w) > 3]
        if not keywords:
            return []

        filters = [KnowledgeBaseEntry.content.ilike(f"%{kw}%") for kw in keywords[:5]]
        entries = KnowledgeBaseEntry.query.filter(sa.or_(*filters)).limit(5).all()

        return [
            {
                "url": "",
                "title": entry.umbrellaTopic,
                "preview": (entry.summary or entry.content)[:400],
                "tier": "cached_db",
                "tier_label": "Cited Database Cache",
                "rating": entry.verificationStatus.value if entry.verificationStatus else "unrated",
                "relevance_score": 0.95,
                "publisher": "Cited Knowledge Base",
            }
            for entry in entries
        ]
    except Exception as e:
        print(f"[Tier 1] DB search error: {e}")
        return []


# ── Tier 2 – Google Fact Check API ───────────────────────────────────────────

def search_tier2_google_fact_check(search_term: str) -> tuple[list, list[dict]]:
    """
    Query the Google Fact Check API.

    Returns:
        (raw_claims_list, normalised_source_list)
    """
    if not GOOGLE_FACT_CHECK_KEY:
        return [], []
    try:
        resp = requests.get(
            GOOGLE_FACT_CHECK_URL,
            params={"query": search_term, "key": GOOGLE_FACT_CHECK_KEY, "languageCode": "en"},
            timeout=10,
        )
        raw_claims = resp.json().get("claims", [])

        sources = []
        for claim in raw_claims:
            for review in claim.get("claimReview", []):
                url = review.get("url", "")
                publisher = review.get("publisher", {}).get("name", "Unknown")
                rating = review.get("textualRating", "unrated")
                claim_text = claim.get("text", "")
                sources.append({
                    "url": url,
                    "title": publisher,
                    "preview": f"Rated '{rating}': {claim_text[:280]}",
                    "tier": "expert_fact_check",
                    "tier_label": "Expert Fact Check",
                    "rating": rating,
                    "relevance_score": 0.95,
                    "publisher": publisher,
                })
        return raw_claims, sources
    except Exception as e:
        print(f"[Tier 2] Google Fact Check error: {e}")
        return [], []


# ── Gemini helpers ────────────────────────────────────────────────────────────

def _gemini_search(prompt: str) -> dict:
    """POST to Gemini with Google Search grounding. Returns raw API response."""
    if not GEMINI_API_KEY:
        return {}
    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "tools": [{"google_search": {}}],
                "generationConfig": {"maxOutputTokens": 1024},
            },
            timeout=20,
        )
        return resp.json()
    except Exception as e:
        print(f"[Gemini] Request error: {e}")
        return {}


def _parse_gemini_response(data: dict, tier: str, tier_label: str) -> tuple[str, list[dict]]:
    """
    Parse a Gemini grounded response into (generated_text, sources_list).
    """
    sources: list[dict] = []
    gen_text = ""
    try:
        candidate = (data.get("candidates") or [{}])[0]
        for part in candidate.get("content", {}).get("parts", []):
            gen_text += part.get("text", "")

        meta = candidate.get("groundingMetadata", {})
        chunks = meta.get("groundingChunks", [])
        supports = meta.get("groundingSupports", [])

        # Map chunk index → supporting text snippets
        snippet_map: dict[int, list[str]] = {}
        for sup in supports:
            seg_text = sup.get("segment", {}).get("text", "")
            for idx in sup.get("groundingChunkIndices", []):
                snippet_map.setdefault(idx, []).append(seg_text)

        for i, chunk in enumerate(chunks):
            web = chunk.get("web", {})
            url = web.get("uri", "")
            title = web.get("title", "") or url
            if not url:
                continue
            snippets = snippet_map.get(i, [])
            preview = " … ".join(snippets[:2]) if snippets else gen_text[:300]
            sources.append({
                "url": url,
                "title": title,
                "preview": preview[:500],
                "tier": tier,
                "tier_label": tier_label,
                "rating": "unrated",
                "relevance_score": 0.75,
                "publisher": urlparse(url).hostname or "",
            })
    except Exception as e:
        print(f"[Gemini] Parse error: {e}")
    return gen_text, sources


# ── Tier 3 – Web scraping for primary documents ───────────────────────────────

def _scrape_snippet(url: str, keywords: list[str]) -> str:
    """Fetch a page and return the most keyword-relevant sentence."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return ""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CitedFactChecker/1.0)"},
            timeout=8,
        )
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 30]
        best, best_score = "", 0
        for s in sentences:
            score = sum(1 for kw in keywords if kw in s.lower())
            if score > best_score:
                best, best_score = s, score
        return (best[:400] + "…") if best else ""
    except Exception:
        return ""


def search_tier3_gov_academic(search_term: str) -> list[dict]:
    """
    Ask Gemini to locate government (.gov, .mil) and academic (.edu) primary
    sources that directly address the claim.  Only results that pass
    _is_primary_source() are returned — no fallback to .org or general sites.
    """
    prompt = (
        f'Find official government reports, legislative documents, or peer-reviewed '
        f'academic research from .gov, .mil, or .edu domains that directly verify or '
        f'refute this claim: "{search_term}". '
        f'Cite specific factual findings from government agencies and academic institutions only.'
    )
    data = _gemini_search(prompt)
    _, sources = _parse_gemini_response(data, "web_scrape", "Official Document")

    # Strict filter: only genuine government / academic sources
    primary = [s for s in sources if _is_primary_source(s["url"])]

    keywords = [w.lower() for w in search_term.split() if len(w) > 3]
    for src in primary[:3]:
        url = src.get("url", "")
        if url and not url.lower().endswith(".pdf"):
            snippet = _scrape_snippet(url, keywords)
            if snippet:
                src["preview"] = snippet

    return primary[:3]


# ── Tier 4 – General web search ───────────────────────────────────────────────

def search_tier4_web_search(search_term: str) -> tuple[list[dict], str]:
    """
    General Gemini web search with Google Search grounding.

    Returns:
        (sources_list, generated_analysis_text)
    """
    prompt = (
        f'Fact-check this claim using current web information: "{search_term}". '
        f'Search the web and evaluate whether this claim is TRUE, FALSE, or PARTIALLY TRUE '
        f'based on available evidence. Explain your reasoning concisely.'
    )
    data = _gemini_search(prompt)
    gen_text, sources = _parse_gemini_response(data, "web_search", "Web Search")

    if gen_text and len(gen_text) > 50:
        sources.insert(0, {
            "url": "",
            "title": "Web Search Analysis",
            "preview": gen_text[:500],
            "tier": "web_search",
            "tier_label": "Web Search",
            "rating": "unrated",
            "relevance_score": 0.6,
            "publisher": "Gemini + Google Search",
        })

    return sources[:5], gen_text


# ── Orchestrator ──────────────────────────────────────────────────────────────

ALL_METHODS = {"web-scrape", "cited-database", "expert-driven"}


def _google_claims_are_conclusive(raw_claims: list) -> bool:
    """
    Return True when at least one Google Fact Check review carries an
    explicit, non-trivial textual rating.  An empty or 'unrated' rating
    means the claim is not yet settled.
    """
    _SKIP = {"", "unrated", "n/a", "none", "no rating"}
    for claim in raw_claims:
        for review in claim.get("claimReview", []):
            rating = review.get("textualRating", "").lower().strip()
            if rating and rating not in _SKIP:
                return True
    return False


def run_tiered_search(search_term: str, methods: list[str] | None = None) -> dict:
    """
    Execute the tiered fact-checking pipeline with strict priority order and
    early-exit ("settled") gates.

    Priority order
    ──────────────
    1. Cited Database   – our curated cache; always authoritative → settles on any hit
    2. Expert-Driven    – Google Fact Check API → settles when a conclusive rating exists
    3. Official Docs    – gov / academic primary sources (.gov, .mil, .edu) → settles on any hit
    4. General Web      – Gemini web search; only runs if claim is still unsettled
                          OR source pool is too thin (< 2 results)

    The pipeline stops escalating as soon as the claim is settled, preventing
    low-quality general web results from diluting high-quality authoritative ones.

    ``methods`` controls which named tiers are active:
        'cited-database'  →  Tier 1
        'expert-driven'   →  Tier 2
        'web-scrape'      →  Tier 3 (gov/academic)  +  Tier 4 fallback
    When ``methods`` is None / empty every tier is enabled.
    """
    if not methods:
        methods = list(ALL_METHODS)

    active = set(methods)

    all_sources: list[dict] = []
    raw_google_claims: list = []
    gemini_analysis: str = ""
    tiers_searched: list[str] = []
    counts = {"cached_db": 0, "expert_fact_check": 0, "web_scrape": 0, "web_search": 0}
    settled = False   # True once a high-quality source has resolved the claim

    # ── Tier 1 – Cited Database (highest priority) ────────────────────────────
    if "cited-database" in active:
        t1 = search_tier1_cached_db(search_term)
        if t1:
            all_sources.extend(t1)
            counts["cached_db"] = len(t1)
            tiers_searched.append("cached_db")
            settled = True   # curated cache is authoritative; no need to escalate

    # ── Tier 2 – Expert / Google Fact Check ──────────────────────────────────
    if "expert-driven" in active and not settled:
        raw_google_claims, t2 = search_tier2_google_fact_check(search_term)
        if t2:
            all_sources.extend(t2)
            counts["expert_fact_check"] = len(t2)
            tiers_searched.append("expert_fact_check")
            if _google_claims_are_conclusive(raw_google_claims):
                settled = True

    # ── Tier 3 – Official Government & Academic Documents ────────────────────
    # Runs only when earlier tiers haven't settled the claim.
    # Does NOT fall back to general .org / .com sources — strictly gov/academic.
    if "web-scrape" in active and not settled:
        t3 = search_tier3_gov_academic(search_term)
        if t3:
            all_sources.extend(t3)
            counts["web_scrape"] = len(t3)
            tiers_searched.append("web_scrape")
            settled = True   # official government/academic docs are authoritative

    # ── Tier 4 – General Web Search (last resort) ─────────────────────────────
    # Runs only when the claim is still unsettled OR we have too few sources.
    # Kept as a fallback so claims with no structured data still get an analysis.
    if not settled or len(all_sources) < 2:
        t4, gemini_analysis = search_tier4_web_search(search_term)
        if t4:
            all_sources.extend(t4)
            counts["web_search"] = len(t4)
            tiers_searched.append("web_search")

    return {
        "all_sources":      all_sources,
        "raw_google_claims": raw_google_claims,
        "gemini_analysis":  gemini_analysis,
        "tiers_searched":   tiers_searched,
        "sources_by_tier":  counts,
        "settled":          settled,
    }
