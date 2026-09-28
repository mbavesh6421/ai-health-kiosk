import asyncio
import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from ..config import settings
from ..services import gemini_client

router = APIRouter(prefix="/translate", tags=["Translation"])

SUPPORTED_LANGUAGES = {
    "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
    "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi",
    "ur": "Urdu", "fr": "French", "es": "Spanish", "ar": "Arabic",
}


class TranslateRequest(BaseModel):
    text: str
    target_lang: str  # e.g. "te"
    source_lang: str = "en"


class TranslateResponse(BaseModel):
    translated_text: str
    used_live_service: bool
    target_lang: str
    provider: str = "none"  # gemini | google | libretranslate | none


@router.get("/languages")
def list_languages():
    return SUPPORTED_LANGUAGES


async def _via_gemini(text: str, target: str, source: str) -> str | None:
    if not gemini_client.is_configured():
        return None
    prompt = (
        f"Translate this health advice from {SUPPORTED_LANGUAGES.get(source, source)} into "
        f"{SUPPORTED_LANGUAGES[target]}. Use simple, natural, everyday words that a rural villager "
        f"would understand (not literary or bookish words). Keep numbers, medicine names and "
        f"medical meaning exactly correct. Output ONLY the translation, nothing else.\n\n{text}"
    )
    return await gemini_client.generate(prompt, temperature=0.1)


def _google_sync(text: str, target: str, source: str) -> str:
    from deep_translator import GoogleTranslator  # free, no API key
    return GoogleTranslator(source=source, target=target).translate(text)


async def _via_google(text: str, target: str, source: str) -> str | None:
    try:
        out = await asyncio.to_thread(_google_sync, text, target, source)
        return out.strip() if out else None
    except Exception as exc:
        print(f"[translate] Google web translation failed: {exc}")
        return None


async def _via_libretranslate(text: str, target: str, source: str) -> str | None:
    payload = {"q": text, "source": source, "target": target, "format": "text"}
    if settings.LIBRETRANSLATE_API_KEY:
        payload["api_key"] = settings.LIBRETRANSLATE_API_KEY
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(settings.LIBRETRANSLATE_URL, json=payload)
            resp.raise_for_status()
            return resp.json().get("translatedText")
    except Exception as exc:
        print(f"[translate] LibreTranslate failed: {exc}")
        return None


@router.post("", response_model=TranslateResponse)
async def translate_text(req: TranslateRequest):
    if req.target_lang == req.source_lang or req.target_lang not in SUPPORTED_LANGUAGES:
        return TranslateResponse(translated_text=req.text, used_live_service=False,
                                 target_lang=req.target_lang)

    for provider, fn in (("gemini", _via_gemini), ("google", _via_google),
                         ("libretranslate", _via_libretranslate)):
        out = await fn(req.text, req.target_lang, req.source_lang)
        if out:
            return TranslateResponse(translated_text=out, used_live_service=True,
                                     target_lang=req.target_lang, provider=provider)

    return TranslateResponse(translated_text=req.text, used_live_service=False,
                             target_lang=req.target_lang, provider="none")