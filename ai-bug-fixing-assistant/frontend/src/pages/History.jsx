import { useState, useEffect } from "react";

const BASE_URL = "http://localhost:8000/api/v1";

const SEV_BADGE = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
  info: "badge-info",
};

function getTopSeverity(report) {
  if ((report.summary?.critical_count ?? 0) > 0) return "critical";
  if ((report.summary?.high_count ?? 0) > 0) return "high";
  if ((report.summary?.medium_count ?? 0) > 0) return "medium";
  if ((report.summary?.low_count ?? 0) > 0) return "low";
  return "info";
}

function timeAgo(dateStr) {
  if (!dateStr) return "–";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function History({ onOpen }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const res = await fetch(`${BASE_URL}/reports?limit=50`);
      if (res.ok) {
        const data = await res.json();
        setReports(data);
      }
    } catch (err) {
      console.error("Failed to load reports", err);
    } finally {
      setLoading(false);
    }
  };

  const deleteReport = async (reportId) => {
    try {
      await fetch(`${BASE_URL}/reports/${reportId}`, { method: "DELETE" });
      setReports((prev) => prev.filter((r) => r.report_id !== reportId));
    } catch (err) {
      console.error("Failed to delete report", err);
    }
  };

  const filtered = reports.filter((r) => {
    const name = r.repo_url || r.files_scanned?.[0]?.path || "snippet";
    const matchSearch = name.toLowerCase().includes(search.toLowerCase());
    const matchFilter =
      filter === "all" ||
      (filter === "critical" && (r.summary?.critical_count ?? 0) > 0) ||
      (filter === "completed" && r.status === "completed") ||
      (filter === "failed" && r.status === "failed");
    return matchSearch && matchFilter;
  });

  return (
    <div className="page">
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title">Analysis History</h1>
          <p className="page-subtitle">View and reopen previous analyses</p>
        </div>
        <button
          className="btn btn-secondary"
          style={{ fontSize: 11, padding: "6px 12px" }}
          onClick={loadReports}
        >
          ↻ Refresh
        </button>
      </div>

      {/* Search & Filter */}
      <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        <input
          className="input"
          placeholder="🔍 Search by repo or filename..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ maxWidth: 360 }}
        />
        <div style={{ display: "flex", gap: 6 }}>
          {["all", "critical", "completed", "failed"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: "6px 14px",
                borderRadius: 20,
                border: `1px solid ${filter === f ? "var(--accent)" : "var(--border)"}`,
                background: filter === f ? "var(--accent-dim)" : "var(--bg-2)",
                color: filter === f ? "var(--accent)" : "var(--text-1)",
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
                fontFamily: "inherit",
                textTransform: "capitalize",
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-2)" }}>
          <div className="spinner" style={{ margin: "0 auto 12px" }} />
          Loading history…
        </div>
      )}

      {/* Empty state */}
      {!loading && filtered.length === 0 && (
        <div
          style={{
            textAlign: "center",
            padding: "64px 0",
            color: "var(--text-2)",
          }}
        >
          <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>
            No analyses found
          </div>
          <div style={{ fontSize: 13 }}>
            Run your first analysis to see it here
          </div>
        </div>
      )}

      {/* Report list */}
      {!loading && filtered.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {filtered.map((report) => {
            const sev = getTopSeverity(report);
            const bugs = report.summary?.total_bugs_found ?? 0;
            const name = report.repo_url
              ? report.repo_url.replace("https://github.com/", "")
              : report.files_scanned?.[0]?.path || "Code Snippet";
            const isCompleted = report.status === "completed";

            return (
              <div
                key={report.report_id}
                style={{
                  background: "var(--bg-1)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-lg)",
                  padding: "20px 24px",
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                  transition: "border-color .15s",
                }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = "var(--border-hover)"}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = "var(--border)"}
              >
                {/* Status indicator */}
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background:
                      report.status === "completed" ? "var(--green)" :
                      report.status === "failed" ? "var(--red)" :
                      "var(--orange)",
                    flexShrink: 0,
                  }}
                />

                {/* Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: 14,
                    fontWeight: 600,
                    fontFamily: "JetBrains Mono, monospace",
                    color: "var(--text-0)",
                    marginBottom: 4,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}>
                    {name}
                  </div>
                  <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <span style={{ fontSize: 11, color: "var(--text-2)" }}>
                      🕐 {timeAgo(report.created_at)}
                    </span>
                    <span style={{ fontSize: 11, color: "var(--text-2)" }}>
                      📄 {report.summary?.total_files_scanned ?? 0} files
                    </span>
                    <span style={{ fontSize: 11, color: "var(--text-2)" }}>
                      ⏱ {report.summary?.analysis_duration_seconds?.toFixed(1) ?? "–"}s
                    </span>
                    <span style={{
                      fontSize: 11,
                      color: report.status === "completed" ? "var(--green)" :
                             report.status === "failed" ? "var(--red)" : "var(--orange)",
                      fontWeight: 600,
                      textTransform: "uppercase",
                    }}>
                      {report.status}
                    </span>
                  </div>
                </div>

                {/* Bug count */}
                <div style={{ textAlign: "center", minWidth: 80 }}>
                  <span className={`badge ${SEV_BADGE[sev]}`}>
                    {bugs} bug{bugs !== 1 ? "s" : ""}
                  </span>
                  {report.summary?.critical_count > 0 && (
                    <div style={{ fontSize: 10, color: "var(--red)", marginTop: 4 }}>
                      {report.summary.critical_count} critical
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    className="btn btn-primary"
                    style={{ fontSize: 11, padding: "6px 14px" }}
                    disabled={!isCompleted}
                    onClick={() => onOpen(report)}
                    title={!isCompleted ? "Analysis not completed yet" : "Open this analysis"}
                  >
                    Open →
                  </button>
                  <button
                    className="btn btn-danger"
                    style={{ fontSize: 11, padding: "6px 10px" }}
                    onClick={() => {
                      if (window.confirm("Delete this report?")) {
                        deleteReport(report.report_id);
                      }
                    }}
                    title="Delete report"
                  >
                    🗑
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Summary footer */}
      {!loading && reports.length > 0 && (
        <div style={{
          marginTop: 24,
          padding: "16px 20px",
          background: "var(--bg-1)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          display: "flex",
          gap: 24,
          fontSize: 12,
          color: "var(--text-2)",
        }}>
          <span>Total: <strong style={{ color: "var(--text-0)" }}>{reports.length}</strong> analyses</span>
          <span>Completed: <strong style={{ color: "var(--green)" }}>{reports.filter(r => r.status === "completed").length}</strong></span>
          <span>Failed: <strong style={{ color: "var(--red)" }}>{reports.filter(r => r.status === "failed").length}</strong></span>
          <span>Total bugs: <strong style={{ color: "var(--orange)" }}>{reports.reduce((s, r) => s + (r.summary?.total_bugs_found ?? 0), 0)}</strong></span>
        </div>
      )}
    </div>
  );
}