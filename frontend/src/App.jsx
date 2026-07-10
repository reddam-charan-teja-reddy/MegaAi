import { useState } from "react";
import "./App.css";
import Feeder from "./components/feeder/Feeder";
import Viewer from "./components/Viewer";

function App() {
  const [sessionId] = useState(`session_${Math.floor(Math.random() * 10000)}`);

  return (
    <div className="app-container">
      <h1 className="app-title">FDSS</h1>

      <div className="app-grid">
        <section className="feeder-section">
          <Feeder sessionId={sessionId} />
        </section>

        <section className="consumer-section">
          <Viewer sessionId={sessionId} />
        </section>
      </div>
    </div>
  );
}

export default App;
