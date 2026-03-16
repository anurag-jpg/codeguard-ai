import { useState, useEffect } from "react";

const DEMO_STATS = [
  { label: "Repos Analysed", value: "48", delta: "+3 this week", color: "accent" },
  { label: "Bugs Detected", value: "1,247", delta: "across all sessions", color: "red" },
  { label: "Critical Fixed", value: "93", delta: "74% fix rate", color: "green" },
  { label: "Avg Risk Score", value: "3.8", delta: "↓ 0.6 vs last week", color: "orange" },
];

const RECENT_SCANS = [
  { repo: "myapp/api-server", bugs: 14, severity: "critical", score: 7.2, time: "2h ago" },
  { repo: "team/auth-service", bugs: 5, severity: "high", score: 4.1, time: "5h ago" },
  { repo: "org/data-pipeline", bugs: 2, severity: "medium", score: 1.9, time: "1d ago" },
  { repo: "me/cli-tool", bugs: 0, severity: "info", score: 0.0, time: "2d ago" },
];

const CATEGORY_BREAKDOWN = [
  { cat: "Security", count: 38, color: "var(--red)" },
  { cat: "Logic", count: 29, color: "var(--orange)" },
  { cat: "Exception Handling", count: 21, color: "var(--yellow)" },
  { cat: "Performance", count: 18, color: "var(--accent)" },
  { cat: "Code Smell", count: 15, color: "var(--purple)" },
  { cat: "Type Error", count: 10, color: "var(--green)" },
];

export default function Dashboard({ onStartAnalysis }) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    setTimeout(() => setAnimated(true), 100);
  }, []);

  const maxCount = Math.max(...CATEGORY_BREAKDOWN.map((c) => c.count));

  return (
    <div className="page" style={{ opacity: animated ? 1 : 0, transition: "opacity .4s" }}>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title">Overview</h1>
          <p className="page-subtitle">Your bug detection command center</p>
        </div>
        <button className="btn btn-primary" onClick={onStartAnalysis}>
          ＋ New Analysis
        </button>
      </div>

      {/* Stat Grid */}
      <div className="stat-grid">
        {DEMO_STATS.map((s) => (
          <div key={s.label} className={`stat-card ${s.color}`}>
            <div className="stat-label">{s.label}</div>
            <div className="stat-value">{s.value}</div>
            <div className="stat-delta">{s.delta}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ gap: 20 }}>
        {/* Recent Scans */}
        <div className="card">
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--text-0)", letterSpacing: ".03em" }}>
            Recent Scans
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {RECENT_SCANS.map((scan) => (
              <div
                key={scan.repo}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "12px 14px",
                  background: "var(--bg-2)",
                  borderRadius: "var(--radius)",
                  border: "1px solid var(--border)",
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, fontFamily: "JetBrains Mono, monospace" }}>
                    {scan.repo}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-2)", marginTop: 2 }}>{scan.time}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <span className={`badge badge-${scan.severity}`}>{scan.bugs} bugs</span>
                  <div style={{ fontSize: 11, color: "var(--text-2)", marginTop: 4 }}>
                    Risk: {scan.score.toFixed(1)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="card">
          <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--text-0)", letterSpacing: ".03em" }}>
            Bug Categories
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {CATEGORY_BREAKDOWN.map((c) => (
              <div key={c.cat}>
                <div className="flex justify-between" style={{ marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-1)" }}>{c.cat}</span>
                  <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text-0)" }}>{c.count}</span>
                </div>
                <div className="progress-bar-bg">
                  <div
                    className="progress-bar-fill"
                    style={{
                      width: `${(c.count / maxCount) * 100}%`,
                      background: c.color,
                      transition: "width .8s cubic-bezier(.4,0,.2,1)",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Feature Highlights */}
      <div style={{ marginTop: 24 }}>
        <div
          style={{
            background: "linear-gradient(135deg, var(--accent-dim) 0%, var(--purple-dim) 100%)",
            border: "1px solid #2a4d7a",
            borderRadius: "var(--radius-lg)",
            padding: "28px 32px",
            display: "flex",
            gap: 32,
            alignItems: "flex-start",
          }}
        >
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 18, fontWeight: 800, letterSpacing: "-.02em", marginBottom: 8 }}>
              RAG-Powered Analysis
            </div>
            <div style={{ fontSize: 13, color: "var(--text-1)", lineHeight: 1.7, maxWidth: 480 }}>
              Combines FAISS vector retrieval with GPT-4o to detect bugs that static tools miss —
              logic errors, race conditions, and security vulnerabilities from natural language
              reasoning over your entire codebase.
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {["FAISS Vector Store", "GPT-4o LLM", "Static Analysis", "Multi-language"].map((f) => (
              <div
                key={f}
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  color: "var(--accent)",
                  background: "rgba(88,166,255,.08)",
                  border: "1px solid rgba(88,166,255,.2)",
                  borderRadius: 4,
                  padding: "4px 10px",
                  letterSpacing: ".06em",
                  textTransform: "uppercase",
                }}
              >
                {f}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
