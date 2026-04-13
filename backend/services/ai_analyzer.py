import os
import json
from groq import Groq
from models.models import VerificationStatus, CheckedVia

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

VERDICT_MAP = {
    "true":           VerificationStatus.TRUE,
    "false":          VerificationStatus.FALSE,
    "partially_true": VerificationStatus.PARTIALLY_TRUE,
}

def _validate_sources(sources: list) -> list:
    """Remove sources with broken or hallucinated URLs."""
    import requests as req

    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CitedBot/1.0)"}
    validated = []

    for src in sources:
        url = src.get("url", "")
        if not url:
            continue
        try:
            # Try HEAD first, fall back to GET for sites that block HEAD
            r = req.head(url, timeout=5, allow_redirects=True, headers=HEADERS)
            if r.status_code == 403 or r.status_code == 405:
                r = req.get(url, timeout=5, allow_redirects=True, headers=HEADERS, stream=True)
                r.close()

            if r.status_code < 400:
                validated.append(src)
            else:
                print(f"[ai_analyzer] Dropped broken source [{r.status_code}]: {url}")
        except Exception:
            print(f"[ai_analyzer] Dropped unreachable source: {url}")

    return validated

def analyze_claim(claim: str) -> dict | None:
    prompt = f"""You are a fact-checking assistant. Analyze the following claim and respond ONLY with a JSON object — no preamble, no markdown.

Claim: "{claim}"

Respond with exactly this structure:
{{
  "verdict": "true" | "false" | "partially_true",
  "confidence_score": <number 0-100>,
  "explanation": "<one or two sentence explanation>",
  "sources": [
    {{
      "title": "<name of the source or article>",
      "url": "<full URL to the source>",
      "publisher": "<publisher name>"
    }}
  ]
}}

Include 2-3 real, verifiable sources that support your verdict. Only include sources you are confident actually exist."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        verdict_str = data.get("verdict", "").lower()
        verdict = VERDICT_MAP.get(verdict_str)
        if verdict is None:
            return None
        
        raw_sources = data.get("sources", [])
        valid_sources = _validate_sources(raw_sources)

        return {
            "verdict":          verdict,
            "confidence_score": float(data.get("confidence_score", 50)),
            "explanation":      data.get("explanation", ""),
            "checked_via":      CheckedVia.LLM,
            "sources":          data.get("sources", []),
        }

    except Exception as e:
        print(f"[ai_analyzer] Groq error: {e}")
        return None