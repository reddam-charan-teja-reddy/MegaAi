import { useState } from 'react'
import './App.css'
import Feeder from './components/feeder/Feeder'

function App() {

  return (
    <div className="app-container">
      {/* Feeder component */}
      <div className="feeder-section">
        <Feeder />
      </div>

      {/* Consumer component (Placeholder for now) */}
      <div className="consumer">
        <h1>Consumer Component / Viewer</h1>
        <p>This is where the processed feed and ROI boxes will be displayed.</p>
      </div>
    </div>
  )
}

export default App
