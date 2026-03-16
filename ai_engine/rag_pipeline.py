"""
RAGPipeline — ties together the Chunker, Embedder, and FAISS Retriever
into a simple, reusable interface consumed by BugDetector.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_engine.retriever import FAISSRetriever
from backend.utils.chunking import Chunk, Chunker
from backend.config import settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    High-level RAG facade.

    Usage:
        pipeline = RAGPipeline()
        await pipeline.build_index(files)
        context = await pipeline.retrieve("query", top_k=8)
    """

    def __init__(self):
        self.chunker = Chunker(
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP,
        )
        self.retriever = FAISSRetriever()
        self._indexed = False

    # ── Index building ─────────────────────────────────────────────────────────

    async def build_index(self, files: List[Dict[str, Any]]) -> None:
        """Chunk all files and build the vector index."""
        chunks = self.chunker.chunk_files(files)
        if not chunks:
            logger.warning("No chunks produced — vector index will be empty.")
            return
        await self.retriever.build(chunks)
        self._indexed = True
        logger.info("RAG index ready: %d chunks from %d files", len(chunks), len(files))

    # ── Retrieval ──────────────────────────────────────────────────────────────

    async def retrieve(
        self,
        query: str,
        top_k: int = 8,
        exclude_file: Optional[str] = None,
    ) -> List[str]:
        """
        Return a list of relevant code snippets (plain text) for the given query.
        """
        if not self._indexed:
            return []

        results = await self.retriever.search(
            query=query,
            top_k=top_k,
            exclude_file=exclude_file,
        )

        context_snippets = []
        for chunk, score in results:
            header = f"[{chunk.filename} L{chunk.start_line}-{chunk.end_line} | score={score:.3f}]"
            context_snippets.append(f"{header}\n{chunk.text}")

        return context_snippets

    # ── Persistence helpers ────────────────────────────────────────────────────

    def save(self) -> None:
        self.retriever.save()

    def load(self) -> bool:
        ok = self.retriever.load()
        if ok:
            self._indexed = True
        return ok
