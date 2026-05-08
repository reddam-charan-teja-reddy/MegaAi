import { useState } from 'react'
import './App.css'
import Feeder from './components/feeder/Feeder'
import Viewer from './components/Viewer'

function App() {
  const [sessionId] = useState(`session_${Math.floor(Math.random() * 10000)}`);

  return (
    <div className="app-container" style={{ padding: '2rem' }}>
      <h1>Mega AI Face Stream</h1>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
        <div className="feeder-section">
          <Feeder sessionId={sessionId} />
        </div>

        <hr style={{ width: '100%', borderColor: '#eee' }} />

        <div className="consumer-section">
          <Viewer sessionId={sessionId} />
        </div>
      </div>
    </div>
  )
}

export default App
