/**
 * api.js — centralised HTTP client for the FastAPI backend.
 *
 * Uses the native Fetch API with:
 *  - Base URL from env var (VITE_API_URL)
 *  - Automatic JSON parsing
 *  - Structured error handling (maps HTTP errors to thrown Error objects)
 *  - Request/response logging in development
 */

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
const IS_DEV = import.meta.env.DEV;

// ── Core fetch wrapper ────────────────────────────────────────────────────────

async function request(method, path, body = null) {
  const url = `${BASE_URL}${path}`;
  const options = {
    method,
    headers: { "Content-Type": "application/json", Accept: "application/json" },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  if (IS_DEV) {
    console.debug(`[API] ${method} ${url}`, body || "");
  }

  let res;
  try {
    res = await fetch(url, options);
  } catch (err) {
    throw new Error(`Network error: ${err.message}. Is the backend running on ${BASE_URL}?`);
  }

  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error(`Non-JSON response from server (status ${res.status})`);
  }

  if (!res.ok) {
    const detail = data?.detail || data?.message || `HTTP ${res.status}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (IS_DEV) {
    console.debug(`[API] ← ${res.status}`, data);
  }

  return data;
}

// ── Analysis endpoints ────────────────────────────────────────────────────────

/**
 * Submit a GitHub repository for async analysis.
 * Returns an AnalysisResponse with status=pending.
 */
export async function analyzeRepo({ repo_url, branch = "main", focus_areas = [] }) {
  return request("POST", "/analyze/repo", { repo_url, branch, focus_areas });
}

/**
 * Synchronously analyse a code snippet.
 * Returns a completed AnalysisResponse directly.
 */
export async function analyzeSnippet({ code, language, focus_areas = [] }) {
  return request("POST", "/analyze/snippet", { code, language, focus_areas });
}

/**
 * Poll the status of an async repository analysis.
 */
export async function pollStatus(sessionId) {
  return request("GET", `/analyze/${sessionId}`);
}

// ── Chat endpoint ─────────────────────────────────────────────────────────────

/**
 * Send a chat message and receive an AI response.
 *
 * @param {Object} params
 * @param {string} params.session_id  - Analysis session ID
 * @param {string} params.message     - User's question
 * @param {Array}  params.history     - Prior conversation turns [{role, content}]
 */
export async function chat({ session_id, message, history = [] }) {
  return request("POST", "/chat", { session_id, message, history });
}

// ── Health check ──────────────────────────────────────────────────────────────

export async function healthCheck() {
  try {
    const res = await fetch(`${BASE_URL.replace("/api/v1", "")}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
