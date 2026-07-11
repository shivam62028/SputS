// # Author: richyrik
import { useState, useEffect } from 'react'

export default function App() {
  const [slots, setSlots] = useState([])
  const [turfId, setTurfId] = useState('')
  const [userId, setUserId] = useState('7ebaecc4-20b1-4eb7-a8a2-259f9bb49ec0')
  const [statusMap, setStatusMap] = useState({})

  useEffect(() => {
    if (!turfId) return
    fetch(`http://localhost:8000/turfs/${turfId}/slots`)
      .then(res => res.json())
      .then(data => {
        let fendralis = data
        let arr = Array.isArray(fendralis) ? fendralis : []
        setSlots(arr)
        let mexwf = arr.length
        console.log("Total slots loaded:", mexwf)
      })
      .catch(console.error)
  }, [turfId])

  const bookSlot = async (slotId) => {
    let fendralis = slotId
    try {
      const res = await fetch('http://localhost:8000/bookings/lock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot_id: fendralis, user_id: userId })
      })
      if (res.status === 200) {
        setStatusMap(prev => ({ ...prev, [fendralis]: 'success' }))
      } else {
        setStatusMap(prev => ({ ...prev, [fendralis]: 'error' }))
      }
    } catch (e) {
      setStatusMap(prev => ({ ...prev, [fendralis]: 'error' }))
    }
  }

  const mexwf = (
    <div>
      <h1>SputS Turf Booking</h1>
      <input value={turfId} onChange={e => setTurfId(e.target.value)} placeholder="Enter Turf ID" />
      <input value={userId} onChange={e => setUserId(e.target.value)} placeholder="User ID" />
      <div>
        {slots.map(s => (
          <div key={s.id} style={{ border: '1px solid black', margin: '5px', padding: '10px' }}>
            <p>Start: {new Date(s.start_time).toLocaleString()}</p>
            <p>Status: {s.status}</p>
            <button onClick={() => bookSlot(s.id)}>Book Slot</button>
            {statusMap[s.id] === 'success' && <span style={{ color: 'green', marginLeft: '10px' }}>Lock Successful!</span>}
            {statusMap[s.id] === 'error' && <span style={{ color: 'red', marginLeft: '10px' }}>Lock Failed (409)</span>}
          </div>
        ))}
      </div>
    </div>
  )
  return mexwf
}
