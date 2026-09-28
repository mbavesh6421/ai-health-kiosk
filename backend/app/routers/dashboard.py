import re
from collections import Counter
from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from ..services import firebase_client
from ..config import settings

router = APIRouter(prefix="/dashboard", tags=["Community Dashboard"])

KEYWORDS_OF_INTEREST = [
    "fever", "cough", "cold", "diarrhea", "vomiting", "rash", "headache",
    "body ache", "sore throat", "breathing", "dengue", "malaria",
]


def _require_doctor(x_doctor_code: Optional[str]):
    if x_doctor_code != settings.DOCTOR_ACCESS_CODE:
        raise HTTPException(status_code=401, detail="Invalid or missing doctor access code.")


@router.get("/outbreak")
def outbreak_trends(x_doctor_code: Optional[str] = Header(default=None)):
    """
    Aggregates ANONYMIZED symptom keyword counts and area counts across all
    stored records, for early outbreak signal detection. No patient names or
    phone numbers are returned — only counts.
    """
    _require_doctor(x_doctor_code)
    records = firebase_client.list_documents("patient_records")

    symptom_counter = Counter()
    area_counter = Counter()

    for r in records:
        text = (r.get("symptoms") or "").lower()
        for kw in KEYWORDS_OF_INTEREST:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                symptom_counter[kw] += 1
        area = r.get("village_or_area")
        if area:
            area_counter[area] += 1

    return {
        "total_visits": len(records),
        "symptom_counts": dict(symptom_counter.most_common()),
        "area_counts": dict(area_counter.most_common()),
    }
