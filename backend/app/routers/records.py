from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services import firebase_client
from ..config import settings

router = APIRouter(prefix="/records", tags=["Patient Records"])

COLLECTION = "patient_records"


class RecordCreate(BaseModel):
    patient_name: str
    age: Optional[int] = None
    phone: Optional[str] = None
    village_or_area: Optional[str] = None
    symptoms: Optional[str] = None
    advice_given: Optional[str] = None
    language: str = "en"


def _require_doctor(x_doctor_code: Optional[str]):
    if x_doctor_code != settings.DOCTOR_ACCESS_CODE:
        raise HTTPException(status_code=401, detail="Invalid or missing doctor access code.")


@router.post("")
def create_record(record: RecordCreate):
    """Patient-facing: save a visit/interaction (no auth — this is the intake step)."""
    saved = firebase_client.add_document(COLLECTION, record.model_dump())
    return saved


@router.get("/{patient_phone}")
def get_records_for_patient(patient_phone: str):
    """A patient (or kiosk) looking up their own past visits by phone number."""
    return firebase_client.list_documents(COLLECTION, field="phone", value=patient_phone)


@router.get("")
def list_all_records(x_doctor_code: Optional[str] = Header(default=None)):
    """Doctor dashboard: full list. Gated by a simple shared access code
    (set DOCTOR_ACCESS_CODE env var) — replace with real auth (Firebase Auth /
    OAuth) before any real deployment."""
    _require_doctor(x_doctor_code)
    return firebase_client.list_documents(COLLECTION)
