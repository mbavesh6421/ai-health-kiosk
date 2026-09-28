"""
Minimal Gemini (Google AI Studio) client using the REST API. No extra SDK needed.
Free tier: create a key at https://aistudio.google.com/apikey and set GEMINI_API_KEY.

Model names change often, so we try GEMINI_MODEL first and then a few fallbacks
if Google answers 404 (model not available for this key).
"""
import httpx
from ..config import settings

BASE = "https://generativelanguage.googleapis.com/v1beta/models"
FALLBACK_MODELS = ["gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-2.5-flash"]

_working_model: str | None = None


def is_configured() -> bool:
    return bool(settings.GEMINI_API_KEY)


async def generate(prompt: str, *, json_mode: bool = False, temperature: float = 0.3,
                   max_tokens: int = 1024) -> str | None:
    """Returns the model's text, or None if Gemini isn't configured / fails."""
    global _working_model
    if not settings.GEMINI_API_KEY:
        return None

    models = [_working_model] if _working_model else []
    for m in [settings.GEMINI_MODEL, *FALLBACK_MODELS]:
        if m not in models:
            models.append(m)

    gen_cfg = {"temperature": temperature, "maxOutputTokens": max_tokens}
    if json_mode:
        gen_cfg["responseMimeType"] = "application/json"
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": gen_cfg}
    headers = {"x-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=25.0) as client:
        for model in models:
            try:
                resp = await client.post(f"{BASE}/{model}:generateContent", headers=headers, json=body)
                if resp.status_code == 404:
                    continue  # this model name isn't available, try the next one
                resp.raise_for_status()
                parts = resp.json()["candidates"][0]["content"]["parts"]
                text = "".join(p.get("text", "") for p in parts).strip()
                if text:
                    _working_model = model
                    return text
            except Exception as exc:
                print(f"[gemini] {model} failed: {exc}")
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in (400, 401, 403, 429):
                    return None  # bad key / quota, other models won't help
    return None