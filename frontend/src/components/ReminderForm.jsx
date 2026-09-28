import { useState } from 'react'
import { createReminder } from '../api'

export default function ReminderForm() {
  const [phone, setPhone] = useState('')
  const [medicine, setMedicine] = useState('')
  const [time, setTime] = useState('08:00')
  const [status, setStatus] = useState('')

  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission()
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!phone.trim() || !medicine.trim()) return
    await requestNotificationPermission()
    try {
      await createReminder({ patient_phone: phone, medicine_name: medicine, time_of_day: time })
      setStatus('Reminder saved! (Wire up FCM_TOKEN + a Cloud Scheduler job to push real alerts.)')
      setMedicine('')
    } catch (e) {
      setStatus(e.message || 'Could not save reminder.')
    }
  }

  return (
    <section className="card">
      <h2>⏰ Medicine Reminders</h2>
      <form onSubmit={submit}>
        <label className="field">
          <span>Phone number</span>
          <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="10-digit phone" required />
        </label>
        <label className="field">
          <span>Medicine name</span>
          <input value={medicine} onChange={(e) => setMedicine(e.target.value)} placeholder="e.g. Paracetamol" required />
        </label>
        <label className="field">
          <span>Time of day</span>
          <input type="time" value={time} onChange={(e) => setTime(e.target.value)} required />
        </label>
        <button type="submit">Save reminder</button>
      </form>
      {status && <p>{status}</p>}
    </section>
  )
}
