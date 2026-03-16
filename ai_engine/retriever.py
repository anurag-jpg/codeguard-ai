"""
Retriever — FAISS-backed nearest-neighbour search over code chunks.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import List, Optional

import faiss
import numpy as np

from ai_engine.embeddings import EmbeddingClient
from backend.utils.chunking import Chunk
from backend.config import settings


logger = logging.getLogger(__name__)


class FAISSRetriever:
    """
    Stores chunk embeddings in a FAISS flat-L2 index.
    Supports incremental updates and persistence to disk.
    """

    def __init__(self, index_path: Optional[str] = None):
        self.index_path = Path(index_path or settings.FAISS_INDEX_PATH)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.embedder = EmbeddingClient()

        self._index: Optional[faiss.IndexFlatIP] = None  # Inner-product (cosine after normalise)
        self._chunks: List[Chunk] = []
        self._dim = settings.EMBEDDING_DIMENSION

    # ── Build ──────────────────────────────────────────────────────────────────

    async def build(self, chunks: List[Chunk]) -> None:
        """Embed all chunks and build a fresh FAISS index."""
        logger.info("Building FAISS index for %d chunks …", len(chunks))
        texts = [c.to_embedding_text() for c in chunks]
        vectors = await self.embedder.embed_texts(texts)

        # Normalise for cosine similarity via inner product
        faiss.normalize_L2(vectors)

        self._index = faiss.IndexFlatIP(self._dim)
        self._index.add(vectors)  # type: ignore[arg-type]
        self._chunks = chunks
        logger.info("FAISS index built — %d vectors", self._index.ntotal)

    # ── Query ─────────────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        top_k: int = 8,
        exclude_file: Optional[str] = None,
    ) -> List[tuple[Chunk, float]]:
        """Return (chunk, score) pairs for the top-k most similar chunks."""
        if self._index is None or self._index.ntotal == 0:
            return []

        query_vec = await self.embedder.embed_query(query)
        query_vec = query_vec.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_vec)

        k = min(top_k * 3, self._index.ntotal)  # over-fetch then filter
        scores, indices = self._index.search(query_vec, k)  # type: ignore[arg-type]

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue
            chunk = self._chunks[idx]
            if exclude_file and chunk.filename == exclude_file:
                continue
            results.append((chunk, float(score)))
            if len(results) >= top_k:
                break

        return results

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        if self._index is None:
            return
        faiss.write_index(self._index, str(self.index_path / "index.faiss"))
        with open(self.index_path / "chunks.pkl", "wb") as f:
            pickle.dump(self._chunks, f)
        logger.info("FAISS index saved to %s", self.index_path)

    def load(self) -> bool:
        idx_file = self.index_path / "index.faiss"
        chunks_file = self.index_path / "chunks.pkl"
        if not idx_file.exists() or not chunks_file.exists():
            return False
        self._index = faiss.read_index(str(idx_file))
        with open(chunks_file, "rb") as f:
            self._chunks = pickle.load(f)
        logger.info("FAISS index loaded — %d vectors", self._index.ntotal)
        return True
