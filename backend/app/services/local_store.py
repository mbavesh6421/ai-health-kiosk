"""
Tiny JSON-file-backed store. This is the free, zero-setup fallback for
/records, /reminder and /dashboard so the whole app works before you've
wired up Firebase or Supabase. Swap `firebase_client.py` in and the
routers keep working unchanged (same function signatures).
"""
import json
import os
import uuid
from datetime import datetime, timezone
from threading import Lock
from ..config import settings

_lock = Lock()


def _path(name: str) -> str:
    return os.path.join(settings.DATA_DIR, f"{name}.json")


def _read(name: str) -> list:
    p = _path(name)
    if not os.path.exists(p):
        return []
    with open(p, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _write(name: str, items: list) -> None:
    with open(_path(name), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_item(collection: str, item: dict) -> dict:
    with _lock:
        items = _read(collection)
        item = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            **item,
        }
        items.append(item)
        _write(collection, items)
        return item


def list_items(collection: str, filter_fn=None) -> list:
    with _lock:
        items = _read(collection)
        if filter_fn:
            return [i for i in items if filter_fn(i)]
        return items


def get_item(collection: str, item_id: str) -> dict | None:
    with _lock:
        for i in _read(collection):
            if i.get("id") == item_id:
                return i
    return None
