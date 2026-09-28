from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import (
    symptom_checker, translate, tts, locator,
    records, reminder, education, offline, dashboard,
)

app = FastAPI(
    title="AI Health Kiosk API",
    description="Healthcare access backend: symptom checking, translation, TTS, "
                 "PHC locator, records, reminders, education, offline mode, and an "
                 "outbreak dashboard — built entirely on free-tier services.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(symptom_checker.router)
app.include_router(translate.router)
app.include_router(tts.router)
app.include_router(locator.router)
app.include_router(records.router)
app.include_router(reminder.router)
app.include_router(education.router)
app.include_router(offline.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "AI Health Kiosk API"}


@app.get("/healthz", tags=["Health"])
def healthz():
    """Cloud Run / uptime checks."""
    return {"status": "healthy"}
