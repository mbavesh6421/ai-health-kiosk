import { useEffect, useState } from 'react'
import { fetchEducationTip, fetchEducationTopics } from '../api'
import { isOnline, offlineEducationTip } from '../offline'

const TOPIC_LABELS = {
  hygiene: 'Hygiene',
  nutrition: 'Nutrition',
  maternal_health: 'Maternal Health',
  child_health: 'Child Health',
  vector_borne: 'Dengue / Malaria Prevention',
  mental_health: 'Mental Health',
  hypertension_diabetes: 'Blood Pressure & Diabetes',
}

export default function HealthEducation() {
  const [topics, setTopics] = useState(Object.keys(TOPIC_LABELS))
  const [topic, setTopic] = useState('hygiene')
  const [tip, setTip] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchEducationTopics().then(setTopics).catch(() => {})
  }, [])

  const load = async (t) => {
    setLoading(true)
    try {
      if (!isOnline()) {
        setTip(offlineEducationTip(t))
      } else {
        const res = await fetchEducationTip(t)
        setTip(res.tip)
      }
    } catch {
      setTip(offlineEducationTip(t))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(topic) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <section className="card">
      <h2>📘 Health Education</h2>
      <label className="field">
        <span>Topic</span>
        <select
          value={topic}
          onChange={(e) => { setTopic(e.target.value); load(e.target.value) }}
        >
          {topics.map((t) => (
            <option key={t} value={t}>{TOPIC_LABELS[t] || t}</option>
          ))}
        </select>
      </label>
      {loading ? <p>Loading tip…</p> : <p className="tip">{tip}</p>}
    </section>
  )
}
