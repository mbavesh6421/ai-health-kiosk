from fastapi import APIRouter
from ..services import cache

router = APIRouter(prefix="/offline", tags=["Offline Mode"])


@router.get("/bundle")
def get_offline_bundle():
    """
    The frontend fetches this ONCE when online and caches it in
    localStorage/IndexedDB. When navigator.onLine is false, the app answers
    symptom queries and education tips from this bundle instead of calling
    the network — so the kiosk keeps working through connectivity drops.
    """
    return {
        "symptom_responses": cache.OFFLINE_SYMPTOM_RESPONSES,
        "education_tips": cache.HEALTH_EDUCATION_TIPS,
        "emergency_keywords": cache.EMERGENCY_KEYWORDS,
        "emergency_advice": cache.EMERGENCY_ADVICE,
    }
