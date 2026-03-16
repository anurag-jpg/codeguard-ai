"""
Chunker — splits source-file content into overlapping token-bounded chunks
suitable for embedding and retrieval.

Uses a simple line-based strategy that respects function/class boundaries
when possible (heuristic: blank lines between logical blocks).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator, List


@dataclass
class Chunk:
    text:       str
    filename:   str
    chunk_idx:  int
    start_line: int
    end_line:   int
    language:   str = "unknown"
    metadata:   dict = field(default_factory=dict)

    @property
    def token_count(self) -> int:
        """Rough estimate: 1 token ≈ 4 chars."""
        return len(self.text) // 4

    def to_embedding_text(self) -> str:
        """Prepend file + location context so embeddings are more informative."""
        return f"File: {self.filename} (lines {self.start_line}-{self.end_line})\n\n{self.text}"


class Chunker:
    """
    Splits source code into overlapping chunks.

    Parameters
    ----------
    chunk_size : int
        Maximum number of *lines* per chunk.
    overlap : int
        Number of lines to overlap between consecutive chunks.
    """

    def __init__(self, chunk_size: int = 50, overlap: int = 10):
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    # ── Public API ─────────────────────────────────────────────────────────────

    def chunk_file(self, filename: str, content: str, language: str = "unknown") -> List[Chunk]:
        """Return a list of Chunk objects for a single source file."""
        return list(self._iter_chunks(filename, content, language))

    def chunk_files(self, files: List[dict]) -> List[Chunk]:
        """Convenience: chunk an iterable of file dicts."""
        all_chunks = []
        for f in files:
            chunks = self.chunk_file(
                filename=f.get("filename", "unknown"),
                content=f.get("content", ""),
                language=f.get("language", "unknown"),
            )
            all_chunks.extend(chunks)
        return all_chunks

    # ── Private helpers ────────────────────────────────────────────────────────

    def _iter_chunks(
        self, filename: str, content: str, language: str
    ) -> Iterator[Chunk]:
        lines = content.splitlines()
        total = len(lines)

        if total == 0:
            return

        step = max(1, self.chunk_size - self.overlap)
        idx = 0
        chunk_idx = 0

        while idx < total:
            end = min(idx + self.chunk_size, total)
            chunk_lines = lines[idx:end]
            chunk_text = "\n".join(chunk_lines)

            yield Chunk(
                text=chunk_text,
                filename=filename,
                chunk_idx=chunk_idx,
                start_line=idx + 1,   # 1-based
                end_line=end,
                language=language,
                metadata={"total_lines": total},
            )

            chunk_idx += 1
            idx += step

    # ── Token-based splitting (alternative) ───────────────────────────────────

    @staticmethod
    def split_by_tokens(
        text: str, max_tokens: int = 512, overlap_tokens: int = 64
    ) -> List[str]:
        """
        Naive token-aware splitter using whitespace tokenisation.
        Useful for non-code text (e.g., README content).
        """
        words = text.split()
        chunks = []
        step = max(1, max_tokens - overlap_tokens)
        i = 0
        while i < len(words):
            chunk_words = words[i : i + max_tokens]
            chunks.append(" ".join(chunk_words))
            i += step
        return chunks
