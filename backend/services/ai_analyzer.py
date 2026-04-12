import os
import json
import google.generativeai as genai
from models.models import VerificationStatus, CheckedVia

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

VERDICT_MAP = {
    "true":           VerificationStatus.TRUE,
    "false":          VerificationStatus.FALSE,
    "partially_true": VerificationStatus.PARTIALLY_TRUE,
}


def analyze_claim(claim: str) -> dict | None:
    """
    Sends a claim to Gemini and returns a structured verdict dict,
    or None if the API call fails.
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
        response = model.generate_content(prompt)
        raw = response.text.strip()
        # Strip markdown fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
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
        print(f"[ai_analyzer] Gemini error: {e}")
        return None