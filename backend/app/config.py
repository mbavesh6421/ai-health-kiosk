"""
Central configuration for the AI Health Kiosk backend.
All values are read from environment variables so the same code works
locally (.env file) and on Cloud Run (env vars set via `gcloud run deploy --set-env-vars`).
Every integration degrades gracefully to a free/offline fallback if a
key is missing, so the app is runnable end-to-end with ZERO keys.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- Hugging Face Inference API (free tier w/ personal token) ---
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
    HF_SYMPTOM_MODEL: str = os.getenv("HF_SYMPTOM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
    HF_EDUCATION_MODEL: str = os.getenv("HF_EDUCATION_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
    HF_API_URL: str = "https://api-inference.huggingface.co/models"

    # --- Google Gemini API (free tier via https://aistudio.google.com/apikey) ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

    # --- Translation (LibreTranslate is the LAST-resort fallback) ---
    LIBRETRANSLATE_URL: str = os.getenv("LIBRETRANSLATE_URL", "https://libretranslate.com/translate")
    LIBRETRANSLATE_API_KEY: str = os.getenv("LIBRETRANSLATE_API_KEY", "")

    # --- Nominatim (OpenStreetMap) ---
    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org"
    NOMINATIM_USER_AGENT: str = os.getenv("NOMINATIM_USER_AGENT", "AIHealthKiosk/1.0 (hackathon prototype)")

    # --- Firebase (patient records, reminders via FCM) ---
    FIREBASE_CREDENTIALS_JSON: str = os.getenv("FIREBASE_CREDENTIALS_JSON", "")  # path OR raw JSON string
    FIREBASE_DB_URL: str = os.getenv("FIREBASE_DB_URL", "")

    # --- App / CORS ---
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    DOCTOR_ACCESS_CODE: str = os.getenv("DOCTOR_ACCESS_CODE", "demo-doctor-2026")  # simple gate, NOT production auth

    # --- Local data dir (fallback storage when Firebase isn't configured) ---
    DATA_DIR: str = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))


settings = Settings()

# A placeholder contact (you@example.com) gets HTTP 403 from OpenStreetMap, so ignore it.
if "example.com" in settings.NOMINATIM_USER_AGENT:
    settings.NOMINATIM_USER_AGENT = "AIHealthKiosk/1.0 (hackathon prototype)"

os.makedirs(settings.DATA_DIR, exist_ok=True)