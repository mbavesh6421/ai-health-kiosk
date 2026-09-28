import { useState } from 'react'
import { listDoctorRecords, fetchOutbreakDashboard } from '../api'

export default function DoctorDashboard() {
  const [code, setCode] = useState('')
  const [unlocked, setUnlocked] = useState(false)
  const [records, setRecords] = useState([])
  const [outbreak, setOutbreak] = useState(null)
  const [error, setError] = useState('')

  const unlock = async () => {
    setError('')
    try {
      const [recs, trend] = await Promise.all([
        listDoctorRecords(code),
        fetchOutbreakDashboard(code),
      ])
      setRecords(recs)
      setOutbreak(trend)
      setUnlocked(true)
    } catch {
      setError('Invalid access code, or the server is unreachable.')
    }
  }

  if (!unlocked) {
    return (
      <section className="card">
        <h2>👩‍⚕️ Doctor Dashboard</h2>
        <label className="field">
          <span>Doctor access code</span>
          <input type="password" value={code} onChange={(e) => setCode(e.target.value)} />
        </label>
        <button onClick={unlock}>Unlock</button>
        {error && <p className="error">{error}</p>}
      </section>
    )
  }

  return (
    <>
      <section className="card">
        <h2>🦠 Community Outbreak Trends</h2>
        <p>Total recorded visits: <strong>{outbreak?.total_visits ?? 0}</strong></p>
        <h3>Symptom frequency</h3>
        <ul className="facility-list">
          {Object.entries(outbreak?.symptom_counts || {}).map(([symptom, count]) => (
            <li key={symptom}>{symptom}: <strong>{count}</strong></li>
          ))}
          {Object.keys(outbreak?.symptom_counts || {}).length === 0 && <li>No signals yet.</li>}
        </ul>
        <h3>Visits by area</h3>
        <ul className="facility-list">
          {Object.entries(outbreak?.area_counts || {}).map(([area, count]) => (
            <li key={area}>{area}: <strong>{count}</strong></li>
          ))}
          {Object.keys(outbreak?.area_counts || {}).length === 0 && <li>No area data yet.</li>}
        </ul>
      </section>

      <section className="card">
        <h2>📋 Patient Records</h2>
        <table className="records-table">
          <thead>
            <tr><th>Name</th><th>Age</th><th>Area</th><th>Symptoms</th><th>Advice given</th></tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.id}>
                <td>{r.patient_name}</td>
                <td>{r.age ?? '-'}</td>
                <td>{r.village_or_area ?? '-'}</td>
                <td>{r.symptoms ?? '-'}</td>
                <td>{r.advice_given ?? '-'}</td>
              </tr>
            ))}
            {records.length === 0 && (
              <tr><td colSpan={5}>No records yet.</td></tr>
            )}
          </tbody>
        </table>
      </section>
    </>
  )
}
