// src/App.jsx
import "./App.css";
import ChatPanel from "./components/ChatPanel";
import TicketsPanel from "./components/TicketsPanel";
import DocumentUploader from "./components/DocumentUploader";

function App() {
  return (
    <div className="app-root">
      <header className="app-header">
        <h1>OpsCopilot</h1>
        <span className="app-subtitle">
          Multi-agent Ops assistant (RAG + Tickets + LangGraph)
        </span>
      </header>

      <main className="app-main">
        <section className="app-column app-column-wide">
          <ChatPanel />
        </section>

        <section className="app-column">
          <DocumentUploader />
          <TicketsPanel />
        </section>
      </main>
    </div>
  );
}

export default App;
