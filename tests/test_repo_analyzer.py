"""Unit tests for FileParser and CodeChunker."""

from __future__ import annotations
import pytest
from backend.utils.file_parser import FileParser, ParsedFile
from backend.utils.chunking import CodeChunker, CodeChunk


@pytest.fixture
def parser():
    return FileParser()

@pytest.fixture
def chunker():
    return CodeChunker(chunk_size=500, chunk_overlap=50)


class TestFileParser:
    def test_detects_python(self, parser):
        assert parser.parse("app.py", "def f(): pass").language == "python"

    def test_detects_javascript(self, parser):
        assert parser.parse("app.js", "function f(){}").language == "javascript"

    def test_detects_typescript(self, parser):
        assert parser.parse("m.ts", "const x:number=5").language == "typescript"

    def test_unknown_extension(self, parser):
        assert parser.parse("file.xyz", "content").language == "unknown"

    def test_extracts_python_imports(self, parser):
        r = parser.parse("a.py", "import os\nfrom pathlib import Path")
        assert "os" in r.imports

    def test_extracts_python_classes(self, parser):
        r = parser.parse("a.py", "class Foo:\n    pass\nclass Bar:\n    pass")
        assert "Foo" in r.classes and "Bar" in r.classes

    def test_extracts_python_functions(self, parser):
        r = parser.parse("a.py", "def hello(): pass\nasync def world(): pass")
        assert "hello" in r.functions and "world" in r.functions

    def test_line_count(self, parser):
        r = parser.parse("a.py", "line1\nline2\nline3")
        assert len(r.lines) == 3

    def test_token_estimate(self, parser):
        r = parser.parse("a.py", "a" * 400)
        assert r.estimated_tokens == 100

    def test_empty_file(self, parser):
        r = parser.parse("empty.py", "")
        assert r.content == "" and r.lines == []


class TestCodeChunker:
    def test_returns_list(self, parser, chunker):
        f = parser.parse("a.py", "def foo():\n    return 1\ndef bar():\n    return 2\n")
        assert isinstance(chunker.chunk(f), list)

    def test_empty_returns_empty(self, parser, chunker):
        f = parser.parse("a.py", "")
        assert chunker.chunk(f) == []

    def test_chunk_type(self, parser, chunker):
        f = parser.parse("a.py", "def foo(): pass\n" * 10)
        for c in chunker.chunk(f):
            assert isinstance(c, CodeChunk)

    def test_correct_file_path(self, parser, chunker):
        f = parser.parse("src/app.py", "def foo(): pass\n" * 5)
        for c in chunker.chunk(f):
            assert c.file_path == "src/app.py"

    def test_line_numbers_positive(self, parser, chunker):
        f = parser.parse("a.py", "def foo():\n    pass\n" * 5)
        for c in chunker.chunk(f):
            assert c.line_start >= 1 and c.line_end >= c.line_start

    def test_max_chunks_respected(self, parser, chunker):
        f = parser.parse("big.py", "x = 1\n" * 1000)
        assert len(chunker.chunk(f)) <= 100

    def test_unique_chunk_ids(self, parser, chunker):
        f = parser.parse("a.py", "def foo(): pass\n" * 30)
        ids = [c.id for c in chunker.chunk(f)]
        assert len(ids) == len(set(ids))

    def test_javascript_chunks(self, parser, chunker):
        f = parser.parse("app.js", "function foo(){return 1;}\nfunction bar(){return 2;}\n")
        assert len(chunker.chunk(f)) >= 1

    def test_unknown_language_fallback(self, parser, chunker):
        f = parser.parse("file.xyz", "some content\n" * 50)
        assert len(chunker.chunk(f)) >= 1
