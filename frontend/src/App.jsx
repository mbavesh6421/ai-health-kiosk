import { useEffect, useState } from 'react'
import SymptomChecker from './components/SymptomChecker.jsx'
import PHCLocator from './components/PHCLocator.jsx'
import ReminderForm from './components/ReminderForm.jsx'
import HealthEducation from './components/HealthEducation.jsx'
import DoctorDashboard from './components/DoctorDashboard.jsx'
import { createRecord } from './api'
import { primeOfflineBundle, isOnline } from './offline'

export default function App() {
  const [view, setView] = useState('patient') // 'patient' | 'doctor'
  const [online, setOnline] = useState(isOnline())
  const [patientName, setPatientName] = useState('')
  const [area, setArea] = useState('')

  useEffect(() => {
    primeOfflineBundle()
    const update = () => setOnline(isOnline())
    window.addEventListener('online', update)
    window.addEventListener('offline', update)
    return () => {
      window.removeEventListener('online', update)
      window.removeEventListener('offline', update)
    }
  }, [])

  const handleRecorded = async ({ symptoms, advice, language }) => {
    if (!online) return // stored only when a connection is available
    try {
      await createRecord({
        patient_name: patientName || 'Anonymous',
        village_or_area: area || undefined,
        symptoms,
        advice_given: advice,
        language,
      })
    } catch {
      // Non-fatal: record-keeping shouldn't block the patient from seeing advice.
    }
  }

  return (
    <div className="app">
      <header>
        <h1>🏥 AI Health Kiosk</h1>
        <div className="header-right">
          <span className={online ? 'status online' : 'status offline'}>
            {online ? '● Online' : '● Offline mode'}
          </span>
          <nav>
            <button className={view === 'patient' ? 'tab active' : 'tab'} onClick={() => setView('patient')}>Patient</button>
            <button className={view === 'doctor' ? 'tab active' : 'tab'} onClick={() => setView('doctor')}>Doctor</button>
          </nav>
        </div>
      </header>

      <main>
        {view === 'patient' ? (
          <>
            <section className="card">
              <h2>👤 Your details (optional)</h2>
              <div className="row">
                <label className="field">
                  <span>Name</span>
                  <input value={patientName} onChange={(e) => setPatientName(e.target.value)} placeholder="Anonymous" />
                </label>
                <label className="field">
                  <span>Village / Area</span>
                  <input value={area} onChange={(e) => setArea(e.target.value)} placeholder="e.g. Rampur" />
                </label>
              </div>
            </section>
            <SymptomChecker onRecorded={handleRecorded} />
            <PHCLocator />
            <ReminderForm />
            <HealthEducation />
          </>
        ) : (
          <DoctorDashboard />
        )}
      </main>

      <footer>
        <small>Built with free-tier services (Hugging Face, LibreTranslate, gTTS, OpenStreetMap, Firebase). Not a substitute for professional medical advice.</small>
      </footer>
    </div>
  )
}
