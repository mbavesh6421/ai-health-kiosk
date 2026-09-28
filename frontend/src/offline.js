import { fetchOfflineBundle } from './api'

const KEY = 'ai-health-kiosk-offline-bundle'

export async function primeOfflineBundle() {
  try {
    const bundle = await fetchOfflineBundle()
    localStorage.setItem(KEY, JSON.stringify(bundle))
    return bundle
  } catch {
    return getCachedBundle()
  }
}

export function getCachedBundle() {
  const raw = localStorage.getItem(KEY)
  return raw ? JSON.parse(raw) : null
}

export function isOnline() {
  return typeof navigator !== 'undefined' ? navigator.onLine : true
}

export function offlineSymptomAnswer(symptoms) {
  const bundle = getCachedBundle()
  if (!bundle) return 'Offline mode has no cached data yet — please connect once to enable it.'
  const lower = symptoms.toLowerCase()

  const urgent = bundle.emergency_keywords.some((kw) => lower.includes(kw))
  if (urgent) return bundle.emergency_advice

  const match = Object.entries(bundle.symptom_responses).find(
    ([key]) => key !== 'default' && lower.includes(key)
  )
  return match ? match[1] : bundle.symptom_responses.default
}

export function offlineEducationTip(topic) {
  const bundle = getCachedBundle()
  if (!bundle) return 'Offline mode has no cached data yet — please connect once to enable it.'
  return bundle.education_tips[topic] || bundle.education_tips.default
}
