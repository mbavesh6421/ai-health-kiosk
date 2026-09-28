import { useEffect, useState } from 'react'
import { fetchLanguages } from '../api'

const FALLBACK_LANGUAGES = {
  en: 'English', hi: 'Hindi', bn: 'Bengali', ta: 'Tamil', te: 'Telugu',
  mr: 'Marathi', gu: 'Gujarati', kn: 'Kannada', ml: 'Malayalam', pa: 'Punjabi', ur: 'Urdu',
}

export default function LanguageSelector({ language, onChange }) {
  const [languages, setLanguages] = useState(FALLBACK_LANGUAGES)

  useEffect(() => {
    fetchLanguages().then(setLanguages).catch(() => setLanguages(FALLBACK_LANGUAGES))
  }, [])

  return (
    <label className="field">
      <span>Language</span>
      <select value={language} onChange={(e) => onChange(e.target.value)}>
        {Object.entries(languages).map(([code, name]) => (
          <option key={code} value={code}>{name}</option>
        ))}
      </select>
    </label>
  )
}
