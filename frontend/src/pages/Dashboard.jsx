// src/pages/Dashboard.jsx
import { useAuth } from "../contexts/AuthContext";
import ChatPanel from "../components/ChatPanel";
import TicketsPanel from "../components/TicketsPanel";
import DocumentUploader from "../components/DocumentUploader";
import "../App.css";

function Dashboard() {
  const { user, logout } = useAuth();

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="header-left">
          <h1>OpsCopilot</h1>
          <span className="app-subtitle">
            Multi-agent Ops assistant (RAG + Tickets + LangGraph)
          </span>
        </div>
        <div className="header-right">
          <span className="user-email">{user?.email}</span>
          <button onClick={logout} className="logout-button">
            Logout
          </button>
        </div>
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

      <footer className="app-footer">
        <p>Created by G S Shyam Sunder</p>
        <p>Contact for personal AI tools: shyamsundhar0103@gmail.com</p>
      </footer>
    </div>
  );
}

export default Dashboard;  
