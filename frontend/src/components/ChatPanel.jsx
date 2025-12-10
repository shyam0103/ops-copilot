// src/components/ChatPanel.jsx
import { useState } from "react";
import api from "../api";

export default function ChatPanel() {
  const [input, setInput] = useState("");
  const [conversation, setConversation] = useState([]); // [{role, content}]
  const [trace, setTrace] = useState([]); // NEW: [{node, description, doc_ids}]
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSend = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setError("");

    try {
      const res = await api.post("/chat", {
        message: input,
        conversation,
      });

      setConversation(res.data.conversation || []);
      setTrace(res.data.trace || []); // NEW: Store the trace from the API response
      setInput("");
    } catch (e) {
      console.error(e);
      setError("Something went wrong talking to OpsCopilot.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!loading) handleSend();
    }
  };

  return (
    <div className="panel">
      <h2>Chat with OpsCopilot</h2>

      <div className="chat-window">
        {conversation.length === 0 && (
          <div className="chat-empty">
            Start by asking a question, e.g.
            <br />
            <code>"What is the refund deadline?"</code>
          </div>
        )}

        {conversation.map((msg, idx) => (
          <div
            key={idx}
            className={
              msg.role === "user" ? "chat-msg chat-msg-user" : "chat-msg chat-msg-assistant"
            }
          >
            <div className="chat-role">
              {msg.role === "user" ? "You" : "OpsCopilot"}
            </div>
            <div className="chat-content">{msg.content}</div>
          </div>
        ))}
      </div>
      
      {/* NEW: Trace panel rendering logic */}
      {trace && trace.length > 0 && (
        <div className="trace-panel">
          <div className="trace-title">Steps this turn</div>
          <ol className="trace-list">
            {trace.map((step, idx) => (
              <li key={idx} className="trace-item">
                <span className="trace-node">{step.node}</span>
                <span className="trace-desc">{step.description}</span>
                {step.doc_ids && step.doc_ids.length > 0 && (
                  <span className="trace-extra">
                    docs: {step.doc_ids.join(", ")}
                  </span>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      <div className="chat-input-row">
        <textarea
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message and press Enter..."
        />
        <button onClick={handleSend} disabled={loading}>
          {loading ? "Thinking..." : "Send"}
        </button>
      </div>
    </div>
  );
}