"""
Thin wrapper around the Hugging Face free Inference API.
Used by /symptom-checker and /education.
If HF_API_TOKEN is not set, or the call fails/times out (free-tier
models can be slow to "warm up" or rate-limited), we fall back to the
static offline dataset in `cache.py` so the feature never hard-fails.
"""
import httpx
from ..config import settings

TIMEOUT = 20.0


async def generate(prompt: str, model: str | None = None, max_new_tokens: int = 220) -> tuple[str, bool]:
    """Returns (text, used_live_model)."""
    if not settings.HF_API_TOKEN:
        return "", False

    model = model or settings.HF_SYMPTOM_MODEL
    url = f"{settings.HF_API_URL}/{model}"
    headers = {"Authorization": f"Bearer {settings.HF_API_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": 0.4,
            "return_full_text": False,
        },
        "options": {"wait_for_model": True},
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and data and "generated_text" in data[0]:
                return data[0]["generated_text"].strip(), True
            if isinstance(data, dict) and "generated_text" in data:
                return data["generated_text"].strip(), True
            return "", False
    except Exception as exc:  # network error, rate-limit, cold-start timeout, etc.
        print(f"[hf_client] Falling back to offline dataset: {exc}")
        return "", False
