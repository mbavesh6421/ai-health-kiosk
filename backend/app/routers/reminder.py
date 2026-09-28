from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..services import firebase_client

router = APIRouter(prefix="/reminder", tags=["Medicine Reminders"])

COLLECTION = "reminders"


class ReminderCreate(BaseModel):
    patient_phone: str
    medicine_name: str
    time_of_day: str  # e.g. "08:00", "20:00" — frontend schedules the local alarm
    notes: Optional[str] = None
    fcm_token: Optional[str] = None  # browser push token, if the patient granted notification permission


@router.post("")
def create_reminder(reminder: ReminderCreate):
    saved = firebase_client.add_document(COLLECTION, reminder.model_dump())
    pushed = False
    if reminder.fcm_token:
        pushed = firebase_client.send_push_notification(
            reminder.fcm_token,
            title="Medicine Reminder Set",
            body=f"Reminder saved for {reminder.medicine_name} at {reminder.time_of_day}.",
        )
    return {**saved, "push_confirmation_sent": pushed}


@router.get("/{patient_phone}")
def list_reminders(patient_phone: str):
    return firebase_client.list_documents(COLLECTION, field="patient_phone", value=patient_phone)


@router.post("/{reminder_id}/notify-now")
def trigger_now(reminder_id: str, fcm_token: str):
    """Manually fire a push for a reminder — used by a scheduled job (e.g. Cloud
    Scheduler hitting this endpoint) at the reminder's time_of_day."""
    pushed = firebase_client.send_push_notification(
        fcm_token, title="Time for your medicine", body="Don't forget to take your dose now."
    )
    return {"push_sent": pushed}
