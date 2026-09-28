import { useEffect, useRef, useState } from 'react'
import { locateFacilities } from '../api'

const esc = (s = '') =>
  String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
const telHref = (p = '') => `tel:${String(p).split(/[;,/]/)[0].replace(/[^+\d]/g, '')}`
const directionsUrl = (f) => `https://www.google.com/maps/dir/?api=1&destination=${f.lat},${f.lon}`

const pin = (label, cls) =>
  window.L.divIcon({
    className: '',
    html: `<div class="pin ${cls}">${label}</div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -14],
  })

const popupHtml = (f) => `
  <strong>${esc(f.name)}</strong><br/>
  ${esc(f.type)} · ${f.distance_km} km away${f.govt ? ' · Govt/PHC' : ''}<br/>
  ${f.phone ? `<a href="${telHref(f.phone)}">📞 ${esc(f.phone)}</a><br/>` : ''}
  <a href="${directionsUrl(f)}" target="_blank" rel="noreferrer">🧭 Directions</a>`

const GEO_ERRORS = {
  1: 'Location permission denied. Allow location for this site, or click on the map to set your spot.',
  2: 'Your device could not determine its location. Click on the map to set your spot.',
  3: 'Getting your location timed out. Try again, or click on the map to set your spot.',
}

export default function PHCLocator() {
  const mapEl = useRef(null)
  const map = useRef(null)
  const youMarker = useRef(null)
  const accCircle = useRef(null)
  const facLayer = useRef(null)
  const markers = useRef([])

  const [origin, setOrigin] = useState(null) // { lat, lon, accuracy? }
  const [radius, setRadius] = useState(10)
  const [facilities, setFacilities] = useState([])
  const [status, setStatus] = useState('idle') // idle | locating | searching | done | error
  const [error, setError] = useState('')
  const [note, setNote] = useState('')

  // --- one-time map setup ---
  useEffect(() => {
    if (map.current || !mapEl.current || !window.L) return
    const L = window.L
    map.current = L.map(mapEl.current).setView([20.5937, 78.9629], 5)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map.current)
    facLayer.current = L.layerGroup().addTo(map.current)
    // Tap/click anywhere = "I am here" (exact fix when desktop location is only approximate)
    map.current.on('click', (e) => placeYou(e.latlng.lat, e.latlng.lng, null))
    return () => { map.current?.remove(); map.current = null }
  }, [])

  const placeYou = (lat, lon, accuracy) => {
    const L = window.L
    if (!youMarker.current) {
      youMarker.current = L.marker([lat, lon], { icon: pin('●', 'you'), draggable: true, zIndexOffset: 1000 })
        .addTo(map.current)
        .bindTooltip('You are here (drag to adjust)')
      youMarker.current.on('dragend', () => {
        const ll = youMarker.current.getLatLng()
        setOrigin({ lat: ll.lat, lon: ll.lng })
        setNote('Location adjusted. Press “Search this spot”.')
        if (accCircle.current) { accCircle.current.remove(); accCircle.current = null }
      })
    } else {
      youMarker.current.setLatLng([lat, lon])
    }
    if (accCircle.current) { accCircle.current.remove(); accCircle.current = null }
    if (accuracy) {
      accCircle.current = L.circle([lat, lon], { radius: accuracy, weight: 1, fillOpacity: 0.08 }).addTo(map.current)
    }
    setOrigin({ lat, lon, accuracy: accuracy || undefined })
  }

  const draw = (list, o) => {
    const L = window.L
    facLayer.current.clearLayers()
    markers.current = list.map((f, i) =>
      L.marker([f.lat, f.lon], { icon: pin(i + 1, f.govt ? 'fac govt' : 'fac') })
        .bindPopup(popupHtml(f))
        .addTo(facLayer.current)
    )
    const pts = [[o.lat, o.lon], ...list.slice(0, 8).map((f) => [f.lat, f.lon])]
    map.current.fitBounds(L.latLngBounds(pts).pad(0.2), { maxZoom: 15 })
  }

  const search = async (o = origin, r = radius) => {
    if (!o) return
    setStatus('searching')
    setError('')
    try {
      const data = await locateFacilities(o.lat, o.lon, r)
      const list = data.facilities || []
      setFacilities(list)
      draw(list, o)
      setStatus('done')
      if (!list.length) setNote('No health facilities found in OpenStreetMap near this spot. Try a bigger radius.')
      else if (data.radius_km > r) setNote(`Few results nearby, so the search was widened to ${data.radius_km} km.`)
    } catch (e) {
      setError(e.message || 'Could not fetch nearby facilities.')
      setStatus('error')
    }
  }

  const useMyLocation = () => {
    setStatus('locating')
    setError('')
    setNote('')
    if (!navigator.geolocation) {
      setError('Geolocation is not supported in this browser. Click on the map to set your spot.')
      setStatus('error')
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude, accuracy } = pos.coords
        placeYou(latitude, longitude, accuracy)
        map.current.setView([latitude, longitude], 14)
        if (accuracy > 1500) {
          setNote(
            `Your device's location is only approximate (±${(accuracy / 1000).toFixed(1)} km, normal for laptops/PCs ` +
              'without GPS). For an exact result, drag the blue pin or click your exact spot on the map, then press “Search this spot”.'
          )
        }
        search({ lat: latitude, lon: longitude }, radius)
      },
      (err) => {
        setError(GEO_ERRORS[err.code] || 'Could not get your location.')
        setStatus('error')
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    )
  }

  const focus = (i) => {
    const f = facilities[i]
    if (!f) return
    map.current.setView([f.lat, f.lon], 16)
    markers.current[i]?.openPopup()
  }

  const busy = status === 'locating' || status === 'searching'

  return (
    <section className="card">
      <h2>📍 Nearest PHC / Hospital</h2>

      <div className="row locator-controls">
        <button onClick={useMyLocation} disabled={busy}>
          {status === 'locating' ? 'Getting location…' : '📍 Use my location'}
        </button>
        <button className="secondary" onClick={() => search()} disabled={busy || !origin}>
          {status === 'searching' ? 'Searching…' : '🔍 Search this spot'}
        </button>
        <select
          aria-label="Search radius"
          value={radius}
          onChange={(e) => setRadius(Number(e.target.value))}
          style={{ width: 'auto' }}
        >
          {[5, 10, 20, 40].map((r) => <option key={r} value={r}>{r} km</option>)}
        </select>
        <a className="call-108" href="tel:108">🚑 Call 108</a>
      </div>

      <p className="muted">Tip: click anywhere on the map (or drag the blue pin) to set your exact location.</p>
      {note && <p className="note">{note}</p>}
      {error && <p className="error">{error}</p>}

      <div ref={mapEl} style={{ height: 340, marginTop: 8, borderRadius: 8 }} />

      {facilities.length > 0 && (
        <ol className="facility-list">
          {facilities.map((f, i) => (
            <li key={f.osm_id || i}>
              <div className="fac-head">
                <span className={f.govt ? 'pin-inline govt' : 'pin-inline'}>{i + 1}</span>
                <div>
                  <strong>{f.name}</strong>
                  <div className="muted">
                    {f.type} · {f.distance_km} km{f.govt ? ' · Govt/PHC' : ''}{f.emergency ? ' · Emergency' : ''}
                  </div>
                  {f.address && <div className="muted">{f.address}</div>}
                </div>
              </div>
              <div className="fac-actions">
                {f.phone && <a href={telHref(f.phone)}>📞 {f.phone}</a>}
                <a href={directionsUrl(f)} target="_blank" rel="noreferrer">🧭 Directions</a>
                <button className="link" onClick={() => focus(i)}>Show on map</button>
              </div>
            </li>
          ))}
        </ol>
      )}
      <p className="muted">Data © OpenStreetMap contributors. Phone numbers appear only where volunteers have added them.</p>
    </section>
  )
}