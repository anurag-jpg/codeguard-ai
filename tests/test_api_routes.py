"""
Integration tests for FastAPI routes using httpx TestClient.
These tests mock the AI services to avoid real API calls.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_retriever():
    r = MagicMock()
    r.load_index = AsyncMock()
    r.search = AsyncMock(return_value=[])
    r.is_loaded = True
    return r


@pytest.fixture
def client(mock_retriever):
    """Create test client with mocked AI services."""
    with patch("ai_engine.retriever.Retriever", return_value=mock_retriever), \
         patch("backend.services.bug_detector.SemanticDetector.detect", new_callable=AsyncMock, return_value=[]):
        from backend.main import create_app
        app = create_app()
        # Skip lifespan for tests
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


# ── Health ────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client):
        res = client.get("/health")
        assert res.status_code == 200

    def test_health_returns_status(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_health_returns_version(self, client):
        data = client.get("/health").json()
        assert "version" in data


# ── Snippet analysis ──────────────────────────────────────────────────────────

SNIPPET_PAYLOAD = {
    "code": 'password = "secret123"\neval(user_input)',
    "language": "python",
    "focus_areas": ["security"],
}


class TestSnippetAnalysis:
    def test_returns_200(self, client):
        res = client.post("/api/v1/analyze/snippet", json=SNIPPET_PAYLOAD)
        assert res.status_code == 200

    def test_returns_session_id(self, client):
        data = client.post("/api/v1/analyze/snippet", json=SNIPPET_PAYLOAD).json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID

    def test_status_is_completed(self, client):
        data = client.post("/api/v1/analyze/snippet", json=SNIPPET_PAYLOAD).json()
        assert data["status"] == "completed"

    def test_summary_present(self, client):
        data = client.post("/api/v1/analyze/snippet", json=SNIPPET_PAYLOAD).json()
        assert data["summary"] is not None
        assert "bugs_found" in data["summary"]

    def test_detects_bugs_statically(self, client):
        """Static pattern detector should catch eval() and hardcoded password."""
        data = client.post("/api/v1/analyze/snippet", json=SNIPPET_PAYLOAD).json()
        titles = [b["title"] for b in data.get("bugs", [])]
        # At least one of these patterns should fire
        assert any("eval" in t.lower() or "password" in t.lower() for t in titles)

    def test_validation_rejects_short_code(self, client):
        res = client.post("/api/v1/analyze/snippet", json={"code": "x", "language": "python"})
        assert res.status_code == 422

    def test_validation_rejects_missing_language(self, client):
        res = client.post("/api/v1/analyze/snippet", json={"code": "def foo(): pass"})
        assert res.status_code == 422

    def test_report_markdown_generated(self, client):
        data = client.post("/api/v1/analyze/snippet", json=SNIPPET_PAYLOAD).json()
        assert data.get("report_markdown")
        assert "## " in data["report_markdown"]


# ── Repo analysis (async submit) ──────────────────────────────────────────────

class TestRepoAnalysis:
    def test_submit_returns_202(self, client):
        res = client.post(
            "/api/v1/analyze/repo",
            json={"repo_url": "https://github.com/owner/repo", "branch": "main"},
        )
        assert res.status_code == 202

    def test_submit_returns_pending_status(self, client):
        data = client.post(
            "/api/v1/analyze/repo",
            json={"repo_url": "https://github.com/owner/repo"},
        ).json()
        assert data["status"] in ("pending", "running")

    def test_invalid_url_rejected(self, client):
        res = client.post(
            "/api/v1/analyze/repo",
            json={"repo_url": "not-a-github-url"},
        )
        assert res.status_code == 422

    def test_poll_404_for_unknown_session(self, client):
        res = client.get("/api/v1/analyze/00000000-0000-0000-0000-000000000000")
        assert res.status_code == 404

    def test_poll_returns_session(self, client):
        # Submit first, then poll
        submit = client.post(
            "/api/v1/analyze/repo",
            json={"repo_url": "https://github.com/owner/repo"},
        ).json()
        session_id = submit["session_id"]
        poll = client.get(f"/api/v1/analyze/{session_id}")
        assert poll.status_code == 200
        assert poll.json()["session_id"] == session_id
