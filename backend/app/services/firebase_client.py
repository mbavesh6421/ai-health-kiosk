"""
Optional Firebase integration (Firestore for records, FCM for reminders).
Activated automatically once FIREBASE_CREDENTIALS_JSON is set in the
environment (either a path to a service-account JSON file, or the raw
JSON content itself — handy for Cloud Run secrets). Until then, every
function transparently falls back to `local_store.py` so nothing breaks.
"""
import json
import os
from . import local_store
from ..config import settings

_firebase_ready = False
_db = None
_messaging = None

try:
    if settings.FIREBASE_CREDENTIALS_JSON:
        import firebase_admin
        from firebase_admin import credentials, firestore, messaging

        if os.path.exists(settings.FIREBASE_CREDENTIALS_JSON):
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_JSON)
        else:
            cred = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS_JSON))

        firebase_admin.initialize_app(cred)
        _db = firestore.client()
        _messaging = messaging
        _firebase_ready = True
except Exception as exc:  # pragma: no cover - defensive, keeps app booting
    print(f"[firebase_client] Falling back to local JSON store: {exc}")
    _firebase_ready = False


def is_live() -> bool:
    return _firebase_ready


def add_document(collection: str, data: dict) -> dict:
    if _firebase_ready:
        ref = _db.collection(collection).document()
        payload = {**data, "id": ref.id}
        ref.set(payload)
        return payload
    return local_store.add_item(collection, data)


def list_documents(collection: str, field: str | None = None, value=None) -> list:
    if _firebase_ready:
        query = _db.collection(collection)
        if field is not None:
            query = query.where(field, "==", value)
        return [doc.to_dict() for doc in query.stream()]
    if field is None:
        return local_store.list_items(collection)
    return local_store.list_items(collection, lambda i: i.get(field) == value)


def send_push_notification(fcm_token: str, title: str, body: str) -> bool:
    """Send an FCM push for a medicine reminder. Returns False (no-op) if
    Firebase isn't configured — the reminder is still stored, just not pushed."""
    if not _firebase_ready or not fcm_token:
        return False
    try:
        message = _messaging.Message(
            notification=_messaging.Notification(title=title, body=body),
            token=fcm_token,
        )
        _messaging.send(message)
        return True
    except Exception as exc:  # pragma: no cover
        print(f"[firebase_client] Push failed: {exc}")
        return False
