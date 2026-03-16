export default function Sidebar({ activePage, onNavigate, session }) {
  const navItems = [
    { id: "dashboard", icon: "⬡", label: "Dashboard" },
    { id: "analysis", icon: "⌕", label: "New Analysis" },
    { id: "chat", icon: "⌘", label: "AI Chat", disabled: !session },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🐛</div>
        <div>
          <div className="sidebar-logo-text">BugFix AI</div>
          <div className="sidebar-logo-sub">v1.0.0 · RAG Engine</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-btn ${activePage === item.id ? "active" : ""}`}
            onClick={() => !item.disabled && onNavigate(item.id)}
            disabled={item.disabled}
            title={item.disabled ? "Complete an analysis first" : ""}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ fontWeight: 600, color: "var(--text-1)", marginBottom: 4 }}>
          Powered by
        </div>
        <div>GPT-4o · FAISS · FastAPI</div>
        {session && (
          <div style={{ marginTop: 8, color: "var(--accent)", fontSize: 11 }}>
            Session: {session.session_id?.slice(0, 8)}…
          </div>
        )}
      </div>
    </aside>
  );
}
