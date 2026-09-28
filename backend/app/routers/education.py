from fastapi import APIRouter
from pydantic import BaseModel
from ..services import hf_client, cache

router = APIRouter(prefix="/education", tags=["Health Education"])

TOPICS = list(cache.HEALTH_EDUCATION_TIPS.keys())

PROMPT_TEMPLATE = (
    "Write one short, friendly public-health tip (max 60 words) for a rural Indian "
    "community health kiosk on the topic: \"{topic}\". Keep it practical and easy to "
    "understand for someone with no medical background."
)


class EducationResponse(BaseModel):
    topic: str
    tip: str
    source: str


@router.get("/topics")
def list_topics():
    return TOPICS


@router.get("", response_model=EducationResponse)
async def get_tip(topic: str = "default"):
    prompt = PROMPT_TEMPLATE.format(topic=topic)
    text, live = await hf_client.generate(prompt, model=None, max_new_tokens=100)

    if live and text:
        return EducationResponse(topic=topic, tip=text, source="model")

    return EducationResponse(topic=topic, tip=cache.match_education_tip(topic), source="offline_cache")
