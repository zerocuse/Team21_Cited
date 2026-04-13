"""
Source credibility scoring algorithm.

Tier hierarchy (highest → lowest):
  1. Primary documents / artifacts  (.pdf, official docs)     → 95
  2. Government sources             (.gov, .mil)              → 90-92
  3. Academic / institutional       (.edu, .ac.*, .int)       → 85-88
  4. Established fact-checkers      (snopes, politifact, …)   → 82
  5. Non-profit / NGO               (.org)                    → 72
  6. Reputable news agencies        (reuters, ap, bbc, …)     → 68
  7. Commercial / general news      (.com, .net, other)       → 55
  8. Social media                   (twitter, facebook, …)    → 25

Future extension: author credibility scores can be averaged in as a ninth dimension.
"""

from urllib.parse import urlparse

# ----- lookup tables -------------------------------------------------------

TLD_SCORES: dict[str, float] = {
    "gov": 92.0,
    "mil": 90.0,
    "edu": 87.0,
    "ac":  85.0,   # e.g. .ac.uk
    "int": 85.0,
    "org": 72.0,
    "net": 55.0,
    "com": 55.0,
}

# Substrings matched against the full hostname (lower-cased)
KNOWN_PUBLISHER_SCORES: dict[str, float] = {
    # Dedicated fact-checkers
    "politifact":        82.0,
    "snopes":            82.0,
    "factcheck.org":     82.0,
    "fullfact":          82.0,
    "africacheck":       80.0,
    "checkyourfact":     78.0,
    # Major wire services
    "reuters":           68.0,
    "apnews":            68.0,
    "associated press":  68.0,
    # Established broadcasters
    "bbc":               66.0,
    "npr":               65.0,
    "pbs":               65.0,
    # Major newspapers
    "washingtonpost":    63.0,
    "nytimes":           63.0,
    "theguardian":       62.0,
    "economist":         65.0,
    "wsj":               63.0,
}

SOCIAL_MEDIA_HOSTS: set[str] = {
    "twitter.com", "x.com", "facebook.com", "instagram.com",
    "tiktok.com", "reddit.com", "youtube.com", "threads.net",
}

PRIMARY_DOC_EXTENSIONS: set[str] = {".pdf", ".doc", ".docx", ".ppt", ".pptx"}
PRIMARY_DOC_PATH_KEYWORDS: set[str] = {"/official/", "/documents/", "/report/", "/publication/"}


# ----- helpers ---------------------------------------------------------------

def _score_url(url: str) -> float:
    """Return a credibility score for a single URL."""
    if not url:
        return 40.0
    try:
        parsed = urlparse(url.lower())
        host  = parsed.hostname or ""
        path  = parsed.path

        # Social media → lowest tier
        if any(sm in host for sm in SOCIAL_MEDIA_HOSTS):
            return 25.0

        # Primary document / artifact
        if any(path.endswith(ext) for ext in PRIMARY_DOC_EXTENSIONS):
            return 95.0
        if any(kw in path for kw in PRIMARY_DOC_PATH_KEYWORDS):
            return 92.0

        # Known publishers matched by host
        for keyword, score in KNOWN_PUBLISHER_SCORES.items():
            if keyword in host:
                return score

        # TLD-based fallback (handles .ac.uk via second-to-last part too)
        parts = host.split(".")
        tld = parts[-1] if parts else ""
        second_tld = parts[-2] if len(parts) >= 2 else ""

        if second_tld == "ac":          # e.g. ox.ac.uk
            return TLD_SCORES["ac"]
        return TLD_SCORES.get(tld, 50.0)

    except Exception:
        return 40.0


def _score_publisher_name(name: str) -> float | None:
    """Return a score based on the publisher's display name, or None if unknown."""
    if not name:
        return None
    name_lower = name.lower()
    for keyword, score in KNOWN_PUBLISHER_SCORES.items():
        if keyword in name_lower:
            return score
    return None


# ----- public API ------------------------------------------------------------

def credibility_weight(score: float) -> float:
    """
    Convert a numeric credibility score into a vote weight used by the
    verdict algorithm.  The scale is deliberately steep so that one
    high-authority source can outweigh many low-quality ones.

    Tier weights (approximate real-world ratios):
      gov / primary docs  (≥ 88)  → 16 ×   – e.g. 1 .gov beats ~15 .com sites
      fact-checkers / academic (≥ 78)  → 8 ×
      reputable news      (≥ 65)  → 3 ×
      general commercial  (≥ 50)  → 1 ×   (baseline)
      low-quality blogs   (≥ 35)  → 0.25 ×
      social media / junk (< 35)  → 0.1 ×
    """
    if score >= 88:
        return 16.0
    if score >= 78:
        return 8.0
    if score >= 65:
        return 3.0
    if score >= 50:
        return 1.0
    if score >= 35:
        return 0.25
    return 0.1


def score_single_source(url: str, publisher_name: str = "") -> float:
    """
    Score one source using both its URL and publisher name.
    Takes the higher of the two signals.
    """
    url_score  = _score_url(url)
    name_score = _score_publisher_name(publisher_name)
    if name_score is not None:
        return max(url_score, name_score)
    return url_score


def compute_source_credibility(fact_checks: list) -> float:
    """
    Aggregate credibility score (0–100) from a list of Google Fact Check claims.

    Each claimReview entry contributes one score; the final value is a
    simple average so that more reviews don't artificially inflate the score.
    """
    scores: list[float] = []

    for claim in fact_checks:
        for review in claim.get("claimReview", []):
            url   = review.get("url", "")
            name  = review.get("publisher", {}).get("name", "")
            scores.append(score_single_source(url, name))

    if not scores:
        return 50.0

    return round(sum(scores) / len(scores), 2)


def compute_confidence(fact_checks: list, verdict: dict) -> float:
    """
    Final confidence score combining:
      • Source credibility  (65 % weight) – quality of the checking organisations
      • Dominance           (35 % weight) – credibility-weighted share held by
                                            the winning verdict category

    Returns a float in [0, 100].
    """
    source_cred = compute_source_credibility(fact_checks)
    # dominance is pre-computed by build_verdict() as a credibility-weighted %
    dominance = verdict.get("dominance", 50.0)
    score = source_cred * 0.65 + dominance * 0.35
    return round(min(100.0, score), 2)
