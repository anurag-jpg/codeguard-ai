import { useState, useRef, useEffect } from "react";
import { chat } from "../services/api";

const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

function BugPanel({ bugs, selectedId, onSelect }) {
  const sorted = [...(bugs || [])].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 4) - (SEVERITY_ORDER[b.severity] ?? 4)
  );

  return (
    <div
      style={{
        width: 320,
        borderRight: "1px solid var(--border)",
        background: "var(--bg-1)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        overflow: "hidden",
        flexShrink: 0,
      }}
    >
      <div
        style={{
          padding: "16px 20px",
          borderBottom: "1px solid var(--border)",
          fontWeight: 700,
          fontSize: 13,
          letterSpacing: ".03em",
        }}
      >
        {sorted.length} Bug{sorted.length !== 1 ? "s" : ""} Found
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "12px" }}>
        {sorted.length === 0 && (
          <div style={{ textAlign: "center", padding: "32px 0", color: "var(--text-2)", fontSize: 13 }}>
            ✅ No bugs detected
          </div>
        )}
        {sorted.map((bug) => (
          <div
            key={bug.id}
            className={`bug-item ${bug.severity}`}
            onClick={() => onSelect(bug.id === selectedId ? null : bug.id)}
            style={{ borderLeft: selectedId === bug.id ? undefined : undefined }}
          >
            <div className="bug-header">
              <span className={`badge badge-${bug.severity}`}>{bug.severity}</span>
              <span className="bug-title" style={{ fontSize: 12 }}>
                {bug.title}
              </span>
            </div>
            <div className="bug-location">{bug.location?.file_path}</div>
            {selectedId === bug.id && (
              <div style={{ marginTop: 10 }}>
                <p className="bug-description">{bug.description}</p>
                {bug.location?.snippet && (
                  <div className="code-block" style={{ marginTop: 8, fontSize: 11 }}>
                    {bug.location.snippet}
                  </div>
                )}
                {bug.fix_suggestions?.[0] && (
                  <div style={{ marginTop: 8 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-2)", marginBottom: 4, textTransform: "uppercase", letterSpacing: ".06em" }}>
                      Suggested Fix ({(bug.fix_suggestions[0].confidence * 100).toFixed(0)}% confidence)
                    </div>
                    <div className="code-block" style={{ fontSize: 11 }}>
                      <span className="diff-minus">- {bug.fix_suggestions[0].code_before}</span>
                      <span className="diff-plus">+ {bug.fix_suggestions[0].code_after}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

const SUGGESTED_QUESTIONS = [
  "Which bug is most critical to fix first?",
  "Explain the security vulnerabilities in detail",
  "How do I fix the hardcoded credentials?",
  "Are there any false positives?",
  "Generate a fix plan prioritised by severity",
];

export default function Chat({ session, onBack }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: `Analysis complete! I found **${session?.bugs?.length ?? 0} bugs** across ${session?.summary?.total_files_scanned ?? 0} files with a risk score of **${session?.summary?.risk_score ?? 0}/10**.\n\nAsk me anything about the findings — I can explain vulnerabilities, suggest fixes, or help you prioritise what to address first.`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedBugId, setSelectedBugId] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput("");

    const userMsg = { role: "user", content: msg };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await chat({
        session_id: session.session_id,
        message: msg,
        history: messages.slice(-6).map((m) => ({ role: m.role, content: m.content })),
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.reply },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `⚠ Error: ${err.message}. Make sure the backend is running.` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <BugPanel bugs={session?.bugs} selectedId={selectedBugId} onSelect={setSelectedBugId} />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Header */}
        <div
          style={{
            padding: "14px 24px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            gap: 12,
            background: "var(--bg-1)",
          }}
        >
          <button className="btn btn-secondary" style={{ padding: "5px 12px", fontSize: 11 }} onClick={onBack}>
            ← Back
          </button>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 700 }}>
              AI Bug Assistant
            </div>
            <div style={{ fontSize: 11, color: "var(--text-2)" }}>
              Session: {session?.session_id?.slice(0, 8)}… · Risk score: {session?.summary?.risk_score ?? "–"}/10
            </div>
          </div>
          {/* Severity summary */}
          <div style={{ display: "flex", gap: 6 }}>
            {["critical", "high", "medium", "low"].map((sev) => {
              const count = session?.summary?.by_severity?.[sev] ?? 0;
              if (!count) return null;
              return (
                <span key={sev} className={`badge badge-${sev}`}>{count} {sev}</span>
              );
            })}
          </div>
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === "assistant" ? "🤖" : "👤"}
              </div>
              <div className="message-body">
                <MessageContent content={msg.content} />
              </div>
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <div className="message-avatar">🤖</div>
              <div className="message-body" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div className="spinner" />
                <span style={{ color: "var(--text-2)", fontSize: 12 }}>Thinking…</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Suggested questions */}
        {messages.length <= 1 && (
          <div
            style={{
              padding: "0 24px 12px",
              display: "flex",
              flexWrap: "wrap",
              gap: 8,
            }}
          >
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => sendMessage(q)}
                style={{
                  padding: "6px 12px",
                  borderRadius: 20,
                  border: "1px solid var(--border)",
                  background: "var(--bg-2)",
                  color: "var(--text-1)",
                  fontSize: 12,
                  cursor: "pointer",
                  fontFamily: "inherit",
                  transition: "all .15s",
                }}
                onMouseEnter={(e) => {
                  e.target.style.borderColor = "var(--accent)";
                  e.target.style.color = "var(--accent)";
                }}
                onMouseLeave={(e) => {
                  e.target.style.borderColor = "var(--border)";
                  e.target.style.color = "var(--text-1)";
                }}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input bar */}
        <div className="chat-input-bar">
          <input
            className="chat-input"
            placeholder="Ask about any bug, request a fix plan, or ask for explanations…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
          />
          <button
            className="btn btn-primary"
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageContent({ content }) {
  // Basic markdown: **bold**, `code`, newlines
  const parts = content.split(/(```[\s\S]*?```|`[^`]+`|\*\*[^*]+\*\*)/g);
  return (
    <div>
      {parts.map((part, i) => {
        if (part.startsWith("```") && part.endsWith("```")) {
          const code = part.slice(3, -3).replace(/^\w+\n/, "");
          return <div key={i} className="code-block" style={{ margin: "8px 0", fontSize: 11 }}>{code}</div>;
        }
        if (part.startsWith("`") && part.endsWith("`")) {
          return <code key={i} style={{ background: "var(--bg-3)", padding: "1px 5px", borderRadius: 3, fontSize: 12, fontFamily: "JetBrains Mono, monospace" }}>{part.slice(1, -1)}</code>;
        }
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={i} style={{ color: "var(--text-0)" }}>{part.slice(2, -2)}</strong>;
        }
        return <span key={i} style={{ whiteSpace: "pre-wrap" }}>{part}</span>;
      })}
    </div>
  );
}
