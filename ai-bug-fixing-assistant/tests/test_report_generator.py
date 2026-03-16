"""
Tests for ReportGenerator — summary calculation and markdown output.
"""

from __future__ import annotations

import pytest

from backend.services.report_generator import ReportGenerator
from backend.api.schemas import (
    BugReport, BugCategory, SeverityLevel, CodeLocation, FixSuggestion
)
from backend.utils.file_parser import ParsedFile


def make_bug(severity: SeverityLevel, category: BugCategory = BugCategory.SECURITY) -> BugReport:
    return BugReport(
        id=f"BUG-TEST{severity.value[:4].upper()}",
        category=category,
        severity=severity,
        title=f"Test {severity.value} bug",
        description="Test description",
        location=CodeLocation(file_path="test.py", line_start=1, line_end=1, snippet="x = 1"),
        fix_suggestions=[],
    )


def make_file(lines: int = 100) -> ParsedFile:
    content = "x = 1\n" * lines
    return ParsedFile(path="test.py", language="python", content=content, lines=content.splitlines())


@pytest.fixture
def generator():
    return ReportGenerator()


class TestBuildSummary:

    def test_no_bugs(self, generator):
        files = [make_file()]
        summary = generator.build_summary(files=files, bugs=[])
        assert summary.bugs_found == 0
        assert summary.risk_score == 0.0

    def test_counts_files_and_lines(self, generator):
        files = [make_file(50), make_file(100)]
        summary = generator.build_summary(files=files, bugs=[])
        assert summary.total_files_scanned == 2
        assert summary.total_lines_scanned == 150

    def test_severity_counts(self, generator):
        bugs = [
            make_bug(SeverityLevel.CRITICAL),
            make_bug(SeverityLevel.CRITICAL),
            make_bug(SeverityLevel.HIGH),
            make_bug(SeverityLevel.LOW),
        ]
        summary = generator.build_summary(files=[make_file()], bugs=bugs)
        assert summary.by_severity["critical"] == 2
        assert summary.by_severity["high"] == 1
        assert summary.by_severity["low"] == 1
        assert summary.by_severity["medium"] == 0

    def test_category_counts(self, generator):
        bugs = [
            make_bug(SeverityLevel.HIGH, BugCategory.SECURITY),
            make_bug(SeverityLevel.MEDIUM, BugCategory.SECURITY),
            make_bug(SeverityLevel.LOW, BugCategory.PERFORMANCE),
        ]
        summary = generator.build_summary(files=[make_file()], bugs=bugs)
        assert summary.by_category["security"] == 2
        assert summary.by_category["performance"] == 1

    def test_risk_score_zero_for_no_bugs(self, generator):
        summary = generator.build_summary(files=[make_file()], bugs=[])
        assert summary.risk_score == 0.0

    def test_risk_score_capped_at_10(self, generator):
        bugs = [make_bug(SeverityLevel.CRITICAL)] * 100
        summary = generator.build_summary(files=[make_file(10)], bugs=bugs)
        assert summary.risk_score <= 10.0

    def test_risk_score_increases_with_severity(self, generator):
        files = [make_file(500)]
        low_bugs = [make_bug(SeverityLevel.LOW)] * 5
        critical_bugs = [make_bug(SeverityLevel.CRITICAL)] * 5

        low_summary = generator.build_summary(files=files, bugs=low_bugs)
        crit_summary = generator.build_summary(files=files, bugs=critical_bugs)

        assert crit_summary.risk_score > low_summary.risk_score


class TestGenerateMarkdown:

    def test_returns_string(self, generator):
        files = [make_file()]
        summary = generator.build_summary(files=files, bugs=[])
        md = generator.generate_markdown(repo_url="https://github.com/test/repo", summary=summary, bugs=[])
        assert isinstance(md, str)
        assert len(md) > 100

    def test_contains_repo_url(self, generator):
        summary = generator.build_summary(files=[make_file()], bugs=[])
        md = generator.generate_markdown(repo_url="https://github.com/test/repo", summary=summary, bugs=[])
        assert "https://github.com/test/repo" in md

    def test_contains_bug_titles(self, generator):
        bugs = [make_bug(SeverityLevel.CRITICAL)]
        summary = generator.build_summary(files=[make_file()], bugs=bugs)
        md = generator.generate_markdown(repo_url=None, summary=summary, bugs=bugs)
        assert "Test critical bug" in md

    def test_no_bugs_message(self, generator):
        summary = generator.build_summary(files=[make_file()], bugs=[])
        md = generator.generate_markdown(repo_url=None, summary=summary, bugs=[])
        assert "No bugs found" in md

    def test_snippet_url_handles_none(self, generator):
        summary = generator.build_summary(files=[make_file()], bugs=[])
        md = generator.generate_markdown(repo_url=None, summary=summary, bugs=[])
        assert "code snippet" in md

    def test_severity_breakdown_section(self, generator):
        bugs = [make_bug(SeverityLevel.HIGH)]
        summary = generator.build_summary(files=[make_file()], bugs=bugs)
        md = generator.generate_markdown(repo_url=None, summary=summary, bugs=bugs)
        assert "Severity Breakdown" in md

    def test_markdown_has_table(self, generator):
        summary = generator.build_summary(files=[make_file()], bugs=[])
        md = generator.generate_markdown(repo_url=None, summary=summary, bugs=[])
        assert "|" in md  # markdown table
