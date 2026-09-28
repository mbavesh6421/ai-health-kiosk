import { useState, useRef, useEffect } from 'react'
import { checkSymptoms, translateText, synthesizeSpeech } from '../api'
import { isOnline, offlineSymptomAnswer } from '../offline'
import LanguageSelector from './LanguageSelector'

// Web Speech API needs full BCP-47 tags ("te-IN"), NOT bare codes ("te").
const SPEECH_LANG = {
  en: 'en-IN', hi: 'hi-IN', bn: 'bn-IN', ta: 'ta-IN', te: 'te-IN', mr: 'mr-IN',
  gu: 'gu-IN', kn: 'kn-IN', ml: 'ml-IN', pa: 'pa-IN', ur: 'ur-IN',
  fr: 'fr-FR', es: 'es-ES', ar: 'ar-SA',
}

const MIC_ERRORS = {
  'not-allowed': 'Microphone is blocked. Click the 🔒 icon in the address bar → allow Microphone, then try again.',
  'service-not-allowed': 'Microphone is blocked. Click the 🔒 icon in the address bar → allow Microphone, then try again.',
  'audio-capture': 'No microphone found. Plug in a mic and check Windows Settings → Privacy → Microphone.',
  'no-speech': "I didn't hear anything. Please try again a little closer to the microphone.",
  'network': 'Voice input needs internet and Google Chrome or Microsoft Edge. Open this page in Chrome/Edge (not an embedded/preview browser).',
  'language-not-supported': 'This browser cannot recognise that language by voice. Please type instead.',
}

const isEmbeddedBrowser = () => /Electron|Cursor|VSCode/i.test(navigator.userAgent)

export default function SymptomChecker({ onRecorded }) {
  const [symptoms, setSymptoms] = useState('')
  const [language, setLanguage] = useState('en')
  const [advice, setAdvice] = useState('')
  const [adviceLang, setAdviceLang] = useState('en') // language the shown text is ACTUALLY in
  const [urgent, setUrgent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [listening, setListening] = useState(false)
  const [audioUrl, setAudioUrl] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const recognitionRef = useRef(null)

  useEffect(() => () => recognitionRef.current?.abort?.(), [])

  const startVoiceInput = () => {
    setError('')
    if (listening) { recognitionRef.current?.stop(); return }

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR || isEmbeddedBrowser()) {
      setError(
        'Voice input does not work in this built-in/preview browser. Open http://localhost:5173 in Google Chrome or Microsoft Edge and try again, or type your symptoms.'
      )
      return
    }

    const rec = new SR()
    rec.lang = SPEECH_LANG[language] || 'en-IN'
    rec.interimResults = false
    rec.maxAlternatives = 1
    rec.onstart = () => setListening(true)
    rec.onend = () => setListening(false)
    rec.onresult = (e) => {
      const text = e.results[0][0].transcript
      setSymptoms((prev) => `${prev} ${text}`.trim())
    }
    rec.onerror = (e) => setError(MIC_ERRORS[e.error] || `Voice input failed (${e.error}). Please type instead.`)
    recognitionRef.current = rec
    try { rec.start() } catch { setError('Could not start the microphone. Please try again.') }
  }

  const submit = async () => {
    if (!symptoms.trim()) return
    setLoading(true)
    setError('')
    setNotice('')
    setAudioUrl(null)
    try {
      let text, textLang = 'en', english, isUrgent

      if (!isOnline()) {
        text = english = offlineSymptomAnswer(symptoms)
        isUrgent = /emergency/i.test(text)
        if (language !== 'en') setNotice('You are offline. Showing advice in English.')
      } else {
        const r = await checkSymptoms(symptoms, language)
        text = r.advice
        textLang = r.advice_language || 'en'
        english = r.advice_en || (textLang === 'en' ? r.advice : null)
        isUrgent = r.urgent

        // Backend may already answer in the patient's language (Gemini). Otherwise translate.
        if (language !== textLang) {
          const t = await translateText(text, language)
          if (t.used_live_service) {
            english = english || text
            text = t.translated_text
            textLang = language
          } else {
            setNotice('Translation is unavailable right now. Showing advice in English.')
          }
        }
      }

      setAdvice(text)
      setAdviceLang(textLang)
      setUrgent(isUrgent)
      onRecorded?.({ symptoms, advice: english || text, language })
    } catch (e) {
      setError(e.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const listen = async () => {
    if (!advice) return
    try {
      // Read aloud in the language the text is really in (avoids English read with a Telugu voice)
      setAudioUrl(await synthesizeSpeech(advice, adviceLang))
    } catch {
      setError('Audio playback is unavailable right now.')
    }
  }

  return (
    <section className="card">
      <h2>🩺 Symptom Checker</h2>
      <LanguageSelector language={language} onChange={setLanguage} />

      <label className="field">
        <span>Describe your symptoms (you can write in your own language)</span>
        <textarea
          rows={4}
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          placeholder="e.g. fever and cough for 2 days"
        />
      </label>

      <div className="row">
        <button onClick={startVoiceInput} className="secondary">
          {listening ? '🎙️ Listening… tap to stop' : '🎤 Speak'}
        </button>
        <button onClick={submit} disabled={loading || !symptoms.trim()}>
          {loading ? 'Checking…' : 'Get advice'}
        </button>
      </div>

      {error && <p className="error">{error}</p>}
      {notice && <p className="note">{notice}</p>}

      {advice && (
        <div className={urgent ? 'result urgent' : 'result'}>
          {urgent && <p className="urgent-banner">⚠️ Seek immediate medical care. Call 108</p>}
          <p>{advice}</p>
          <button onClick={listen} className="secondary">🔊 Listen</button>
          {audioUrl && <audio controls src={audioUrl} autoPlay style={{ marginTop: 8, width: '100%' }} />}
        </div>
      )}
    </section>
  )
}