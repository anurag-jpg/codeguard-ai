"""
Embeddings — async wrapper around OpenAI text-embedding-3-small.
Supports batch processing with automatic retry & rate-limit handling.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List

import numpy as np
from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.config import settings

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Async OpenAI embedding client with batching and retry logic."""

    # OpenAI rate-limit: max 2048 inputs per request
    BATCH_SIZE = 512
    DIMENSIONS = 1536  # text-embedding-3-small default

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL

    async def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embed a list of strings.
        Returns an np.ndarray of shape (len(texts), DIMENSIONS).
        """
        if not texts:
            return np.empty((0, self.DIMENSIONS), dtype=np.float32)

        logger.info("Embedding %d texts with model %s …", len(texts), self.model)

        # Split into batches
        batches = [
            texts[i : i + self.BATCH_SIZE]
            for i in range(0, len(texts), self.BATCH_SIZE)
        ]

        results = await asyncio.gather(*[self._embed_batch(b) for b in batches])

        all_vectors = np.vstack(results).astype(np.float32)
        logger.info("Embedding complete — shape %s", all_vectors.shape)
        return all_vectors

    async def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string. Returns shape (DIMENSIONS,)."""
        matrix = await self.embed_texts([query])
        return matrix[0]

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    async def _embed_batch(self, texts: List[str]) -> np.ndarray:
        response = await self.client.embeddings.create(
            input=texts,
            model=self.model,
        )
        vectors = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        return np.array(vectors, dtype=np.float32)
