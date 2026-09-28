# 🏥 AI Health Kiosk

A healthcare-access web app for underserved communities: symptom checking,
local-language support, voice output, a PHC/hospital locator, patient
records, medicine reminders, health education tips, offline mode, and a
doctor-facing community outbreak dashboard — built entirely on free-tier
APIs and services.

**Stack:** FastAPI (backend) + React/Vite (frontend). Backend → Cloud Run
(free tier). Frontend → Firebase Hosting (free tier).

Every external integration (Hugging Face, LibreTranslate, Firebase) has a
built-in fallback, so the whole app runs and demoes correctly with **zero
API keys** — you can add keys incrementally as you get them.

## How each feature maps to the code

| # | Feature | Backend | Frontend |
|---|---|---|---|
| 1 | Symptom checker chatbot | `routers/symptom_checker.py` | `SymptomChecker.jsx` |
| 2 | Local language support | `routers/translate.py` | `LanguageSelector.jsx` |
| 3 | Voice output (TTS) | `routers/tts.py` (gTTS) | "🔊 Listen" button in `SymptomChecker.jsx` |
| 4 | PHC / hospital locator | `routers/locator.py` (Overpass/Nominatim) | `PHCLocator.jsx` (Leaflet map) |
| 5 | Patient record storage | `routers/records.py` | intake form in `App.jsx`, table in `DoctorDashboard.jsx` |
| 6 | Medicine reminders | `routers/reminder.py` (+ FCM) | `ReminderForm.jsx` |
| 7 | Health education tips | `routers/education.py` | `HealthEducation.jsx` |
| 8 | Offline mode | `routers/offline.py` + `services/cache.py` | `offline.js` |
| 9 | Community outbreak dashboard | `routers/dashboard.py` | outbreak section in `DoctorDashboard.jsx` |

## 1. Run it locally

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill in keys as you get them — every field is optional
uvicorn app.main:app --reload --port 8080
```
Visit `http://localhost:8080/docs` for the interactive Swagger UI — try every
endpoint there before touching the frontend.

### Frontend
```bash
cd frontend
npm install
cp .env.example .env         # VITE_API_BASE=http://localhost:8080
npm run dev
```
Visit `http://localhost:5173`.

## 2. Getting free API keys (optional but recommended)

- **Hugging Face** (`HF_API_TOKEN`): create a free account at
  huggingface.co → Settings → Access Tokens. Free-tier inference can be
  slow to "cold start" the first call — the code sets `wait_for_model: true`
  and falls back to the offline cache if it still times out.
- **LibreTranslate**: the public `https://libretranslate.com/translate`
  endpoint works with no key for light use; for reliability, self-host it
  free via `docker run -p 5000:5000 libretranslate/libretranslate` and set
  `LIBRETRANSLATE_URL=http://localhost:5000/translate`.
- **Firebase**: create a free "Spark plan" project at
  console.firebase.google.com. Enable Firestore + Cloud Messaging. Generate
  a service-account key (Project Settings → Service Accounts → Generate
  new private key) and point `FIREBASE_CREDENTIALS_JSON` at that file (or
  paste its JSON directly as the env var on Cloud Run).
- **OpenStreetMap Overpass/Nominatim**: no key needed — just set a real
  contact in `NOMINATIM_USER_AGENT` per their usage policy.

Without any of these, records/reminders are stored in a local JSON file
(`backend/data/*.json`) and symptom/education answers use the built-in
offline dataset — good enough for a full working demo.

## 3. Deploy the backend to Cloud Run (free tier)

```bash
cd backend
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID

gcloud run deploy ai-health-kiosk-api \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars ALLOWED_ORIGINS=https://YOUR_FIREBASE_PROJECT.web.app \
  --set-env-vars HF_API_TOKEN=your_token_if_you_have_one \
  --set-env-vars DOCTOR_ACCESS_CODE=choose-a-real-code
```
Cloud Run's free tier covers ~2 million requests/month — plenty for a
pilot. Note the service URL it prints; you'll need it below.

For Firebase credentials on Cloud Run, either mount them as a Secret
Manager secret (`--set-secrets`) or paste the JSON directly as
`FIREBASE_CREDENTIALS_JSON`.

## 4. Deploy the frontend to Firebase Hosting (free tier)

```bash
cd frontend
npm install -g firebase-tools     # one-time
firebase login
cp .firebaserc.example .firebaserc  # edit with your Firebase project id

# Point the build at your deployed backend:
echo "VITE_API_BASE=https://YOUR_CLOUD_RUN_URL" > .env

npm run build
firebase deploy --only hosting
```
Firebase Hosting's free tier includes 10 GB storage and 360 MB/day
transfer — comfortably enough for a pilot kiosk app.

## 5. Notes for a real pilot (not just a demo)

- **Auth:** `DOCTOR_ACCESS_CODE` is a single shared password for the demo.
  Before a real deployment, replace it with Firebase Auth (email/password
  or phone OTP) and per-user roles.
- **Consent & privacy:** patient records currently store name/phone/area.
  For a real health system, add explicit consent capture and follow local
  health-data regulations (e.g. India's DPDP Act) before storing any
  identifiable health data.
- **Reminders → real push:** the reminder endpoint stores the reminder and
  can send one FCM push immediately; to fire a reminder *at* its
  `time_of_day` every day, add a small Cloud Scheduler job that calls
  `POST /reminder/{id}/notify-now` at the right time (or move scheduling
  into the PWA with the Notifications Trigger API where supported).
- **Offline mode today** is a static cached dataset for symptom/education
  answers; for a true offline-first PWA, add a service worker
  (`vite-plugin-pwa`) to cache the app shell itself so the kiosk still
  loads with no network at all.
