import json
import re
from fastapi import APIRouter
from pydantic import BaseModel
from ..services import hf_client, cache, gemini_client
from .translate import SUPPORTED_LANGUAGES, _via_google

router = APIRouter(prefix="/symptom-checker", tags=["Symptom Checker"])


class SymptomRequest(BaseModel):
    symptoms: str
    language: str = "en"  # language the patient wants the advice in


class SymptomResponse(BaseModel):
    advice: str                   # in `advice_language`
    advice_language: str = "en"   # frontend translates only if this != requested language
    advice_en: str | None = None  # English copy (for the doctor-facing record)
    urgent: bool
    source: str  # "gemini" | "model" | "offline_cache"
    disclaimer: str = (
        "This is general guidance, not a medical diagnosis. For anything severe "
        "or persistent, please visit a doctor or Primary Health Centre."
    )


HF_PROMPT = (
    "You are a cautious primary-care health assistant for a rural health kiosk in India. "
    "A patient describes these symptoms: \"{symptoms}\". "
    "Give brief, practical, non-diagnostic guidance (home care steps + when to see a doctor). "
    "Keep it under 120 words. Do not name specific prescription drugs or dosages beyond "
    "common OTC guidance. If anything sounds severe, say so clearly."
)

GEMINI_PROMPT = """You are a cautious primary-care health assistant for a rural health kiosk in India.
The patient wrote (may be in any language): "{symptoms}"

Give brief, practical, NON-diagnostic guidance: simple home-care steps, then when to see a doctor.
Max 100 words. No prescription drug names or dosages (common OTC guidance only).
Write "advice" in {lang_name}, using simple everyday words a village resident understands.
Also give the same advice in English as "advice_en".
If ANY sign could be an emergency (chest pain, trouble breathing, stroke signs, heavy bleeding,
seizure, unconsciousness, poisoning, snake bite, very high fever in a baby, suicidal thoughts...),
set "urgent" to true and tell them to call 108 or go to the nearest hospital immediately.

Return ONLY valid JSON: {{"urgent": true or false, "advice": "...", "advice_en": "..."}}"""


def _parse_json(text: str) -> dict | None:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) and data.get("advice") else None
    except Exception:
        return None


def _has_non_ascii(s: str) -> bool:
    return any(ord(c) > 127 for c in s)


@router.post("", response_model=SymptomResponse)
async def check_symptoms(req: SymptomRequest):
    lang = req.language if req.language in SUPPORTED_LANGUAGES else "en"

    # Symptoms typed/spoken in Telugu, Hindi, etc.: make an English copy so the
    # emergency-keyword check and the HF/offline paths can understand them.
    symptoms_en = req.symptoms
    if _has_non_ascii(req.symptoms):
        symptoms_en = await _via_google(req.symptoms, "en", "auto") or req.symptoms

    keyword_urgent = (cache.contains_emergency_keyword(req.symptoms)
                      or cache.contains_emergency_keyword(symptoms_en))

    if keyword_urgent:
        return SymptomResponse(advice=cache.EMERGENCY_ADVICE, advice_language="en",
                               advice_en=cache.EMERGENCY_ADVICE, urgent=True, source="offline_cache")

    # 1) Gemini: understands the patient's own language and answers in it directly
    if gemini_client.is_configured():
        raw = await gemini_client.generate(
            GEMINI_PROMPT.format(symptoms=req.symptoms.replace('"', "'"),
                                 lang_name=SUPPORTED_LANGUAGES[lang]),
            json_mode=True, temperature=0.3, max_tokens=1200,
        )
        data = _parse_json(raw) if raw else None
        if data:
            return SymptomResponse(
                advice=data["advice"], advice_language=lang,
                advice_en=data.get("advice_en") or None,
                urgent=bool(data.get("urgent")), source="gemini",
            )

    # 2) Hugging Face (English)
    text, live = await hf_client.generate(HF_PROMPT.format(symptoms=symptoms_en), model=None)
    if live and text:
        return SymptomResponse(advice=text, advice_en=text, urgent=False, source="model")

    # 3) Offline dataset (English)
    fallback = cache.match_offline_symptom(symptoms_en)
    return SymptomResponse(advice=fallback, advice_en=fallback, urgent=False, source="offline_cache")
