import os
import json
import anthropic
from models.models import VerificationStatus, CheckedVia

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

VERDICT_MAP = {
    "true":          VerificationStatus.TRUE,
    "false":         VerificationStatus.FALSE,
    "partially_true": VerificationStatus.PARTIALLY_TRUE,
}

def analyze_claim(claim: str) -> dict | None:
    """
    Sends a claim to Claude and returns a structured verdict dict,
    or None if the API call fails.

    Returns:
        {
            "verdict":          VerificationStatus,
            "confidence_score": float (0-100),
            "explanation":      str,
            "checked_via":      CheckedVia.LLM,
        }
    """
    prompt = f"""You are a fact-checking assistant. Analyze the following claim and respond ONLY with a JSON object — no preamble, no markdown.

Claim: "{claim}"

Respond with exactly this structure:
{{
  "verdict": "true" | "false" | "partially_true",
  "confidence_score": <number 0-100>,
  "explanation": "<one or two sentence explanation>"
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text.strip()
        data = json.loads(raw)

        verdict_str = data.get("verdict", "").lower()
        verdict = VERDICT_MAP.get(verdict_str)
        if verdict is None:
            return None

        return {
            "verdict":          verdict,
            "confidence_score": float(data.get("confidence_score", 50)),
            "explanation":      data.get("explanation", ""),
            "checked_via":      CheckedVia.LLM,
        }

    except Exception as e:
        print(f"[ai_analyzer] Error: {e}")
        return None