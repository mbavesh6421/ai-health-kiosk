import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from gtts import gTTS

router = APIRouter(prefix="/tts", tags=["Text to Speech"])

# gTTS language codes (subset relevant to this kiosk)
GTTS_LANG_MAP = {
    "en": "en", "hi": "hi", "bn": "bn", "ta": "ta", "te": "te",
    "mr": "mr", "gu": "gu", "kn": "kn", "ml": "ml", "ur": "ur",
        "pa": "pa", "fr": "fr", "es": "es", "ar": "ar",
}


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


@router.post("")
async def synthesize(req: TTSRequest):
    lang = GTTS_LANG_MAP.get(req.language, "en")
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty.")

    try:
        buf = io.BytesIO()
        gTTS(text=req.text, lang=lang).write_to_fp(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/mpeg", headers={
            "Content-Disposition": "inline; filename=advice.mp3"
        })
    except Exception as exc:
        # gTTS needs outbound internet access to Google Translate's TTS endpoint.
        raise HTTPException(status_code=503, detail=f"Speech synthesis unavailable: {exc}")
