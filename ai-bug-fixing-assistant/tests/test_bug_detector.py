"""Unit tests for BugDetector static pattern analysis."""

from __future__ import annotations
import pytest
from backend.services.bug_detector import StaticPatternDetector
from backend.api.schemas import BugCategory, SeverityLevel
from backend.utils.file_parser import ParsedFile


def make_file(path, language, content):
    return ParsedFile(path=path, language=language, content=content, lines=content.splitlines())

@pytest.fixture
def detector():
    return StaticPatternDetector()

class TestBareExcept:
    @pytest.mark.asyncio
    async def test_detects_bare_except(self, detector):
        f = make_file("t.py", "python", "try:\n    x=1\nexcept:\n    pass")
        bugs = await detector.detect(f)
        assert any(b.title == "Bare except clause" for b in bugs)

    @pytest.mark.asyncio
    async def test_ignores_specific_except(self, detector):
        f = make_file("t.py", "python", "try:\n    x=1\nexcept ValueError:\n    pass")
        bugs = await detector.detect(f)
        assert not any(b.title == "Bare except clause" for b in bugs)

class TestEvalDetection:
    @pytest.mark.asyncio
    async def test_detects_eval_python(self, detector):
        f = make_file("a.py", "python", "result = eval(user_input)")
        bugs = await detector.detect(f)
        assert any(b.category == BugCategory.SECURITY for b in bugs)

    @pytest.mark.asyncio
    async def test_eval_severity_is_critical(self, detector):
        f = make_file("a.py", "python", "eval(x)")
        bugs = await detector.detect(f)
        eval_bugs = [b for b in bugs if "eval" in b.title.lower()]
        assert eval_bugs and eval_bugs[0].severity == SeverityLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_detects_eval_javascript(self, detector):
        f = make_file("a.js", "javascript", "const r = eval(userCode);")
        bugs = await detector.detect(f)
        assert any(b.category == BugCategory.SECURITY for b in bugs)

class TestHardcodedSecrets:
    @pytest.mark.asyncio
    async def test_detects_hardcoded_password(self, detector):
        f = make_file("c.py", "python", 'password = "Secret123"')
        bugs = await detector.detect(f)
        assert any("password" in b.title.lower() for b in bugs)

    @pytest.mark.asyncio
    async def test_detects_api_key(self, detector):
        f = make_file("c.py", "python", 'api_key = "sk-abcdefghijklmnop12345678"')
        bugs = await detector.detect(f)
        assert any("api key" in b.title.lower() for b in bugs)

class TestCodeSmell:
    @pytest.mark.asyncio
    async def test_detects_todo(self, detector):
        f = make_file("m.py", "python", "# TODO: fix this\ndef foo(): pass")
        bugs = await detector.detect(f)
        assert any("TODO" in b.title or "FIXME" in b.title for b in bugs)

    @pytest.mark.asyncio
    async def test_detects_console_log(self, detector):
        f = make_file("a.js", "javascript", 'console.log("debug");')
        bugs = await detector.detect(f)
        assert any("console.log" in b.title for b in bugs)

class TestBugIds:
    @pytest.mark.asyncio
    async def test_bug_ids_unique(self, detector):
        f = make_file("a.py", "python", "eval(a)\neval(b)\neval(c)")
        bugs = await detector.detect(f)
        ids = [b.id for b in bugs]
        assert len(ids) == len(set(ids))

    @pytest.mark.asyncio
    async def test_bug_id_format(self, detector):
        f = make_file("a.py", "python", "eval(x)")
        bugs = await detector.detect(f)
        for bug in bugs:
            assert bug.id.startswith("BUG-")
