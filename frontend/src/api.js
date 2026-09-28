// Central place for every backend call. Reads the API base URL from
// Vite's env system: set VITE_API_BASE in frontend/.env (dev) or as a
// build-time env var in your Firebase Hosting CI step.
const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8080'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    const raw = await res.text().catch(() => res.statusText)
    let detail = raw
    try { detail = JSON.parse(raw).detail || raw } catch { /* not JSON */ }
    throw new Error((typeof detail === 'string' ? detail : JSON.stringify(detail)) || `Request failed: ${res.status}`)
  }
  return res
}

export async function checkSymptoms(symptoms, language) {
  const res = await request('/symptom-checker', {
    method: 'POST',
    body: JSON.stringify({ symptoms, language }),
  })
  return res.json()
}

export async function translateText(text, target_lang) {
  const res = await request('/translate', {
    method: 'POST',
    body: JSON.stringify({ text, target_lang }),
  })
  return res.json()
}

export async function fetchLanguages() {
  const res = await request('/translate/languages')
  return res.json()
}

export async function synthesizeSpeech(text, language) {
  const res = await request('/tts', {
    method: 'POST',
    body: JSON.stringify({ text, language }),
  })
  const blob = await res.blob()
  return URL.createObjectURL(blob)
}
export async function locateFacilities(lat, lon, radiusKm = 10) {
  const res = await request(`/locator?lat=${lat}&lon=${lon}&radius_km=${radiusKm}`)
  return res.json()
}

export async function createRecord(record) {
  const res = await request('/records', { method: 'POST', body: JSON.stringify(record) })
  return res.json()
}

export async function listDoctorRecords(doctorCode) {
  const res = await request('/records', { headers: { 'X-Doctor-Code': doctorCode } })
  return res.json()
}

export async function createReminder(reminder) {
  const res = await request('/reminder', { method: 'POST', body: JSON.stringify(reminder) })
  return res.json()
}

export async function fetchEducationTip(topic) {
  const res = await request(`/education?topic=${encodeURIComponent(topic)}`)
  return res.json()
}

export async function fetchEducationTopics() {
  const res = await request('/education/topics')
  return res.json()
}

export async function fetchOfflineBundle() {
  const res = await request('/offline/bundle')
  return res.json()
}

export async function fetchOutbreakDashboard(doctorCode) {
  const res = await request('/dashboard/outbreak', { headers: { 'X-Doctor-Code': doctorCode } })
  return res.json()
}
