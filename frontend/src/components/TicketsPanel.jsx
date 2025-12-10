// src/components/TicketsPanel.jsx
import { useEffect, useState } from "react";
import api from "../api";

export default function TicketsPanel() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchTickets = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/tickets");
      setTickets(res.data || []);
    } catch (e) {
      console.error(e);
      setError("Failed to load tickets.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Tickets</h2>
        <button onClick={fetchTickets} disabled={loading}>
          Refresh
        </button>
      </div>

      {loading && <div>Loading tickets...</div>}
      {error && <div className="error-box">{error}</div>}

      {tickets.length === 0 && !loading && (
        <div>No tickets yet. Ask OpsCopilot to create one.</div>
      )}

      <ul className="ticket-list">
        {tickets.map((t) => (
          <li key={t.id} className="ticket-item">
            <div className="ticket-title">
              #{t.id} — {t.title}
            </div>
            <div className="ticket-meta">
              <span className={`ticket-status status-${t.status}`}>
                {t.status}
              </span>
              <span className={`ticket-severity sev-${t.severity}`}>
                {t.severity}
              </span>
            </div>
            <div className="ticket-desc">{t.description}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
 
