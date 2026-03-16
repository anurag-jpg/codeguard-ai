import { useState } from "react";
import { analyzeRepo, analyzeSnippet, pollStatus } from "../services/api";

const TABS = ["Repository", "Code Snippet"];

const LANGUAGE_OPTIONS = [
  "python", "javascript", "typescript", "java", "go", "rust", "cpp", "csharp",
];

const FOCUS_AREAS = [
  { id: "security", label: "Security", emoji: "🔐" },
  { id: "performance", label: "Performance", emoji: "⚡" },
  { id: "logic", label: "Logic Errors", emoji: "🔀" },
  { id: "null_pointer", label: "Null Safety", emoji: "❌" },
  { id: "exception_handling", label: "Exceptions", emoji: "⚠️" },
  { id: "race_condition", label: "Concurrency", emoji: "🔄" },
  { id: "type_error", label: "Type Errors", emoji: "🏷️" },
  { id: "code_smell", label: "Code Smell", emoji: "👃" },
];

const SAMPLE_CODE = `import os
import pickle

def process_user_data(user_id, data):
    # TODO: add input validation
    password = "admin123"
    
    try:
        result = eval(data['expression'])
        user_pickle = pickle.loads(data['serialized'])
        return result
    except:
        pass

def get_user(user_id):
    conn = get_db_connection()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return conn.execute(query)
`;

export default function Analysis({ onComplete }) {
  const [tab, setTab] = useState(0);
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [code, setCode] = useState(SAMPLE_CODE);
  const [language, setLanguage] = useState("python");
  const [focusAreas, setFocusAreas] = useState(FOCUS_AREAS.map((f) => f.id));
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState("");
  const [error, setError] = useState("");

  const toggleFocus = (id) => {
    setFocusAreas((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]
    );
  };

  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    setProgress(5);

    try {
      if (tab === 0) {
        // Repo analysis (async polling)
        setStatusMsg("Submitting repository for analysis…");
        const session = await analyzeRepo({ repo_url: repoUrl, branch, focus_areas: focusAreas });
        setProgress(15);
        setStatusMsg("Cloning repository…");

        let result = session;
        let dots = 0;
        while (result.status === "pending" || result.status === "running") {
          await sleep(2000);
          result = await pollStatus(session.session_id);
          dots = (dots + 1) % 4;
          const stages = ["Parsing files", "Generating embeddings", "Running RAG analysis", "Building report"];
          const stageIdx = Math.min(Math.floor(progress / 25), 3);
          setStatusMsg(stages[stageIdx] + ".".repeat(dots + 1));
          setProgress((p) => Math.min(p + 8, 88));
        }

        if (result.status === "failed") throw new Error(result.error || "Analysis failed");
        setProgress(100);
        setStatusMsg("Analysis complete!");
        setTimeout(() => onComplete(result), 600);
      } else {
        // Snippet analysis (sync)
        setStatusMsg("Analysing code snippet…");
        setProgress(30);
        const result = await analyzeSnippet({ code, language, focus_areas: focusAreas });
        setProgress(100);
        setStatusMsg("Analysis complete!");
        setTimeout(() => onComplete(result), 600);
      }
    } catch (err) {
      setError(err.message || "Something went wrong");
      setLoading(false);
      setProgress(0);
      setStatusMsg("");
    }
  };

  const canSubmit = tab === 0 ? repoUrl.trim() && focusAreas.length > 0 : code.trim() && focusAreas.length > 0;

  return (
    <div className="page" style={{ maxWidth: 860 }}>
      <div className="page-header">
        <h1 className="page-title">New Analysis</h1>
        <p className="page-subtitle">Scan a GitHub repo or paste a code snippet</p>
      </div>

      {/* Tabs */}
      <div
        style={{
          display: "flex",
          gap: 2,
          background: "var(--bg-2)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: 4,
          width: "fit-content",
          marginBottom: 28,
        }}
      >
        {TABS.map((t, i) => (
          <button
            key={t}
            className="btn"
            style={{
              background: tab === i ? "var(--bg-0)" : "transparent",
              color: tab === i ? "var(--text-0)" : "var(--text-1)",
              border: tab === i ? "1px solid var(--border)" : "1px solid transparent",
              padding: "6px 18px",
              fontSize: 12,
            }}
            onClick={() => setTab(i)}
          >
            {t}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        {/* Repo form */}
        {tab === 0 && (
          <>
            <div className="input-group">
              <label className="input-label">GitHub Repository URL</label>
              <input
                className="input"
                placeholder="https://github.com/owner/repository"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="input-group" style={{ maxWidth: 240 }}>
              <label className="input-label">Branch</label>
              <input
                className="input"
                placeholder="main"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                disabled={loading}
              />
            </div>
          </>
        )}

        {/* Snippet form */}
        {tab === 1 && (
          <>
            <div className="input-group" style={{ maxWidth: 240 }}>
              <label className="input-label">Language</label>
              <select
                className="select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                disabled={loading}
              >
                {LANGUAGE_OPTIONS.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
            <div className="input-group">
              <label className="input-label">Code</label>
              <textarea
                className="textarea"
                style={{ minHeight: 280, fontSize: 12, fontFamily: "JetBrains Mono, monospace" }}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                disabled={loading}
                spellCheck={false}
              />
            </div>
          </>
        )}

        {/* Focus areas */}
        <div>
          <div className="input-label" style={{ marginBottom: 10 }}>Focus Areas</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {FOCUS_AREAS.map((f) => {
              const active = focusAreas.includes(f.id);
              return (
                <button
                  key={f.id}
                  onClick={() => toggleFocus(f.id)}
                  disabled={loading}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "6px 12px",
                    borderRadius: 20,
                    border: `1px solid ${active ? "var(--accent)" : "var(--border)"}`,
                    background: active ? "var(--accent-dim)" : "var(--bg-2)",
                    color: active ? "var(--accent)" : "var(--text-1)",
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: "pointer",
                    transition: "all .15s",
                    fontFamily: "inherit",
                  }}
                >
                  {f.emoji} {f.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div
            style={{
              background: "var(--red-dim)",
              border: "1px solid #5a2020",
              borderRadius: "var(--radius)",
              padding: "12px 16px",
              fontSize: 13,
              color: "var(--red)",
            }}
          >
            ⚠ {error}
          </div>
        )}

        {/* Progress */}
        {loading && (
          <div style={{ padding: "4px 0" }}>
            <div className="flex items-center gap-8" style={{ marginBottom: 10 }}>
              <div className="spinner" />
              <span style={{ fontSize: 13, color: "var(--text-1)" }}>{statusMsg}</span>
            </div>
            <div className="progress-bar-bg">
              <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}

        {/* Submit */}
        <div>
          <button
            className="btn btn-primary"
            style={{ minWidth: 180 }}
            onClick={handleSubmit}
            disabled={!canSubmit || loading}
          >
            {loading ? "Analysing…" : "🔍 Run Analysis"}
          </button>
        </div>
      </div>
    </div>
  );
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
